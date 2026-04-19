from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length

from ...extensions import db
from ...models import (
    Assignment,
    Attendance,
    ClassRoom,
    Mark,
    Notification,
    Student,
    Subject,
    Teacher,
    TeacherSubjectAssignment,
    User,
)
from ...utils import role_required

admin_bp = Blueprint("admin", __name__)


class UserForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    role = SelectField("Role", choices=[("teacher", "Teacher"), ("student", "Student")])
    code = StringField("Admission / Employee Code", validators=[DataRequired()])
    class_id = SelectField("Class", coerce=int, validate_choice=False)
    submit = SubmitField("Save")


class StudentForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    admission_no = StringField("Admission Number", validators=[DataRequired(), Length(max=30)])
    roll_no = StringField("Roll Number", validators=[DataRequired(), Length(max=20)])
    class_id = SelectField("Class", coerce=int, validate_choice=False)
    guardian_name = StringField("Guardian Name")
    submit = SubmitField("Add Student")


class TeacherForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    employee_code = StringField("Employee Code", validators=[DataRequired(), Length(max=30)])
    qualification = StringField("Qualification")
    submit = SubmitField("Add Teacher")


class ClassForm(FlaskForm):
    name = StringField("Class Name", validators=[DataRequired()])
    section = StringField("Section", validators=[DataRequired()])
    submit = SubmitField("Save")


class SubjectForm(FlaskForm):
    name = StringField("Subject Name", validators=[DataRequired()])
    code = StringField("Subject Code", validators=[DataRequired()])
    submit = SubmitField("Save")


class AssignmentForm(FlaskForm):
    teacher_id = SelectField("Teacher", coerce=int)
    class_id = SelectField("Class", coerce=int)
    subject_id = SelectField("Subject", coerce=int)
    submit = SubmitField("Assign")


class BroadcastForm(FlaskForm):
    role = SelectField(
        "Target Role",
        choices=[("all", "All Users"), ("student", "Students"), ("teacher", "Teachers"), ("admin", "Admins")],
    )
    title = StringField("Title", validators=[DataRequired(), Length(max=150)])
    message = StringField("Message", validators=[DataRequired(), Length(max=255)])
    submit = SubmitField("Send Notification")


def _email_exists(email):
    return User.query.filter_by(email=email.lower().strip()).first() is not None


def _create_user(full_name, email, password, role):
    user = User(full_name=full_name.strip(), email=email.lower().strip(), role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user


@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    marks = Mark.query.all()
    attendance = Attendance.query.all()
    students = Student.query.count()
    teachers = Teacher.query.count()
    pass_count = len([m for m in marks if m.grade != "F"])
    fail_count = len(marks) - pass_count
    top_students = (
        db.session.query(Student, db.func.avg(Mark.percentage).label("avg_per"))
        .join(Mark, Student.id == Mark.student_id)
        .group_by(Student.id)
        .order_by(db.desc("avg_per"))
        .limit(5)
        .all()
    )
    attendance_ratio = 0
    if attendance:
        attendance_ratio = round(
            (len([a for a in attendance if a.status == "present"]) / len(attendance)) * 100, 2
        )
    return render_template(
        "admin/dashboard.html",
        students=students,
        teachers=teachers,
        pass_count=pass_count,
        fail_count=fail_count,
        top_students=top_students,
        attendance_ratio=attendance_ratio,
    )


@admin_bp.route("/users", methods=["GET", "POST"])
@login_required
@role_required("admin")
def manage_users():
    form = UserForm()
    form.class_id.choices = [(0, "N/A")] + [(c.id, f"{c.name}-{c.section}") for c in ClassRoom.query.all()]

    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            role=form.role.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        if form.role.data == "student":
            profile = Student(
                user_id=user.id,
                admission_no=form.code.data.strip(),
                class_id=form.class_id.data,
                roll_no=form.code.data.strip()[-4:],
            )
        else:
            profile = Teacher(user_id=user.id, employee_code=form.code.data.strip())
        db.session.add(profile)
        db.session.commit()
        flash("User created successfully.", "success")
        return redirect(url_for("admin.manage_users"))

    users = User.query.filter(User.role.in_(["teacher", "student"])).all()
    return render_template("admin/users.html", form=form, users=users)


@admin_bp.route("/students", methods=["GET", "POST"])
@login_required
@role_required("admin")
def manage_students():
    form = StudentForm()
    form.class_id.choices = [(c.id, f"{c.name}-{c.section}") for c in ClassRoom.query.all()]

    if form.validate_on_submit():
        if _email_exists(form.email.data):
            flash("Email already exists.", "danger")
            return redirect(url_for("admin.manage_students"))
        if Student.query.filter_by(admission_no=form.admission_no.data.strip()).first():
            flash("Admission number already exists.", "danger")
            return redirect(url_for("admin.manage_students"))

        user = _create_user(form.full_name.data, form.email.data, form.password.data, "student")
        db.session.add(
            Student(
                user_id=user.id,
                admission_no=form.admission_no.data.strip(),
                class_id=form.class_id.data,
                roll_no=form.roll_no.data.strip(),
                guardian_name=form.guardian_name.data.strip() or None,
            )
        )
        db.session.commit()
        flash("Student added successfully.", "success")
        return redirect(url_for("admin.manage_students"))

    search = request.args.get("q", "").strip()
    students_query = Student.query.join(User, Student.user_id == User.id).join(ClassRoom, Student.class_id == ClassRoom.id)
    if search:
        students_query = students_query.filter(
            db.or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                Student.admission_no.ilike(f"%{search}%"),
            )
        )
    students = students_query.order_by(Student.id.desc()).all()
    return render_template("admin/students.html", form=form, students=students, search=search)


@admin_bp.route("/teachers", methods=["GET", "POST"])
@login_required
@role_required("admin")
def manage_teachers():
    form = TeacherForm()
    if form.validate_on_submit():
        if _email_exists(form.email.data):
            flash("Email already exists.", "danger")
            return redirect(url_for("admin.manage_teachers"))
        if Teacher.query.filter_by(employee_code=form.employee_code.data.strip()).first():
            flash("Employee code already exists.", "danger")
            return redirect(url_for("admin.manage_teachers"))

        user = _create_user(form.full_name.data, form.email.data, form.password.data, "teacher")
        db.session.add(
            Teacher(
                user_id=user.id,
                employee_code=form.employee_code.data.strip(),
                qualification=form.qualification.data.strip() or None,
            )
        )
        db.session.commit()
        flash("Teacher added successfully.", "success")
        return redirect(url_for("admin.manage_teachers"))

    search = request.args.get("q", "").strip()
    teachers_query = Teacher.query.join(User, Teacher.user_id == User.id)
    if search:
        teachers_query = teachers_query.filter(
            db.or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                Teacher.employee_code.ilike(f"%{search}%"),
            )
        )
    teachers = teachers_query.order_by(Teacher.id.desc()).all()
    return render_template("admin/teachers.html", form=form, teachers=teachers, search=search)


@admin_bp.route("/broadcast", methods=["GET", "POST"])
@login_required
@role_required("admin")
def broadcast_notification():
    form = BroadcastForm()
    if form.validate_on_submit():
        query = User.query
        if form.role.data != "all":
            query = query.filter_by(role=form.role.data)
        users = query.all()

        for user in users:
            db.session.add(
                Notification(
                    user_id=user.id,
                    title=form.title.data.strip(),
                    message=form.message.data.strip(),
                )
            )
        db.session.commit()
        flash(f"Notification sent to {len(users)} users.", "success")
        return redirect(url_for("admin.broadcast_notification"))

    recent_notifications = Notification.query.order_by(Notification.created_at.desc()).limit(10).all()
    return render_template("admin/broadcast.html", form=form, recent_notifications=recent_notifications)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User removed.", "info")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/classes", methods=["GET", "POST"])
@login_required
@role_required("admin")
def classes():
    form = ClassForm()
    if form.validate_on_submit():
        db.session.add(ClassRoom(name=form.name.data, section=form.section.data))
        db.session.commit()
        flash("Class created.", "success")
        return redirect(url_for("admin.classes"))
    return render_template("admin/classes.html", form=form, classes=ClassRoom.query.all())


@admin_bp.route("/subjects", methods=["GET", "POST"])
@login_required
@role_required("admin")
def subjects():
    form = SubjectForm()
    if form.validate_on_submit():
        db.session.add(Subject(name=form.name.data, code=form.code.data))
        db.session.commit()
        flash("Subject created.", "success")
        return redirect(url_for("admin.subjects"))
    return render_template("admin/subjects.html", form=form, subjects=Subject.query.all())


@admin_bp.route("/assign", methods=["GET", "POST"])
@login_required
@role_required("admin")
def assign_teacher():
    form = AssignmentForm()
    form.teacher_id.choices = [(t.id, t.user.full_name) for t in Teacher.query.all()]
    form.class_id.choices = [(c.id, f"{c.name}-{c.section}") for c in ClassRoom.query.all()]
    form.subject_id.choices = [(s.id, f"{s.name} ({s.code})") for s in Subject.query.all()]

    if form.validate_on_submit():
        assign = TeacherSubjectAssignment(
            teacher_id=form.teacher_id.data,
            class_id=form.class_id.data,
            subject_id=form.subject_id.data,
        )
        db.session.add(assign)
        db.session.commit()
        flash("Teacher assigned successfully.", "success")
        return redirect(url_for("admin.assign_teacher"))

    assignments = TeacherSubjectAssignment.query.all()
    return render_template("admin/assignments.html", form=form, assignments=assignments)

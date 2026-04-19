import os
from datetime import date

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from flask_mail import Message
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import DateField, FloatField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange

from ...extensions import db, mail
from ...models import Assignment, Attendance, Mark, Notification, Student, Teacher, TeacherSubjectAssignment, User
from ...utils import calculate_grade, role_required

teacher_bp = Blueprint("teacher", __name__)


class MarksForm(FlaskForm):
    student_id = SelectField("Student", coerce=int)
    assignment_id = SelectField("Class-Subject", coerce=int)
    internal = FloatField("Internal", validators=[DataRequired(), NumberRange(min=0, max=40)])
    external = FloatField("External", validators=[DataRequired(), NumberRange(min=0, max=60)])
    submit = SubmitField("Save Marks")


class AttendanceForm(FlaskForm):
    student_id = SelectField("Student", coerce=int)
    assignment_id = SelectField("Class-Subject", coerce=int)
    day = DateField("Date", default=date.today, validators=[DataRequired()])
    status = SelectField("Status", choices=[("present", "Present"), ("absent", "Absent")])
    submit = SubmitField("Save Attendance")


def _teacher():
    return Teacher.query.filter_by(user_id=current_user.id).first_or_404()


@teacher_bp.route("/dashboard")
@login_required
@role_required("teacher")
def dashboard():
    teacher = _teacher()
    assigned = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher.id).all()
    marks_count = Mark.query.filter_by(teacher_id=teacher.id).count()
    assignments_count = Assignment.query.filter_by(teacher_id=teacher.id).count()
    return render_template(
        "teacher/dashboard.html",
        assigned=assigned,
        marks_count=marks_count,
        assignments_count=assignments_count,
    )


@teacher_bp.route("/marks", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def marks():
    teacher = _teacher()
    form = MarksForm()
    my_assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher.id).all()
    class_ids = {a.class_id for a in my_assignments}
    students = Student.query.filter(Student.class_id.in_(class_ids)).all() if class_ids else []
    form.student_id.choices = [(s.id, f"{s.user.full_name} ({s.admission_no})") for s in students]
    form.assignment_id.choices = [(a.id, f"{a.classroom.name}-{a.classroom.section} / {a.subject.name}") for a in my_assignments]

    if form.validate_on_submit():
        assign = TeacherSubjectAssignment.query.get_or_404(form.assignment_id.data)
        if assign.teacher_id != teacher.id:
            flash("Unauthorized action.", "danger")
            return redirect(url_for("teacher.marks"))

        student = Student.query.get_or_404(form.student_id.data)
        if student.class_id != assign.class_id:
            flash("Student is not in this class.", "danger")
            return redirect(url_for("teacher.marks"))

        total = form.internal.data + form.external.data
        percentage = total
        record = Mark(
            student_id=student.id,
            subject_id=assign.subject_id,
            class_id=assign.class_id,
            teacher_id=teacher.id,
            internal_marks=form.internal.data,
            external_marks=form.external.data,
            total_marks=total,
            percentage=percentage,
            grade=calculate_grade(percentage),
        )
        db.session.add(record)
        db.session.add(
            Notification(
                user_id=student.user_id,
                title="Marks Updated",
                message=f"Your marks for {assign.subject.name} have been published.",
            )
        )
        db.session.commit()
        flash("Marks saved.", "success")
        return redirect(url_for("teacher.marks"))

    marks_list = Mark.query.filter_by(teacher_id=teacher.id).order_by(Mark.created_at.desc()).all()
    return render_template("teacher/marks.html", form=form, marks_list=marks_list)


@teacher_bp.route("/attendance", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def attendance():
    teacher = _teacher()
    form = AttendanceForm()
    my_assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher.id).all()
    class_ids = {a.class_id for a in my_assignments}
    students = Student.query.filter(Student.class_id.in_(class_ids)).all() if class_ids else []
    form.student_id.choices = [(s.id, s.user.full_name) for s in students]
    form.assignment_id.choices = [(a.id, f"{a.classroom.name}-{a.classroom.section} / {a.subject.name}") for a in my_assignments]

    if form.validate_on_submit():
        assign = TeacherSubjectAssignment.query.get_or_404(form.assignment_id.data)
        if assign.teacher_id != teacher.id:
            flash("Unauthorized action.", "danger")
            return redirect(url_for("teacher.attendance"))
        entry = Attendance(
            student_id=form.student_id.data,
            class_id=assign.class_id,
            subject_id=assign.subject_id,
            teacher_id=teacher.id,
            day=form.day.data,
            status=form.status.data,
        )
        db.session.add(entry)
        db.session.commit()
        flash("Attendance recorded.", "success")
        return redirect(url_for("teacher.attendance"))
    return render_template("teacher/attendance.html", form=form)


@teacher_bp.route("/assignments", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def upload_assignment():
    teacher = _teacher()
    if request.method == "POST":
        assignment_id = int(request.form.get("assignment_id", "0"))
        title = request.form.get("title", "").strip()
        uploaded = request.files.get("file")
        assign = TeacherSubjectAssignment.query.get_or_404(assignment_id)
        if assign.teacher_id != teacher.id or not uploaded:
            flash("Invalid assignment upload request.", "danger")
            return redirect(url_for("teacher.upload_assignment"))

        filename = secure_filename(uploaded.filename)
        upload_dir = os.path.join(current_app.root_path, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        uploaded.save(filepath)

        db.session.add(
            Assignment(
                teacher_id=teacher.id,
                class_id=assign.class_id,
                subject_id=assign.subject_id,
                title=title,
                file_path=filename,
            )
        )
        db.session.commit()
        flash("File uploaded.", "success")
        return redirect(url_for("teacher.upload_assignment"))

    assignments = TeacherSubjectAssignment.query.filter_by(teacher_id=teacher.id).all()
    uploads = Assignment.query.filter_by(teacher_id=teacher.id).all()
    return render_template("teacher/assignments.html", assignments=assignments, uploads=uploads)


@teacher_bp.route("/send-result-email/<int:student_id>", methods=["POST"])
@login_required
@role_required("teacher")
def send_result_email(student_id):
    student = Student.query.get_or_404(student_id)
    user = User.query.get_or_404(student.user_id)
    msg = Message(
        subject="Academic Result Update",
        recipients=[user.email],
        body=f"Hello {user.full_name}, your latest results are available in the student portal.",
    )
    mail.send(msg)
    flash("Result email sent.", "success")
    return redirect(url_for("teacher.marks"))


@teacher_bp.route("/files/<path:filename>")
@login_required
@role_required("teacher", "student")
def files(filename):
    return send_from_directory(os.path.join(current_app.root_path, "uploads"), filename, as_attachment=True)

from datetime import datetime, date

from flask_login import UserMixin

from .extensions import bcrypt, db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student_profile = db.relationship("Student", back_populates="user", uselist=False)
    teacher_profile = db.relationship("Teacher", back_populates="user", uselist=False)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class ClassRoom(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    section = db.Column(db.String(20), nullable=False)

    students = db.relationship("Student", back_populates="classroom")
    subject_assignments = db.relationship("TeacherSubjectAssignment", back_populates="classroom")


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    admission_no = db.Column(db.String(30), unique=True, nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    roll_no = db.Column(db.String(20), nullable=False)
    guardian_name = db.Column(db.String(120), nullable=True)

    user = db.relationship("User", back_populates="student_profile")
    classroom = db.relationship("ClassRoom", back_populates="students")
    marks = db.relationship("Mark", back_populates="student")
    attendance = db.relationship("Attendance", back_populates="student")
    submissions = db.relationship("StudentSubmission", back_populates="student")


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    employee_code = db.Column(db.String(30), unique=True, nullable=False)
    qualification = db.Column(db.String(120), nullable=True)

    user = db.relationship("User", back_populates="teacher_profile")
    assignments = db.relationship("TeacherSubjectAssignment", back_populates="teacher")


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    code = db.Column(db.String(20), nullable=False, unique=True)

    assignments = db.relationship("TeacherSubjectAssignment", back_populates="subject")
    marks = db.relationship("Mark", back_populates="subject")
    assignments_uploaded = db.relationship("Assignment", back_populates="subject")


class TeacherSubjectAssignment(db.Model):
    __tablename__ = "teacher_subject_assignments"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)

    teacher = db.relationship("Teacher", back_populates="assignments")
    classroom = db.relationship("ClassRoom", back_populates="subject_assignments")
    subject = db.relationship("Subject", back_populates="assignments")

    __table_args__ = (
        db.UniqueConstraint("teacher_id", "class_id", "subject_id", name="uq_teacher_class_subject"),
    )


class Mark(db.Model):
    __tablename__ = "marks"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    internal_marks = db.Column(db.Float, nullable=False, default=0)
    external_marks = db.Column(db.Float, nullable=False, default=0)
    total_marks = db.Column(db.Float, nullable=False, default=0)
    percentage = db.Column(db.Float, nullable=False, default=0)
    grade = db.Column(db.String(2), nullable=False, default="F")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="marks")
    subject = db.relationship("Subject", back_populates="marks")


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    day = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(10), nullable=False, default="present")

    student = db.relationship("Student", back_populates="attendance")


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subject = db.relationship("Subject", back_populates="assignments_uploaded")
    submissions = db.relationship("StudentSubmission", back_populates="assignment")


class StudentSubmission(db.Model):
    __tablename__ = "student_submissions"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assignment = db.relationship("Assignment", back_populates="submissions")
    student = db.relationship("Student", back_populates="submissions")


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

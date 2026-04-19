import os

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import case, func
from werkzeug.utils import secure_filename

from ...extensions import db
from ...models import Assignment, Attendance, Mark, Student, StudentSubmission
from ...utils import role_required

student_bp = Blueprint("student", __name__)


def _student():
    return Student.query.filter_by(user_id=current_user.id).first_or_404()


@student_bp.route("/dashboard")
@login_required
@role_required("student")
def dashboard():
    student = _student()
    marks = Mark.query.filter_by(student_id=student.id).all()
    attendance = Attendance.query.filter_by(student_id=student.id).all()
    total_classes = len(attendance)
    present = len([a for a in attendance if a.status == "present"])
    attendance_per = round((present / total_classes) * 100, 2) if total_classes else 0

    assignments = Assignment.query.filter_by(class_id=student.class_id).all()
    submissions = (
        StudentSubmission.query.filter_by(student_id=student.id)
        .order_by(StudentSubmission.created_at.desc())
        .all()
    )
    chart_labels = [m.subject.name for m in marks]
    chart_values = [m.percentage for m in marks]
    predicted_performance = round(sum(chart_values) / len(chart_values), 2) if chart_values else 0

    return render_template(
        "student/dashboard.html",
        student=student,
        marks=marks,
        attendance_per=attendance_per,
        assignments=assignments,
        submissions=submissions,
        chart_labels=chart_labels,
        chart_values=chart_values,
        predicted_performance=predicted_performance,
    )


@student_bp.route("/profile")
@login_required
@role_required("student")
def profile():
    return render_template("student/profile.html", student=_student())


@student_bp.route("/monthly-report")
@login_required
@role_required("student")
def monthly_report():
    student = _student()
    dialect = db.engine.dialect.name
    if dialect == "postgresql":
        month_expr = func.to_char(Attendance.day, "YYYY-MM").label("month")
    else:
        # MySQL/MariaDB style
        month_expr = func.date_format(Attendance.day, "%Y-%m").label("month")

    monthly = (
        Attendance.query.with_entities(
            month_expr,
            func.sum(case((Attendance.status == "present", 1), else_=0)).label("present"),
            func.count(Attendance.id).label("total"),
        )
        .filter_by(student_id=student.id)
        .group_by(month_expr)
        .all()
    )
    return render_template("student/monthly_report.html", monthly=monthly)


@student_bp.route("/upload-assignment", methods=["GET", "POST"])
@login_required
@role_required("student")
def upload_assignment():
    student = _student()
    assignments = Assignment.query.filter_by(class_id=student.class_id).all()

    if request.method == "POST":
        assignment_id = int(request.form.get("assignment_id", "0"))
        title = request.form.get("title", "").strip()
        uploaded = request.files.get("file")

        assignment = Assignment.query.get_or_404(assignment_id)
        if assignment.class_id != student.class_id:
            flash("You can upload only for your class assignments.", "danger")
            return redirect(url_for("student.upload_assignment"))

        if not uploaded or not uploaded.filename:
            flash("Please select a file.", "danger")
            return redirect(url_for("student.upload_assignment"))

        filename = secure_filename(uploaded.filename)
        unique_filename = f"student_{student.id}_{assignment.id}_{filename}"
        upload_dir = os.path.join(current_app.root_path, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        uploaded.save(os.path.join(upload_dir, unique_filename))

        db.session.add(
            StudentSubmission(
                assignment_id=assignment.id,
                student_id=student.id,
                title=title or assignment.title,
                file_path=unique_filename,
            )
        )
        db.session.commit()
        flash("Assignment uploaded successfully.", "success")
        return redirect(url_for("student.upload_assignment"))

    submissions = (
        StudentSubmission.query.filter_by(student_id=student.id)
        .order_by(StudentSubmission.created_at.desc())
        .all()
    )
    return render_template(
        "student/upload_assignment.html",
        assignments=assignments,
        submissions=submissions,
    )

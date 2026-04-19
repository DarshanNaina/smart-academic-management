import random
from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Message
from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from ...extensions import db, mail
from ...models import ClassRoom, Student, Teacher, User


auth_bp = Blueprint("auth", __name__)


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Send OTP")


class OTPForm(FlaskForm):
    otp = StringField("One Time Password", validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField("Verify OTP")


class StudentRegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    admission_no = StringField("Admission Number", validators=[DataRequired(), Length(max=30)])
    roll_no = StringField("Roll Number", validators=[DataRequired(), Length(max=20)])
    guardian_name = StringField("Guardian Name", validators=[Length(max=120)])
    class_id = SelectField("Class", coerce=int, validate_choice=False)
    submit = SubmitField("Register Student")


class TeacherRegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    employee_code = StringField("Employee Code", validators=[DataRequired(), Length(max=30)])
    qualification = StringField("Qualification", validators=[Length(max=120)])
    submit = SubmitField("Register Teacher")


class AdminRegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register Admin")


def _send_otp_email(user_email, otp_code):
    msg = Message(
        subject="SAMS Login OTP",
        recipients=[user_email],
        body=f"Your Smart Academic Management System OTP is: {otp_code}. It expires in 5 minutes.",
    )
    mail.send(msg)


def _otp_expired():
    otp_expires_at = session.get("otp_expires_at")
    if not otp_expires_at:
        return True
    return datetime.utcnow() > datetime.fromisoformat(otp_expires_at)


def _clear_otp_session():
    session.pop("pending_user_id", None)
    session.pop("pending_next_page", None)
    session.pop("otp_code", None)
    session.pop("otp_expires_at", None)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard_router"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            otp_code = f"{random.randint(100000, 999999)}"
            session["pending_user_id"] = user.id
            session["pending_next_page"] = request.args.get("next")
            session["otp_code"] = otp_code
            session["otp_expires_at"] = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
            try:
                _send_otp_email(user.email, otp_code)
                flash("OTP sent to your email. Please verify.", "info")
            except Exception:
                flash("Mail not configured. OTP shown in flash for testing.", "warning")
                flash(f"Demo OTP: {otp_code}", "secondary")
            return redirect(url_for("auth.verify_otp"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard_router"))
    if not session.get("pending_user_id"):
        flash("Please login first to request an OTP.", "warning")
        return redirect(url_for("auth.login"))

    form = OTPForm()
    if form.validate_on_submit():
        if _otp_expired():
            _clear_otp_session()
            flash("OTP expired. Please login again.", "danger")
            return redirect(url_for("auth.login"))

        if form.otp.data.strip() != session.get("otp_code"):
            flash("Invalid OTP.", "danger")
            return redirect(url_for("auth.verify_otp"))

        user = User.query.get(session.get("pending_user_id"))
        if not user:
            _clear_otp_session()
            flash("User not found.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user)
        next_page = session.get("pending_next_page")
        _clear_otp_session()
        flash("Login successful with OTP.", "success")
        return redirect(next_page or url_for("main.dashboard_router"))

    return render_template("auth/verify_otp.html", form=form)


@auth_bp.route("/register/student", methods=["GET", "POST"])
def register_student():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard_router"))

    form = StudentRegisterForm()
    classes = ClassRoom.query.all()
    form.class_id.choices = [(c.id, f"{c.name}-{c.section}") for c in classes]

    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower().strip()).first():
            flash("Email already exists.", "danger")
            return redirect(url_for("auth.register_student"))
        if Student.query.filter_by(admission_no=form.admission_no.data.strip()).first():
            flash("Admission number already exists.", "danger")
            return redirect(url_for("auth.register_student"))

        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            role="student",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
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
        flash("Student registered successfully. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_student.html", form=form)


@auth_bp.route("/register/teacher", methods=["GET", "POST"])
def register_teacher():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard_router"))

    form = TeacherRegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower().strip()).first():
            flash("Email already exists.", "danger")
            return redirect(url_for("auth.register_teacher"))
        if Teacher.query.filter_by(employee_code=form.employee_code.data.strip()).first():
            flash("Employee code already exists.", "danger")
            return redirect(url_for("auth.register_teacher"))

        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            role="teacher",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        db.session.add(
            Teacher(
                user_id=user.id,
                employee_code=form.employee_code.data.strip(),
                qualification=form.qualification.data.strip() or None,
            )
        )
        db.session.commit()
        flash("Teacher registered successfully. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_teacher.html", form=form)


@auth_bp.route("/register/admin", methods=["GET", "POST"])
def register_admin():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard_router"))

    form = AdminRegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower().strip()).first():
            flash("Email already exists.", "danger")
            return redirect(url_for("auth.register_admin"))

        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            role="admin",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Admin registered successfully. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register_admin.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    _clear_otp_session()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

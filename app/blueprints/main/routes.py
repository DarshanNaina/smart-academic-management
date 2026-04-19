from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required

from ...models import Notification

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard_router():
    if current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    if current_user.role == "teacher":
        return redirect(url_for("teacher.dashboard"))
    if current_user.role == "student":
        return redirect(url_for("student.dashboard"))
    return redirect(url_for("auth.logout"))


@main_bp.route("/notifications")
@login_required
def notifications():
    notices = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return render_template("notifications.html", notices=notices)

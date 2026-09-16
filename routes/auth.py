from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from models.user import User
from services.audit_service import log_event

auth_bp = Blueprint("auth", __name__)


def _is_locked(user: User) -> bool:
    return bool(user.locked_until and user.locked_until > datetime.utcnow())


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # --- Basic input validation ---
        if not full_name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("register.html")

        # Password is hashed — never stored in plain text.
        user = User(full_name=full_name, email=email, role="vault_owner")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        log_event("register", user_id=user.id, resource="user_account")
        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        # Generic error message on purpose — never reveal whether the
        # email or the password was wrong (prevents user enumeration).
        generic_error = "Email or password is incorrect."

        if not user:
            log_event("login_failed", resource=email, result="failure")
            flash(generic_error, "danger")
            return render_template("login.html")

        if _is_locked(user):
            flash("This account is temporarily locked due to repeated failed "
                  "login attempts. Please try again later.", "danger")
            log_event("login_failed", user_id=user.id, resource="account_locked", result="failure")
            return render_template("login.html")

        if not user.check_password(password):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                user.failed_login_attempts = 0
                flash("Too many failed attempts. Account locked for 15 minutes.", "danger")
            else:
                flash(generic_error, "danger")
            db.session.commit()
            log_event("login_failed", user_id=user.id, result="failure")
            return render_template("login.html")

        # --- Successful login ---
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        db.session.commit()

        session.clear()
        session.permanent = True
        session["user_id"] = user.id
        session["role"] = user.role
        session["full_name"] = user.full_name

        log_event("login_success", user_id=user.id)
        flash(f"Welcome back, {user.full_name}!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    user_id = session.get("user_id")
    session.clear()
    if user_id:
        log_event("logout", user_id=user_id)
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

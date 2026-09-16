from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, flash
from models.user import User

dashboard_bp = Blueprint("dashboard", __name__)


def login_required(view_func):
    """Simple server-side session check. Every protected route must use this."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapped


@dashboard_bp.route("/dashboard")
@login_required
def index():
    user = User.query.get(session["user_id"])
    if not user:
        # Session refers to a user that no longer exists — force re-login.
        session.clear()
        return redirect(url_for("auth.login"))

    # Placeholder stats — Steps 4+ will replace these with real counts
    # (assets, nominees, documents, will instructions, digital accounts, tasks).
    stats = {
        "total_assets": 0,
        "total_nominees": 0,
        "total_documents": 0,
        "total_will_instructions": 0,
        "total_digital_accounts": 0,
        "total_tasks": 0,
    }

    return render_template("dashboard.html", user=user, stats=stats)

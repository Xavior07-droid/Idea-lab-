from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, flash
from models.user import User
from models.asset import Asset
from models.nominee import Nominee

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

    # Real counts for the modules that exist so far. Steps 5+ will add the
    # actual nominee/document/will/digital-account/task tables and these
    # will start counting real rows for this user instead of 0.
    stats = {
        "total_assets": Asset.query.filter_by(user_id=user.id).count(),
        "total_nominees": Nominee.query.filter_by(user_id=user.id).count(),
        "total_documents": 0,
        "total_will_instructions": 0,
        "total_digital_accounts": 0,
        "total_tasks": 0,
    }

    # Menu links to every module. Modules not built yet are marked disabled
    # so the dashboard is a real, honest "one central place" without
    # linking to routes that don't exist yet.
    modules = [
        {"name": "Assets", "endpoint": "assets.list_assets", "enabled": True},
        {"name": "Nominees", "endpoint": "nominees.list_nominees", "enabled": True},
        {"name": "Documents", "endpoint": None, "enabled": False},
        {"name": "Will", "endpoint": None, "enabled": False},
        {"name": "AI Checker", "endpoint": None, "enabled": False},
        {"name": "Digital Legacy", "endpoint": None, "enabled": False},
        {"name": "Trusted Contact", "endpoint": None, "enabled": False},
        {"name": "Life Verification", "endpoint": None, "enabled": False},
        {"name": "Inheritance Tasks", "endpoint": None, "enabled": False},
    ]

    return render_template("dashboard.html", user=user, stats=stats, modules=modules)

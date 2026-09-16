from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from models.nominee import Nominee
from models.asset import Asset
from routes.dashboard import login_required
from services.audit_service import log_event

nominees_bp = Blueprint("nominees", __name__, url_prefix="/nominees")


@nominees_bp.route("/")
@login_required
def list_nominees():
    nominees = (Nominee.query
                .filter_by(user_id=session["user_id"])
                .order_by(Nominee.created_at.desc())
                .all())
    return render_template("nominees.html", nominees=nominees)


@nominees_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_nominee():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        relationship = request.form.get("relationship", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not relationship:
            flash("Name and relationship are required.", "danger")
            return render_template("nominee_form.html", nominee=None, form=request.form)

        nominee = Nominee(
            user_id=session["user_id"],
            name=name,
            relationship=relationship,
            email=email or None,
            phone=phone or None,
        )
        db.session.add(nominee)
        db.session.commit()

        log_event("nominee_created", user_id=session["user_id"], resource=f"nominee:{nominee.id}")
        flash("Nominee added successfully.", "success")
        return redirect(url_for("nominees.list_nominees"))

    return render_template("nominee_form.html", nominee=None, form=None)


@nominees_bp.route("/<int:nominee_id>/edit", methods=["GET", "POST"])
@login_required
def edit_nominee(nominee_id):
    nominee = Nominee.query.filter_by(id=nominee_id, user_id=session["user_id"]).first()
    if not nominee:
        flash("Nominee not found.", "danger")
        return redirect(url_for("nominees.list_nominees"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        relationship = request.form.get("relationship", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not relationship:
            flash("Name and relationship are required.", "danger")
            return render_template("nominee_form.html", nominee=nominee, form=request.form)

        nominee.name = name
        nominee.relationship = relationship
        nominee.email = email or None
        nominee.phone = phone or None
        db.session.commit()

        log_event("nominee_updated", user_id=session["user_id"], resource=f"nominee:{nominee.id}")
        flash("Nominee updated successfully.", "success")
        return redirect(url_for("nominees.list_nominees"))

    return render_template("nominee_form.html", nominee=nominee, form=None)


@nominees_bp.route("/<int:nominee_id>/delete", methods=["POST"])
@login_required
def delete_nominee(nominee_id):
    nominee = Nominee.query.filter_by(id=nominee_id, user_id=session["user_id"]).first()
    if not nominee:
        flash("Nominee not found.", "danger")
        return redirect(url_for("nominees.list_nominees"))

    db.session.delete(nominee)
    db.session.commit()

    log_event("nominee_deleted", user_id=session["user_id"], resource=f"nominee:{nominee_id}")
    flash("Nominee deleted.", "info")
    return redirect(url_for("nominees.list_nominees"))


@nominees_bp.route("/<int:nominee_id>/assign", methods=["GET", "POST"])
@login_required
def assign_nominee(nominee_id):
    """Assign this nominee to one or more of the user's assets."""
    nominee = Nominee.query.filter_by(id=nominee_id, user_id=session["user_id"]).first()
    if not nominee:
        flash("Nominee not found.", "danger")
        return redirect(url_for("nominees.list_nominees"))

    assets = Asset.query.filter_by(user_id=session["user_id"]).order_by(Asset.name).all()

    if request.method == "POST":
        selected_ids = set(int(i) for i in request.form.getlist("asset_ids"))

        for asset in assets:
            currently_assigned = nominee.assets.filter(Asset.id == asset.id).first() is not None
            should_be_assigned = asset.id in selected_ids

            if should_be_assigned and not currently_assigned:
                nominee.assets.append(asset)
            elif currently_assigned and not should_be_assigned:
                nominee.assets.remove(asset)

        db.session.commit()
        log_event("nominee_assigned", user_id=session["user_id"], resource=f"nominee:{nominee.id}")
        flash(f"Assets updated for {nominee.name}.", "success")
        return redirect(url_for("nominees.list_nominees"))

    assigned_ids = {a.id for a in nominee.assets}
    return render_template("nominee_assign.html", nominee=nominee, assets=assets, assigned_ids=assigned_ids)

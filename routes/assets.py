from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db
from models.asset import Asset
from routes.dashboard import login_required
from services.audit_service import log_event

assets_bp = Blueprint("assets", __name__, url_prefix="/assets")

CATEGORIES = ["Property", "Bank Account", "Insurance", "Vehicle", "Investment", "Other"]


@assets_bp.route("/")
@login_required
def list_assets():
    assets = (Asset.query
              .filter_by(user_id=session["user_id"])
              .order_by(Asset.created_at.desc())
              .all())
    return render_template("assets.html", assets=assets)


@assets_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_asset():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        provider = request.form.get("provider", "").strip()
        reference = request.form.get("reference", "").strip()
        approx_value = request.form.get("approx_value", "").strip()
        description = request.form.get("description", "").strip()

        if not name or not category:
            flash("Name and category are required.", "danger")
            return render_template("asset_form.html", categories=CATEGORIES, asset=None, form=request.form)

        value = None
        if approx_value:
            try:
                value = float(approx_value)
            except ValueError:
                flash("Approximate value must be a number.", "danger")
                return render_template("asset_form.html", categories=CATEGORIES, asset=None, form=request.form)

        asset = Asset(
            user_id=session["user_id"],
            name=name,
            category=category,
            provider=provider or None,
            reference=reference or None,
            approx_value=value,
            description=description or None,
        )
        db.session.add(asset)
        db.session.commit()

        log_event("asset_created", user_id=session["user_id"], resource=f"asset:{asset.id}")
        flash("Asset added successfully.", "success")
        return redirect(url_for("assets.list_assets"))

    return render_template("asset_form.html", categories=CATEGORIES, asset=None, form=None)


@assets_bp.route("/<int:asset_id>/edit", methods=["GET", "POST"])
@login_required
def edit_asset(asset_id):
    asset = Asset.query.filter_by(id=asset_id, user_id=session["user_id"]).first()
    if not asset:
        flash("Asset not found.", "danger")
        return redirect(url_for("assets.list_assets"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        provider = request.form.get("provider", "").strip()
        reference = request.form.get("reference", "").strip()
        approx_value = request.form.get("approx_value", "").strip()
        description = request.form.get("description", "").strip()

        if not name or not category:
            flash("Name and category are required.", "danger")
            return render_template("asset_form.html", categories=CATEGORIES, asset=asset, form=request.form)

        value = None
        if approx_value:
            try:
                value = float(approx_value)
            except ValueError:
                flash("Approximate value must be a number.", "danger")
                return render_template("asset_form.html", categories=CATEGORIES, asset=asset, form=request.form)

        asset.name = name
        asset.category = category
        asset.provider = provider or None
        asset.reference = reference or None
        asset.approx_value = value
        asset.description = description or None
        db.session.commit()

        log_event("asset_updated", user_id=session["user_id"], resource=f"asset:{asset.id}")
        flash("Asset updated successfully.", "success")
        return redirect(url_for("assets.list_assets"))

    return render_template("asset_form.html", categories=CATEGORIES, asset=asset, form=None)


@assets_bp.route("/<int:asset_id>/delete", methods=["POST"])
@login_required
def delete_asset(asset_id):
    asset = Asset.query.filter_by(id=asset_id, user_id=session["user_id"]).first()
    if not asset:
        flash("Asset not found.", "danger")
        return redirect(url_for("assets.list_assets"))

    db.session.delete(asset)
    db.session.commit()

    log_event("asset_deleted", user_id=session["user_id"], resource=f"asset:{asset_id}")
    flash("Asset deleted.", "info")
    return redirect(url_for("assets.list_assets"))

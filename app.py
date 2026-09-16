import os
import uuid
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory,
    abort,
)
from werkzeug.utils import secure_filename

from datetime import datetime, timedelta

from models import (
    db,
    User,
    Asset,
    Nominee,
    WillInstruction,
    Document,
    DigitalAccount,
    TrustedContact,
    LifeVerification,
    Task,
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB per upload

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key-change-me"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    BASE_DIR, "database", "legacy_vault.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

db.init_app(app)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


# ---------------------------------------------------------------------------
# Home / Auth  (Step 1 & 2)
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("register"))

        user = User(full_name=full_name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            session["full_name"] = user.full_name
            flash(f"Welcome back, {user.full_name}!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Dashboard (Step 3)
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    stats = {
        "assets": Asset.query.filter_by(user_id=user.id).count(),
        "nominees": Nominee.query.filter_by(user_id=user.id).count(),
        "documents": Document.query.filter_by(user_id=user.id).count(),
        "will_instructions": WillInstruction.query.filter_by(user_id=user.id).count(),
        "digital_accounts": DigitalAccount.query.filter_by(user_id=user.id).count(),
        "tasks": Task.query.filter_by(user_id=user.id).count(),
    }
    verification = get_or_create_verification(user)
    if verification.next_verification_due < datetime.utcnow() and verification.status == "OK":
        verification.status = "VERIFICATION_REQUIRED"
        db.session.commit()
    return render_template("dashboard.html", stats=stats, verification=verification)


# ---------------------------------------------------------------------------
# Asset Management (Step 4)
# ---------------------------------------------------------------------------
@app.route("/assets")
@login_required
def assets_list():
    user = current_user()
    assets = Asset.query.filter_by(user_id=user.id).order_by(Asset.created_at.desc()).all()
    return render_template("assets.html", assets=assets)


@app.route("/assets/add", methods=["GET", "POST"])
@login_required
def asset_add():
    if request.method == "POST":
        user = current_user()
        asset = Asset(
            user_id=user.id,
            name=request.form.get("name", "").strip(),
            category=request.form.get("category", "").strip(),
            provider=request.form.get("provider", "").strip(),
            reference=request.form.get("reference", "").strip(),
            approx_value=float(request.form.get("approx_value") or 0),
            description=request.form.get("description", "").strip(),
        )

        if not asset.name or not asset.category:
            flash("Asset name and category are required.", "danger")
            return redirect(url_for("asset_add"))

        db.session.add(asset)
        db.session.commit()
        flash("Asset added successfully.", "success")
        return redirect(url_for("assets_list"))

    return render_template("asset_form.html", asset=None)


@app.route("/assets/<int:asset_id>/edit", methods=["GET", "POST"])
@login_required
def asset_edit(asset_id):
    user = current_user()
    asset = Asset.query.filter_by(id=asset_id, user_id=user.id).first_or_404()

    if request.method == "POST":
        asset.name = request.form.get("name", "").strip()
        asset.category = request.form.get("category", "").strip()
        asset.provider = request.form.get("provider", "").strip()
        asset.reference = request.form.get("reference", "").strip()
        asset.approx_value = float(request.form.get("approx_value") or 0)
        asset.description = request.form.get("description", "").strip()

        db.session.commit()
        flash("Asset updated successfully.", "success")
        return redirect(url_for("assets_list"))

    return render_template("asset_form.html", asset=asset)


@app.route("/assets/<int:asset_id>/delete", methods=["POST"])
@login_required
def asset_delete(asset_id):
    user = current_user()
    asset = Asset.query.filter_by(id=asset_id, user_id=user.id).first_or_404()
    db.session.delete(asset)
    db.session.commit()
    flash("Asset deleted.", "info")
    return redirect(url_for("assets_list"))


# ---------------------------------------------------------------------------
# Nominee Management (Step 5)
# ---------------------------------------------------------------------------
@app.route("/nominees")
@login_required
def nominees_list():
    user = current_user()
    nominees = (
        Nominee.query.filter_by(user_id=user.id).order_by(Nominee.created_at.desc()).all()
    )
    return render_template("nominees.html", nominees=nominees)


@app.route("/nominees/add", methods=["GET", "POST"])
@login_required
def nominee_add():
    if request.method == "POST":
        user = current_user()
        nominee = Nominee(
            user_id=user.id,
            name=request.form.get("name", "").strip(),
            relationship_=request.form.get("relationship", "").strip(),
            email=request.form.get("email", "").strip(),
            phone=request.form.get("phone", "").strip(),
        )

        if not nominee.name or not nominee.relationship_:
            flash("Nominee name and relationship are required.", "danger")
            return redirect(url_for("nominee_add"))

        db.session.add(nominee)
        db.session.commit()
        flash("Nominee added successfully.", "success")
        return redirect(url_for("nominees_list"))

    return render_template("nominee_form.html", nominee=None)


@app.route("/nominees/<int:nominee_id>/edit", methods=["GET", "POST"])
@login_required
def nominee_edit(nominee_id):
    user = current_user()
    nominee = Nominee.query.filter_by(id=nominee_id, user_id=user.id).first_or_404()

    if request.method == "POST":
        nominee.name = request.form.get("name", "").strip()
        nominee.relationship_ = request.form.get("relationship", "").strip()
        nominee.email = request.form.get("email", "").strip()
        nominee.phone = request.form.get("phone", "").strip()

        db.session.commit()
        flash("Nominee updated successfully.", "success")
        return redirect(url_for("nominees_list"))

    return render_template("nominee_form.html", nominee=nominee)


@app.route("/nominees/<int:nominee_id>/delete", methods=["POST"])
@login_required
def nominee_delete(nominee_id):
    user = current_user()
    nominee = Nominee.query.filter_by(id=nominee_id, user_id=user.id).first_or_404()
    db.session.delete(nominee)
    db.session.commit()
    flash("Nominee deleted.", "info")
    return redirect(url_for("nominees_list"))


@app.route("/assets/<int:asset_id>/assign-nominee", methods=["GET", "POST"])
@login_required
def assign_nominee(asset_id):
    user = current_user()
    asset = Asset.query.filter_by(id=asset_id, user_id=user.id).first_or_404()
    all_nominees = Nominee.query.filter_by(user_id=user.id).all()

    if request.method == "POST":
        nominee_id = request.form.get("nominee_id")
        nominee = Nominee.query.filter_by(id=nominee_id, user_id=user.id).first()

        if not nominee:
            flash("Please select a valid nominee.", "danger")
        elif nominee in asset.nominees:
            flash("This nominee is already assigned to the asset.", "warning")
        else:
            asset.nominees.append(nominee)
            db.session.commit()
            flash(f"{nominee.name} assigned to {asset.name}.", "success")

        return redirect(url_for("assign_nominee", asset_id=asset.id))

    return render_template("assign_nominee.html", asset=asset, all_nominees=all_nominees)


@app.route("/assets/<int:asset_id>/remove-nominee/<int:nominee_id>", methods=["POST"])
@login_required
def remove_nominee(asset_id, nominee_id):
    user = current_user()
    asset = Asset.query.filter_by(id=asset_id, user_id=user.id).first_or_404()
    nominee = Nominee.query.filter_by(id=nominee_id, user_id=user.id).first_or_404()

    if nominee in asset.nominees:
        asset.nominees.remove(nominee)
        db.session.commit()
        flash(f"{nominee.name} removed from {asset.name}.", "info")

    return redirect(url_for("assign_nominee", asset_id=asset.id))


# ---------------------------------------------------------------------------
# Will / Inheritance Instructions (Step 6)
# ---------------------------------------------------------------------------
@app.route("/will")
@login_required
def will_list():
    user = current_user()
    instructions = (
        WillInstruction.query.filter_by(user_id=user.id)
        .order_by(WillInstruction.created_at.desc())
        .all()
    )
    return render_template("will.html", instructions=instructions)


@app.route("/will/add", methods=["GET", "POST"])
@login_required
def will_add():
    user = current_user()
    user_assets = Asset.query.filter_by(user_id=user.id).all()

    if request.method == "POST":
        asset_id = request.form.get("asset_id") or None
        beneficiary_name = request.form.get("beneficiary_name", "").strip()
        instruction_text = request.form.get("instruction_text", "").strip()

        if not beneficiary_name or not instruction_text:
            flash("Beneficiary and instruction text are required.", "danger")
            return redirect(url_for("will_add"))

        instruction = WillInstruction(
            user_id=user.id,
            asset_id=int(asset_id) if asset_id else None,
            beneficiary_name=beneficiary_name,
            instruction_text=instruction_text,
        )
        db.session.add(instruction)
        db.session.commit()
        flash("Will instruction added successfully.", "success")
        return redirect(url_for("will_list"))

    return render_template("will_form.html", instruction=None, user_assets=user_assets)


@app.route("/will/<int:instruction_id>/edit", methods=["GET", "POST"])
@login_required
def will_edit(instruction_id):
    user = current_user()
    instruction = WillInstruction.query.filter_by(
        id=instruction_id, user_id=user.id
    ).first_or_404()
    user_assets = Asset.query.filter_by(user_id=user.id).all()

    if request.method == "POST":
        asset_id = request.form.get("asset_id") or None
        instruction.asset_id = int(asset_id) if asset_id else None
        instruction.beneficiary_name = request.form.get("beneficiary_name", "").strip()
        instruction.instruction_text = request.form.get("instruction_text", "").strip()

        db.session.commit()
        flash("Will instruction updated successfully.", "success")
        return redirect(url_for("will_list"))

    return render_template("will_form.html", instruction=instruction, user_assets=user_assets)


@app.route("/will/<int:instruction_id>/delete", methods=["POST"])
@login_required
def will_delete(instruction_id):
    user = current_user()
    instruction = WillInstruction.query.filter_by(
        id=instruction_id, user_id=user.id
    ).first_or_404()
    db.session.delete(instruction)
    db.session.commit()
    flash("Will instruction deleted.", "info")
    return redirect(url_for("will_list"))


# ---------------------------------------------------------------------------
# Will Checker (Step 7) — simple rule-based checks, no AI
# ---------------------------------------------------------------------------
@app.route("/will/checker")
@login_required
def will_checker():
    user = current_user()

    assets = Asset.query.filter_by(user_id=user.id).all()
    instructions = WillInstruction.query.filter_by(user_id=user.id).all()

    results = []

    # Rule 1: Asset without any will instruction
    for asset in assets:
        has_instruction = any(i.asset_id == asset.id for i in instructions)
        if has_instruction:
            results.append({
                "rule": "Asset has a will instruction",
                "subject": asset.name,
                "status": "PASS",
                "detail": f'"{asset.name}" is covered by a will instruction.',
            })
        else:
            results.append({
                "rule": "Asset has a will instruction",
                "subject": asset.name,
                "status": "WARNING",
                "detail": f'"{asset.name}" has no will instruction linked to it.',
            })

    # Rule 2: Will instruction pointing to a missing/deleted asset
    for instruction in instructions:
        if instruction.asset_id is not None and instruction.asset is None:
            results.append({
                "rule": "Instruction refers to an existing asset",
                "subject": instruction.beneficiary_name,
                "status": "WARNING",
                "detail": (
                    f'Instruction for "{instruction.beneficiary_name}" refers to '
                    "an asset that no longer exists."
                ),
            })
        else:
            results.append({
                "rule": "Instruction refers to an existing asset",
                "subject": instruction.beneficiary_name,
                "status": "PASS",
                "detail": (
                    f'Instruction for "{instruction.beneficiary_name}" refers to '
                    f'"{instruction.asset.name}".'
                    if instruction.asset
                    else f'Instruction for "{instruction.beneficiary_name}" is not tied to a specific asset.'
                ),
            })

    # Rule 3: Asset without any nominee assigned
    for asset in assets:
        if asset.nominees:
            results.append({
                "rule": "Asset has a nominee",
                "subject": asset.name,
                "status": "PASS",
                "detail": f'"{asset.name}" has at least one nominee assigned.',
            })
        else:
            results.append({
                "rule": "Asset has a nominee",
                "subject": asset.name,
                "status": "WARNING",
                "detail": f'"{asset.name}" has no nominee assigned.',
            })

    # Rule 4: Will instruction without a beneficiary
    for instruction in instructions:
        if instruction.beneficiary_name and instruction.beneficiary_name.strip():
            results.append({
                "rule": "Instruction has a beneficiary",
                "subject": instruction.instruction_text[:40],
                "status": "PASS",
                "detail": f'Instruction is assigned to beneficiary "{instruction.beneficiary_name}".',
            })
        else:
            results.append({
                "rule": "Instruction has a beneficiary",
                "subject": instruction.instruction_text[:40],
                "status": "WARNING",
                "detail": "Instruction has no beneficiary specified.",
            })

    warning_count = sum(1 for r in results if r["status"] == "WARNING")
    pass_count = sum(1 for r in results if r["status"] == "PASS")

    return render_template(
        "will_checker.html",
        results=results,
        warning_count=warning_count,
        pass_count=pass_count,
        has_data=bool(assets or instructions),
    )


# ---------------------------------------------------------------------------
# Document Management (Step 8)
# ---------------------------------------------------------------------------
@app.route("/documents")
@login_required
def documents_list():
    user = current_user()
    documents = (
        Document.query.filter_by(user_id=user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return render_template("documents.html", documents=documents)


@app.route("/documents/upload", methods=["GET", "POST"])
@login_required
def document_upload():
    if request.method == "POST":
        user = current_user()

        file = request.files.get("file")
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()

        if not file or file.filename == "":
            flash("Please choose a file to upload.", "danger")
            return redirect(url_for("document_upload"))

        if not allowed_file(file.filename):
            flash("Only PDF, JPG, JPEG and PNG files are allowed.", "danger")
            return redirect(url_for("document_upload"))

        original_filename = secure_filename(file.filename)
        ext = original_filename.rsplit(".", 1)[1].lower()
        stored_filename = f"{uuid.uuid4().hex}.{ext}"

        filepath = os.path.join(UPLOAD_DIR, stored_filename)
        file.save(filepath)
        file_size = os.path.getsize(filepath)

        document = Document(
            user_id=user.id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            category=category or "Other",
            description=description,
            file_size=file_size,
        )
        db.session.add(document)
        db.session.commit()

        flash("Document uploaded successfully.", "success")
        return redirect(url_for("documents_list"))

    return render_template("document_upload.html")


@app.route("/documents/<int:document_id>/download")
@login_required
def document_download(document_id):
    user = current_user()
    document = Document.query.filter_by(id=document_id, user_id=user.id).first_or_404()
    return send_from_directory(
        UPLOAD_DIR, document.stored_filename, as_attachment=True,
        download_name=document.original_filename,
    )


@app.route("/documents/<int:document_id>/delete", methods=["POST"])
@login_required
def document_delete(document_id):
    user = current_user()
    document = Document.query.filter_by(id=document_id, user_id=user.id).first_or_404()

    filepath = os.path.join(UPLOAD_DIR, document.stored_filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(document)
    db.session.commit()
    flash("Document deleted.", "info")
    return redirect(url_for("documents_list"))


# ---------------------------------------------------------------------------
# Digital Legacy — digital accounts (Step 9)
# ---------------------------------------------------------------------------
DIGITAL_ACCOUNT_ACTIONS = ["Preserve", "Memorialize", "Transfer", "Delete"]


@app.route("/digital-legacy")
@login_required
def digital_accounts_list():
    user = current_user()
    accounts = (
        DigitalAccount.query.filter_by(user_id=user.id)
        .order_by(DigitalAccount.created_at.desc())
        .all()
    )
    return render_template("digital_legacy.html", accounts=accounts)


@app.route("/digital-legacy/add", methods=["GET", "POST"])
@login_required
def digital_account_add():
    if request.method == "POST":
        user = current_user()
        account = DigitalAccount(
            user_id=user.id,
            service=request.form.get("service", "").strip(),
            account_identifier=request.form.get("account_identifier", "").strip(),
            action=request.form.get("action", "").strip(),
            beneficiary=request.form.get("beneficiary", "").strip(),
            instructions=request.form.get("instructions", "").strip(),
        )

        if not account.service or not account.account_identifier or not account.action:
            flash("Service, account identifier and action are required.", "danger")
            return redirect(url_for("digital_account_add"))

        db.session.add(account)
        db.session.commit()
        flash("Digital account added successfully.", "success")
        return redirect(url_for("digital_accounts_list"))

    return render_template(
        "digital_legacy_form.html", account=None, actions=DIGITAL_ACCOUNT_ACTIONS
    )


@app.route("/digital-legacy/<int:account_id>/edit", methods=["GET", "POST"])
@login_required
def digital_account_edit(account_id):
    user = current_user()
    account = DigitalAccount.query.filter_by(
        id=account_id, user_id=user.id
    ).first_or_404()

    if request.method == "POST":
        account.service = request.form.get("service", "").strip()
        account.account_identifier = request.form.get("account_identifier", "").strip()
        account.action = request.form.get("action", "").strip()
        account.beneficiary = request.form.get("beneficiary", "").strip()
        account.instructions = request.form.get("instructions", "").strip()

        db.session.commit()
        flash("Digital account updated successfully.", "success")
        return redirect(url_for("digital_accounts_list"))

    return render_template(
        "digital_legacy_form.html", account=account, actions=DIGITAL_ACCOUNT_ACTIONS
    )


@app.route("/digital-legacy/<int:account_id>/delete", methods=["POST"])
@login_required
def digital_account_delete(account_id):
    user = current_user()
    account = DigitalAccount.query.filter_by(
        id=account_id, user_id=user.id
    ).first_or_404()
    db.session.delete(account)
    db.session.commit()
    flash("Digital account deleted.", "info")
    return redirect(url_for("digital_accounts_list"))


# ---------------------------------------------------------------------------
# Trusted Contact (Step 10)
# ---------------------------------------------------------------------------
@app.route("/trusted-contacts")
@login_required
def trusted_contacts_list():
    user = current_user()
    contacts = (
        TrustedContact.query.filter_by(user_id=user.id)
        .order_by(TrustedContact.created_at.desc())
        .all()
    )
    return render_template("trusted_contacts.html", contacts=contacts)


@app.route("/trusted-contacts/add", methods=["GET", "POST"])
@login_required
def trusted_contact_add():
    if request.method == "POST":
        user = current_user()
        contact = TrustedContact(
            user_id=user.id,
            name=request.form.get("name", "").strip(),
            relationship_=request.form.get("relationship", "").strip(),
            email=request.form.get("email", "").strip(),
            phone=request.form.get("phone", "").strip(),
        )

        if not contact.name or not contact.relationship_:
            flash("Name and relationship are required.", "danger")
            return redirect(url_for("trusted_contact_add"))

        db.session.add(contact)
        db.session.commit()
        flash("Trusted contact added successfully.", "success")
        return redirect(url_for("trusted_contacts_list"))

    return render_template("trusted_contact_form.html", contact=None)


@app.route("/trusted-contacts/<int:contact_id>/edit", methods=["GET", "POST"])
@login_required
def trusted_contact_edit(contact_id):
    user = current_user()
    contact = TrustedContact.query.filter_by(
        id=contact_id, user_id=user.id
    ).first_or_404()

    if request.method == "POST":
        contact.name = request.form.get("name", "").strip()
        contact.relationship_ = request.form.get("relationship", "").strip()
        contact.email = request.form.get("email", "").strip()
        contact.phone = request.form.get("phone", "").strip()

        db.session.commit()
        flash("Trusted contact updated successfully.", "success")
        return redirect(url_for("trusted_contacts_list"))

    return render_template("trusted_contact_form.html", contact=contact)


@app.route("/trusted-contacts/<int:contact_id>/delete", methods=["POST"])
@login_required
def trusted_contact_delete(contact_id):
    user = current_user()
    contact = TrustedContact.query.filter_by(
        id=contact_id, user_id=user.id
    ).first_or_404()
    db.session.delete(contact)
    db.session.commit()
    flash("Trusted contact deleted.", "info")
    return redirect(url_for("trusted_contacts_list"))


# ---------------------------------------------------------------------------
# Life Verification (Step 11) — SIMULATION ONLY
#
# This module never releases anything automatically. It only tracks a
# last/next check-in date and a status flag. A missed verification just
# flips the status to VERIFICATION_REQUIRED for the user to see.
# ---------------------------------------------------------------------------
def get_or_create_verification(user):
    record = LifeVerification.query.filter_by(user_id=user.id).first()
    if not record:
        now = datetime.utcnow()
        record = LifeVerification(
            user_id=user.id,
            last_verified_at=now,
            next_verification_due=now + timedelta(days=30),
            status="OK",
            verification_interval_days=30,
        )
        db.session.add(record)
        db.session.commit()
    return record


@app.route("/life-verification")
@login_required
def life_verification():
    user = current_user()
    record = get_or_create_verification(user)

    # If the due date has quietly passed (e.g. app reopened later),
    # reflect that in the status without doing anything else.
    if record.next_verification_due < datetime.utcnow() and record.status == "OK":
        record.status = "VERIFICATION_REQUIRED"
        db.session.commit()

    return render_template("life_verification.html", record=record)


@app.route("/life-verification/confirm", methods=["POST"])
@login_required
def life_verification_confirm():
    user = current_user()
    record = get_or_create_verification(user)

    now = datetime.utcnow()
    record.last_verified_at = now
    record.next_verification_due = now + timedelta(days=record.verification_interval_days)
    record.status = "OK"
    db.session.commit()

    flash("Life status confirmed. Next verification date has been reset.", "success")
    return redirect(url_for("life_verification"))


@app.route("/life-verification/simulate-missed", methods=["POST"])
@login_required
def life_verification_simulate_missed():
    """Development/demo only: pretend the check-in window passed."""
    user = current_user()
    record = get_or_create_verification(user)

    record.next_verification_due = datetime.utcnow() - timedelta(days=1)
    record.status = "VERIFICATION_REQUIRED"
    db.session.commit()

    flash(
        "Simulated a missed verification. Status is now VERIFICATION_REQUIRED. "
        "Nothing has been released — this is a demo only.",
        "warning",
    )
    return redirect(url_for("life_verification"))


# ---------------------------------------------------------------------------
# Inheritance Tasks (Step 12)
# ---------------------------------------------------------------------------
TASK_STATUSES = ["Pending", "In Progress", "Completed"]


@app.route("/tasks")
@login_required
def tasks_list():
    user = current_user()
    tasks = Task.query.filter_by(user_id=user.id).order_by(Task.created_at.desc()).all()
    return render_template("tasks.html", tasks=tasks, statuses=TASK_STATUSES)


@app.route("/tasks/add", methods=["GET", "POST"])
@login_required
def task_add():
    if request.method == "POST":
        user = current_user()
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "Pending").strip()

        if not title:
            flash("Task title is required.", "danger")
            return redirect(url_for("task_add"))

        if status not in TASK_STATUSES:
            status = "Pending"

        task = Task(
            user_id=user.id,
            title=title,
            description=description,
            status=status,
        )
        db.session.add(task)
        db.session.commit()
        flash("Task added successfully.", "success")
        return redirect(url_for("tasks_list"))

    return render_template("task_form.html", task=None, statuses=TASK_STATUSES)


@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def task_edit(task_id):
    user = current_user()
    task = Task.query.filter_by(id=task_id, user_id=user.id).first_or_404()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        status = request.form.get("status", "Pending").strip()

        if not title:
            flash("Task title is required.", "danger")
            return redirect(url_for("task_edit", task_id=task.id))

        task.title = title
        task.description = request.form.get("description", "").strip()
        task.status = status if status in TASK_STATUSES else "Pending"

        db.session.commit()
        flash("Task updated successfully.", "success")
        return redirect(url_for("tasks_list"))

    return render_template("task_form.html", task=task, statuses=TASK_STATUSES)


@app.route("/tasks/<int:task_id>/status", methods=["POST"])
@login_required
def task_update_status(task_id):
    """Quick status change from the task list (no full edit form)."""
    user = current_user()
    task = Task.query.filter_by(id=task_id, user_id=user.id).first_or_404()

    new_status = request.form.get("status", "").strip()
    if new_status in TASK_STATUSES:
        task.status = new_status
        db.session.commit()
        flash(f'Task "{task.title}" marked as {new_status}.', "success")
    else:
        flash("Invalid status.", "danger")

    return redirect(url_for("tasks_list"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def task_delete(task_id):
    user = current_user()
    task = Task.query.filter_by(id=task_id, user_id=user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "info")
    return redirect(url_for("tasks_list"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)

# Digital Legacy Vault — Prototype (Steps 1–14)

A working Flask prototype for the Digital Legacy Vault & Inheritance
Management System. All 14 build steps are implemented:

1. Project setup
2. User registration / login / logout
3. Dashboard
4. Asset management (add / view / edit / delete)
5. Nominee management (add / view / edit / delete, assign to assets)
6. Will / Inheritance instructions (add / view / edit / delete)
7. Will Checker (rule-based, no AI)
8. Document Management (upload / view / download / delete — PDF, JPG, JPEG, PNG)
9. Digital Legacy (digital accounts: add / view / edit / delete)
10. Trusted Contact (add / view / edit / delete)
11. Life Verification (simulation only — never auto-releases anything)
12. Inheritance Tasks (add / view / edit / delete, quick status change)
13. Everything connected via the dashboard and nav bar
14. Demo data seeding (`seed_demo.py`)

## Run it locally

```bash
cd digital-legacy-vault

# create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# install dependencies
pip install -r requirements.txt

# run the app
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

The SQLite database is created automatically at
`database/legacy_vault.db` the first time you run the app.

## Try it out — fastest way (with demo data)

```bash
python seed_demo.py
python app.py
```

Log in with:
- **Email:** demo@vault.local
- **Password:** demo1234

This gives you 5 assets, 3 nominees, 3 will instructions, 2 digital
accounts, 1 trusted contact, and 5 inheritance tasks already set up.
One asset ("Mutual Fund") is intentionally left without a nominee or
will instruction — open **Will → Checker** to see it flagged as a
WARNING.

## Try it out — manual walkthrough (no seed data)

1. Register a new account.
2. Log in — you'll land on the Dashboard.
3. Add a couple of Assets (e.g. "Mumbai Property", "Bank Account").
4. Add a couple of Nominees (e.g. "Mother", "Brother").
5. From the Assets page, click **Nominees** on an asset to assign one.
6. Go to **Will** and add an inheritance instruction, e.g.
   Asset: Mumbai Property, Beneficiary: Mother,
   Instruction: "Transfer property to mother".
7. Open **Will → Checker** to see PASS/WARNING results.
8. Upload a document under **Documents**.
9. Add a digital account under **Digital Legacy**.
10. Add a person under **Trusted Contact**.
11. Open **Life Verification** — click "Confirm I Am Alive", then try
    "Simulate Missed Verification" to see the VERIFICATION_REQUIRED
    state (nothing is ever auto-released).
12. Add a task under **Inheritance Tasks** and change its status.
13. Logout from the top-right menu.

## Notes on scope

This is an intentionally lean prototype:
- No email sending, no real identity verification, no payment/legal
  integrations — Life Verification is a UI simulation only.
- Passwords are hashed with Werkzeug's `generate_password_hash`, but
  the Flask `SECRET_KEY` in `app.py` is a placeholder — change it
  before any real deployment.
- Single SQLite file, no migrations tooling (`db.create_all()` runs
  on startup).


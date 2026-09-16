"""
seed_demo.py — Step 14

Populates the Digital Legacy Vault database with a demo user and sample
data so the prototype can be shown immediately without manual entry.

Usage:
    python seed_demo.py

Safe to re-run: if the demo user already exists, seeding is skipped.
"""
from app import app
from models import (
    db,
    User,
    Asset,
    Nominee,
    WillInstruction,
    DigitalAccount,
    TrustedContact,
    Task,
)

DEMO_EMAIL = "demo@vault.local"
DEMO_PASSWORD = "demo1234"


def seed():
    with app.app_context():
        db.create_all()

        existing = User.query.filter_by(email=DEMO_EMAIL).first()
        if existing:
            print(f"Demo user already exists ({DEMO_EMAIL}). Skipping seed.")
            print(f"Login with: {DEMO_EMAIL} / {DEMO_PASSWORD}")
            return

        # --- User ---------------------------------------------------
        user = User(full_name="Demo User", email=DEMO_EMAIL)
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        db.session.commit()

        # --- Assets ---------------------------------------------------
        mumbai_property = Asset(
            user_id=user.id,
            name="Mumbai Property",
            category="Real Estate",
            provider="Self-owned",
            reference="Flat No. 402, Andheri West",
            approx_value=8500000,
            description="2BHK apartment.",
        )
        bank_account = Asset(
            user_id=user.id,
            name="Bank Account",
            category="Bank",
            provider="HDFC Bank",
            reference="A/C ****4521",
            approx_value=350000,
            description="Primary savings account.",
        )
        insurance = Asset(
            user_id=user.id,
            name="Insurance",
            category="Insurance",
            provider="LIC",
            reference="Policy No. 998877",
            approx_value=2000000,
            description="Term life insurance policy.",
        )
        vehicle = Asset(
            user_id=user.id,
            name="Vehicle",
            category="Vehicle",
            provider="Self-owned",
            reference="MH-31-AB-1234",
            approx_value=650000,
            description="Family car.",
        )
        # Intentionally left without a nominee or will instruction,
        # so the Will Checker produces a WARNING for it.
        mutual_fund = Asset(
            user_id=user.id,
            name="Mutual Fund",
            category="Investment",
            provider="HDFC Mutual Fund",
            reference="Folio No. 55221100",
            approx_value=420000,
            description="SIP investment portfolio.",
        )
        db.session.add_all([mumbai_property, bank_account, insurance, vehicle, mutual_fund])
        db.session.commit()

        # --- Nominees ---------------------------------------------------
        mother = Nominee(user_id=user.id, name="Mother", relationship_="Mother",
                          email="mother@example.com", phone="9800000001")
        father = Nominee(user_id=user.id, name="Father", relationship_="Father",
                          email="father@example.com", phone="9800000002")
        brother = Nominee(user_id=user.id, name="Brother", relationship_="Brother",
                           email="brother@example.com", phone="9800000003")
        db.session.add_all([mother, father, brother])
        db.session.commit()

        # Assign nominees to assets (mutual_fund intentionally skipped)
        mumbai_property.nominees.append(mother)
        bank_account.nominees.append(brother)
        insurance.nominees.append(father)
        vehicle.nominees.append(mother)
        db.session.commit()

        # --- Will Instructions ---------------------------------------------------
        wi1 = WillInstruction(
            user_id=user.id, asset_id=mumbai_property.id,
            beneficiary_name="Mother", instruction_text="Transfer property to mother",
        )
        wi2 = WillInstruction(
            user_id=user.id, asset_id=bank_account.id,
            beneficiary_name="Brother", instruction_text="Transfer bank balance to brother",
        )
        wi3 = WillInstruction(
            user_id=user.id, asset_id=insurance.id,
            beneficiary_name="Father", instruction_text="Insurance claim to be handled by father",
        )
        # mutual_fund intentionally has no instruction -> Will Checker WARNING
        db.session.add_all([wi1, wi2, wi3])
        db.session.commit()

        # --- Digital Legacy ---------------------------------------------------
        gmail = DigitalAccount(
            user_id=user.id, service="Google", account_identifier="demo@gmail.com",
            action="Preserve", beneficiary="Brother",
            instructions="Keep account active for family photos.",
        )
        facebook = DigitalAccount(
            user_id=user.id, service="Facebook", account_identifier="demo.user",
            action="Memorialize", beneficiary="Mother",
            instructions="Convert to a memorial account.",
        )
        db.session.add_all([gmail, facebook])
        db.session.commit()

        # --- Trusted Contact ---------------------------------------------------
        trusted = TrustedContact(
            user_id=user.id, name="Brother", relationship_="Brother",
            email="brother@example.com", phone="9800000003",
        )
        db.session.add(trusted)
        db.session.commit()

        # --- Inheritance Tasks ---------------------------------------------------
        tasks = [
            Task(user_id=user.id, title="Contact Bank",
                 description="Inform HDFC Bank and initiate the claim process.",
                 status="Pending"),
            Task(user_id=user.id, title="Contact Insurance Company",
                 description="File the LIC insurance claim.",
                 status="Pending"),
            Task(user_id=user.id, title="Check Property Documents",
                 description="Verify Mumbai property title deed and registration.",
                 status="In Progress"),
            Task(user_id=user.id, title="Review Investment",
                 description="Review the mutual fund folio and update nominee.",
                 status="Pending"),
            Task(user_id=user.id, title="Review Digital Accounts",
                 description="Go through Google and Facebook account instructions.",
                 status="Completed"),
        ]
        db.session.add_all(tasks)
        db.session.commit()

        print("Demo data seeded successfully.")
        print(f"Login with: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print('Note: "Mutual Fund" was left without a nominee/will instruction')
        print("on purpose, so the Will Checker will show a WARNING for it.")


if __name__ == "__main__":
    seed()

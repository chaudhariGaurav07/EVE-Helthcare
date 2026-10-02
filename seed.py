"""
Seed script to populate the database with sample diagnostic centres and tests.
Run: python seed.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.models.centre import DiagnosticCentre, DiagnosticTest
from app.security import hash_password

CENTRES_DATA = [
    {
        "name": "Apollo Diagnostics - Koramangala",
        "location": "Bangalore",
        "address": "80 Feet Road, Koramangala 4th Block, Bangalore 560034",
        "tests": [
            {"name": "Complete Blood Count (CBC)", "description": "Measures different components of blood", "price": 450.00},
            {"name": "Lipid Profile", "description": "Checks cholesterol and triglyceride levels", "price": 850.00},
            {"name": "Thyroid Profile (T3, T4, TSH)", "description": "Evaluates thyroid gland function", "price": 1200.00},
            {"name": "HbA1c", "description": "Measures average blood sugar over 3 months", "price": 600.00},
            {"name": "Liver Function Test (LFT)", "description": "Assesses liver health", "price": 750.00},
        ],
    },
    {
        "name": "SRL Diagnostics - Indiranagar",
        "location": "Bangalore",
        "address": "12th Main, HAL 2nd Stage, Indiranagar, Bangalore 560038",
        "tests": [
            {"name": "Complete Blood Count (CBC)", "description": "Measures different components of blood", "price": 400.00},
            {"name": "Vitamin D Test", "description": "Checks vitamin D levels in blood", "price": 1100.00},
            {"name": "Kidney Function Test (KFT)", "description": "Evaluates kidney health and function", "price": 900.00},
            {"name": "Urine Routine Examination", "description": "Physical and chemical analysis of urine", "price": 250.00},
        ],
    },
    {
        "name": "Dr. Lal PathLabs - Connaught Place",
        "location": "New Delhi",
        "address": "N-14, Connaught Circus, New Delhi 110001",
        "tests": [
            {"name": "Complete Blood Count (CBC)", "description": "Measures different components of blood", "price": 500.00},
            {"name": "COVID-19 RT-PCR", "description": "Detects SARS-CoV-2 virus RNA", "price": 800.00},
            {"name": "Iron Studies", "description": "Measures iron, ferritin, and TIBC levels", "price": 1500.00},
            {"name": "ESR (Erythrocyte Sedimentation Rate)", "description": "Non-specific marker of inflammation", "price": 200.00},
            {"name": "Blood Glucose Fasting", "description": "Fasting blood sugar measurement", "price": 150.00},
            {"name": "Lipid Profile", "description": "Checks cholesterol and triglyceride levels", "price": 900.00},
        ],
    },
    {
        "name": "Thyrocare - Andheri",
        "location": "Mumbai",
        "address": "D-37/1, TTC MIDC, Turbhe, Navi Mumbai 400703",
        "tests": [
            {"name": "Aarogyam Full Body Checkup", "description": "Comprehensive 72-parameter health screening", "price": 2500.00},
            {"name": "Thyroid Profile (T3, T4, TSH)", "description": "Evaluates thyroid gland function", "price": 950.00},
            {"name": "Complete Blood Count (CBC)", "description": "Measures different components of blood", "price": 350.00},
            {"name": "Vitamin B12 Test", "description": "Checks vitamin B12 levels in blood", "price": 800.00},
        ],
    },
    {
        "name": "Metropolis Healthcare - Banjara Hills",
        "location": "Hyderabad",
        "address": "Road No. 1, Banjara Hills, Hyderabad 500034",
        "tests": [
            {"name": "Dengue NS1 Antigen", "description": "Early detection of dengue infection", "price": 700.00},
            {"name": "Malaria Antigen Test", "description": "Rapid detection of malaria parasites", "price": 550.00},
            {"name": "Complete Blood Count (CBC)", "description": "Measures different components of blood", "price": 420.00},
            {"name": "CRP (C-Reactive Protein)", "description": "Marker of inflammation and infection", "price": 650.00},
            {"name": "Widal Test", "description": "Serological test for typhoid fever", "price": 300.00},
        ],
    },
]

TEST_USERS = [
    {"email": "patient@example.com", "password": "password123", "full_name": "Gaurav Sharma", "phone": "+919876543210"},
    {"email": "admin@example.com", "password": "password123", "full_name": "Admin User", "phone": "+919876543211"},
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(DiagnosticCentre).count() > 0:
            print("Database already seeded. Skipping.")
            return

        for user_data in TEST_USERS:
            user = User(
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                phone=user_data["phone"],
            )
            db.add(user)
        print(f"Created {len(TEST_USERS)} test users")

        total_tests = 0
        for centre_data in CENTRES_DATA:
            centre = DiagnosticCentre(
                name=centre_data["name"],
                location=centre_data["location"],
                address=centre_data["address"],
            )
            db.add(centre)
            db.flush()

            for test_data in centre_data["tests"]:
                test = DiagnosticTest(
                    name=test_data["name"],
                    description=test_data["description"],
                    price=test_data["price"],
                    centre_id=centre.id,
                )
                db.add(test)
                total_tests += 1

        db.commit()
        print(f"Seeded {len(CENTRES_DATA)} diagnostic centres with {total_tests} tests")
        print("\nTest credentials:")
        print("  Email: patient@example.com")
        print("  Password: password123")

    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

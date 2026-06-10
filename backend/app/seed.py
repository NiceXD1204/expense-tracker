"""Create tables and seed a few sample expenses if the table is empty.

Run as a one-off Helm hook Job (`pre-install,pre-upgrade`) so the app starts
with some demo data: `python -m app.seed`.
"""

from . import models
from .database import Base, SessionLocal, engine

SAMPLE_EXPENSES = [
    {"description": "Groceries", "amount": 54.30, "category": "Food"},
    {"description": "Bus pass", "amount": 25.00, "category": "Transport"},
    {"description": "Electricity bill", "amount": 80.15, "category": "Utilities"},
]


def main() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(models.Expense).count() == 0:
            db.add_all(models.Expense(**row) for row in SAMPLE_EXPENSES)
            db.commit()
            print(f"Seeded {len(SAMPLE_EXPENSES)} sample expenses.")
        else:
            print("Expenses table already has data, skipping seed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

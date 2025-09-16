import csv
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models import Context

CSV_PATH = r"C:\Users\monti\Projects\DashValidator\data\contexts.csv"

def main() -> None:
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set in .env")
    engine = create_engine(db_url, pool_pre_ping=True)

    inserted = 0
    updated = 0
    total = 0

    # Use utf-8-sig to tolerate BOM in header
    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f, Session(engine) as session:
        reader = csv.DictReader(f)
        required = ["key", "value", "description"]
        if [*reader.fieldnames] != required:
            raise ValueError(f"CSV headers must be exactly: {required}; got: {reader.fieldnames}")

        for row in reader:
            total += 1
            k = (row.get("key") or "").strip()
            v = (row.get("value") or "").strip()
            d = row.get("description") or None
            if not k or not v:
                # skip incomplete rows
                continue

            existing = session.query(Context).filter_by(key=k).first()
            if existing:
                changed = False
                if existing.value != v:
                    existing.value = v; changed = True
                if (existing.description or "") != (d or ""):
                    existing.description = d; changed = True
                if changed:
                    updated += 1
            else:
                session.add(Context(key=k, value=v, description=d))
                inserted += 1

        session.commit()

    print(f"Processed: {total} | Inserted: {inserted} | Updated: {updated}")

if __name__ == "__main__":
    main()

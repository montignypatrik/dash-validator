import csv
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models import Establishment

CSV_PATH = r"C:\Users\monti\Projects\DashValidator\data\establishments.csv"

def parse_bool(val: str | None) -> bool:
    if val is None:
        return False
    return str(val).strip().lower() in {"1", "true", "yes", "y"}

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
        required = ["number", "name", "city", "region_code", "is_active"]
        if [*reader.fieldnames] != required:
            raise ValueError(f"CSV headers must be exactly: {required}; got: {reader.fieldnames}")

        for row in reader:
            total += 1
            number = (row.get("number") or "").strip()
            name = (row.get("name") or "").strip()
            city = (row.get("city") or "").strip() or None
            region_code = (row.get("region_code") or "").strip() or None
            is_active = parse_bool(row.get("is_active"))

            if not number or not name:
                # skip incomplete rows
                continue

            existing = session.query(Establishment).filter_by(number=number).first()
            if existing:
                changed = False
                if existing.name != name:
                    existing.name = name; changed = True
                if (existing.city or "") != (city or ""):
                    existing.city = city; changed = True
                if (existing.region_code or "") != (region_code or ""):
                    existing.region_code = region_code; changed = True
                if existing.is_active != is_active:
                    existing.is_active = is_active; changed = True
                if changed:
                    updated += 1
            else:
                session.add(Establishment(
                    number=number,
                    name=name,
                    city=city,
                    region_code=region_code,
                    is_active=is_active
                ))
                inserted += 1

        session.commit()

    print(f"Processed: {total} | Inserted: {inserted} | Updated: {updated}")

if __name__ == "__main__":
    main()

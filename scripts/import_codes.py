import csv
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models import Code

CSV_PATH = r"C:\Users\monti\Projects\DashValidator\data\codes.csv"

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

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f, Session(engine) as session:
        reader = csv.DictReader(f)
        required = {"code", "name", "description", "is_active"}
        if set(reader.fieldnames or []) != required:
            raise ValueError(f"CSV headers must be exactly: {sorted(required)}; got: {reader.fieldnames}")

        for row in reader:
            total += 1
            code_val = (row.get("code") or "").strip()
            name_val = (row.get("name") or "").strip()
            desc_val = row.get("description") or None
            active_val = parse_bool(row.get("is_active"))

            if not code_val or not name_val:
                # Skip incomplete lines
                continue

            existing = session.query(Code).filter_by(code=code_val).first()
            if existing:
                changed = False
                if existing.name != name_val:
                    existing.name = name_val
                    changed = True
                if (existing.description or "") != (desc_val or ""):
                    existing.description = desc_val
                    changed = True
                if existing.is_active != active_val:
                    existing.is_active = active_val
                    changed = True
                if changed:
                    updated += 1
            else:
                session.add(Code(code=code_val, name=name_val, description=desc_val, is_active=active_val))
                inserted += 1

        session.commit()

    print(f"Processed: {total} rows | Inserted: {inserted} | Updated: {updated}")

if __name__ == "__main__":
    main()


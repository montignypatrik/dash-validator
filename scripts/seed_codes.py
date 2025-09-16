import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models import Code
from app.database import Base

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create a new session
with Session(engine) as session:
    # Check if code already exists
    existing = session.query(Code).filter_by(code="19928").first()
    if existing:
        print("Code 19928 already exists:", existing.name)
    else:
        new_code = Code(
            code="19928",
            name="Consultation de base",
            description="Test seed row",
            is_active=True,
        )
        session.add(new_code)
        session.commit()
        print("Inserted new code:", new_code.code, new_code.name)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Code
from app.schemas import CodeOut

router = APIRouter(prefix="/codes", tags=["codes"])

# Dependency: get a session and close it after the request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[CodeOut])
def list_codes(db: Session = Depends(get_db)):
    """Return all codes as JSON."""
    return db.query(Code).all()

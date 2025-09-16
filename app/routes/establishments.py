from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Establishment
from app.schemas import EstablishmentOut

router = APIRouter(prefix="/establishments", tags=["establishments"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[EstablishmentOut])
def list_establishments(db: Session = Depends(get_db)):
    return db.query(Establishment).all()

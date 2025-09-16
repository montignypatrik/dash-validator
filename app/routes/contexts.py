from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Context
from app.schemas import ContextOut

router = APIRouter(prefix="/contexts", tags=["contexts"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[ContextOut])
def list_contexts(db: Session = Depends(get_db)):
    return db.query(Context).all()

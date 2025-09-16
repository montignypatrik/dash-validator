from fastapi import FastAPI
from sqlalchemy import text
from app.database import engine, Base
from app import models

app = FastAPI(title="DashValidator API")

# Create tables at startup (tiny & simple for Milestone B)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/db/health")
def db_health():
    # Simple connection test
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected"}

@app.get("/")
def root():
    return {"message": "API is running"}

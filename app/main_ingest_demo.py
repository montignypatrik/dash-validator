# C:\Users\monti\Projects\DashValidator\app\main_ingest_demo.py
from __future__ import annotations

from fastapi import FastAPI
from app.routers.ingest import router as ingest_router

app = FastAPI(title="DashValidator Ingestion Demo")
app.include_router(ingest_router)

# Simple health to confirm it's running
@app.get("/health")
def health():
    return {"status": "ok"}

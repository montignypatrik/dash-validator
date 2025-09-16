from fastapi import FastAPI, status, Response
from sqlalchemy import text
import time

from app.routes import codes, contexts, establishments
from app.database import SessionLocal  # corrected path

app = FastAPI()

# Register routers
app.include_router(codes.router)
app.include_router(contexts.router)
app.include_router(establishments.router)

@app.get("/")
def root():
    return {"message": "API is running"}

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """
    Extended health check:
    - Confirms app is running
    - Attempts DB connection and reports latency
    """
    started = time.perf_counter()

    db_status = "unknown"
    db_latency_ms = None
    db_error = None

    try:
        session = SessionLocal()
        t0 = time.perf_counter()
        session.execute(text("SELECT 1"))
        session.close()
        db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        db_status = "ok"
    except Exception as exc:
        db_status = "error"
        db_error = str(exc)

    overall = "ok" if db_status == "ok" else "degraded"

    return {
        "status": overall,
        "uptime_check": "ok",
        "db": {
            "status": db_status,
            "latency_ms": db_latency_ms,
            "error": db_error,
        },
        "total_latency_ms": round((time.perf_counter() - started) * 1000, 2),
    }

@app.head("/health", status_code=status.HTTP_200_OK)
def health_head():
    """
    Lightweight health check for load balancers.
    Returns headers only (no JSON body).
    """
    return Response(status_code=status.HTTP_200_OK)

@app.get("/healthz", status_code=status.HTTP_200_OK)
def healthz():
    """
    Alias to /health for compatibility with common monitoring systems.
    """
    return health_check()

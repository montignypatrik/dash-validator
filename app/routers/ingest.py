# C:\Users\monti\Projects\DashValidator\app\routers\ingest.py
from __future__ import annotations

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from typing import List, Dict, Tuple
from io import StringIO
import csv

from app.database import SessionLocal  # your existing session factory
from app.validators import (
    run_all_validations,
    load_required_companion_map,
)

router = APIRouter(tags=["ingestion"])

def _detect_delimiter(sample_text: str) -> Tuple[str, str]:
    """
    Return (delimiter, hint) where delimiter is ',' or ';' and hint is 'comma'/'semicolon'.
    We inspect up to the first 5 non-empty lines.
    """
    lines = [ln for ln in sample_text.splitlines() if ln.strip()]
    lines = lines[:5] if lines else []
    if not lines:
        return (",", "comma")
    semi = sum(ln.count(";") for ln in lines)
    comma = sum(ln.count(",") for ln in lines)
    if semi > comma:
        return (";", "semicolon")
    return (",", "comma")

def _read_csv(upload_text: str, delimiter: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Parse CSV text into (headers, rows).
    - headers: list of column names
    - rows: list of dicts mapping header -> value
    """
    reader = csv.DictReader(StringIO(upload_text), delimiter=delimiter)
    headers = list(reader.fieldnames or [])
    rows: List[Dict[str, str]] = []
    for row in reader:
        # Normalize None to empty string to avoid KeyErrors later
        rows.append({k: (v if v is not None else "") for k, v in row.items()})
    return headers, rows

@router.post("/ingest", summary="Upload CSV and run validations")
async def ingest(file: UploadFile = File(...)) -> JSONResponse:
    try:
        raw = await file.read()
        # Decode and trim BOM if present
        text = raw.decode("utf-8-sig", errors="replace")

        # Detect delimiter
        delimiter, hint = _detect_delimiter(text)

        # Parse CSV
        headers, rows = _read_csv(text, delimiter=delimiter)

        # Prepare required headers list (adjust to your canonical headers)
        required_headers = [
            "#","Facture","ID RAMQ","Date de Service","Début","Fin","Periode",
            "Lieu de pratique","Secteur d'activité","Diagnostic","Code","Unités",
            "Règle","Élément de contexte","Montant Preliminaire","Montant payé",
            "Doctor Info"
        ]

        # Open DB session and load DB-driven rules
        with SessionLocal() as db:
            companion_map = load_required_companion_map(db)

        # Run all validators
        errors = run_all_validations(
            rows=rows,
            headers=headers,
            required_headers=required_headers,
            required_companion_map=companion_map,
            facture_field="Facture",
            doctor_field="Doctor Info",
            code_field="Code",
        )

        payload = {
            "filename": file.filename,
            "delimiter_hint": hint,
            "uploaded_headers": headers,
            "row_count": len(rows),
            "errors": errors,
        }
        return JSONResponse(status_code=200, content=payload)

    except Exception as exc:
        return JSONResponse(
            status_code=400,
            content={
                "filename": getattr(file, "filename", None),
                "error": f"{type(exc).__name__}: {exc}",
            },
        )

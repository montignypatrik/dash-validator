# C:\Users\monti\Projects\DashValidator\app\routers\ingest.py
from __future__ import annotations

import csv
import io
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.services.header_rule import load_required_headers, validate_headers, _get_engine

router = APIRouter(tags=["ingestion"])


def _read_header_row(file_bytes: bytes) -> list[str]:
    """
    Return the parsed header row from the uploaded CSV bytes.
    Auto-detect delimiter with csv.Sniffer; fallback to semicolon, then comma.
    Always decode as UTF-8 with BOM handling.
    """
    text = file_bytes.decode("utf-8-sig", errors="replace")
    sample = text[:4096]

    # Try sniffer first
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        delimiter = dialect.delimiter
    except Exception:
        # Fallback: prefer semicolon, then comma
        delimiter = ";"
        if "," in sample and ";" not in sample:
            delimiter = ","

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        headers = next(reader)
    except StopIteration:
        headers = []

    return [h for h in headers]


@router.post("/ingest", summary="Upload CSV and validate headers only")
async def ingest(file: UploadFile = File(...)) -> JSONResponse:
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file.")

    # 1) Parse header row from CSV
    uploaded_headers = _read_header_row(contents)

    # 2) Load rule from DB
    engine = _get_engine()
    params = load_required_headers(engine)

    # 3) Validate
    is_valid, missing = validate_headers(uploaded_headers, params)

    return JSONResponse(
        status_code=200,
        content={
            "filename": file.filename,
            "delimiter_hint": params.get("delimiter"),
            "uploaded_headers": uploaded_headers,
            "required_headers": params.get("required_headers"),
            "valid": is_valid,
            "missing_headers": missing,
        },
    )

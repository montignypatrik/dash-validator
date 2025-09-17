# C:\Users\monti\Projects\DashValidator\app\routers\metrics.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
import csv
import io

router = APIRouter(prefix="/metrics", tags=["metrics"])

# Exact French headers
HEADER_DATE = "Date de Service"
HEADER_PATIENT = "Patient"

def _norm(s: str) -> str:
    return (s or "").strip().lower()

def _find_header(fieldnames: List[str], target: str) -> Optional[str]:
    mapping = {_norm(name): name for name in (fieldnames or [])}
    return mapping.get(_norm(target))

def _decode_bytes(data: bytes) -> str:
    """
    Try common encodings seen in CSV exports (Excel, regional settings).
    Order matters: UTF-8 with BOM -> UTF-8 -> Latin-1.
    """
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return data.decode(enc)
        except Exception:
            continue
    # Last-resort fallback: ignore undecodable characters
    return data.decode("utf-8", errors="ignore")

def _parse_date_to_yyyy_mm_dd(s: str) -> Optional[str]:
    """
    Accept several common date formats and normalize to YYYY-MM-DD.
    """
    if not s:
        return None
    s = s.strip()
    if not s:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # ISO-like fallback: e.g., 2025-09-14T10:30:00 -> take date part
    if "T" in s:
        try:
            dt = datetime.strptime(s.split("T", 1)[0], "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    return None

@router.post("/unique-patients-by-day")
async def unique_patients_by_day(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload a CSV (multipart/form-data, field 'file') that includes:
      - 'Date de Service' (date)
      - 'Patient' (patient ID; used as the ONLY deduplication key)
    Returns per-day unique patient counts and meta info.
    Supports both comma- and semicolon-separated CSVs.
    """
    try:
        raw = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read upload: {e}")

    text = _decode_bytes(raw)

    # Detect delimiter (explicitly test comma and semicolon). Fallback to ';'
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";"])
        delim = getattr(dialect, "delimiter", ";") or ";"
    except csv.Error:
        delim = ";"

    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV appears to have no header row.")

    date_col = _find_header(reader.fieldnames, HEADER_DATE)
    patient_col = _find_header(reader.fieldnames, HEADER_PATIENT)

    if not date_col:
        raise HTTPException(status_code=400, detail=f"Missing required header: '{HEADER_DATE}'")
    if not patient_col:
        raise HTTPException(status_code=400, detail=f"Missing required header: '{HEADER_PATIENT}'")

    totals: Dict[str, set] = {}
    rows_total = 0
    rows_used = 0
    rows_skipped = 0
    warnings: List[str] = []

    for row in reader:
        rows_total += 1

        date_raw = (row.get(date_col) or "").strip()
        patient_raw = (row.get(patient_col) or "").strip()

        date_norm = _parse_date_to_yyyy_mm_dd(date_raw)
        patient_key = patient_raw  # Patient-only dedup key (as requested)

        if not date_norm or not patient_key:
            rows_skipped += 1
            continue

        if date_norm not in totals:
            totals[date_norm] = set()
        totals[date_norm].add(patient_key)
        rows_used += 1

    results = [
        {"date": d, "unique_patients": len(pids)}
        for d, pids in sorted(totals.items(), key=lambda x: x[0])
    ]

    if rows_skipped > 0:
        warnings.append(f"{rows_skipped} row(s) skipped due to missing/invalid date or Patient.")

    # Small hint if we had to fall back to ';'
    if delim == ";" and ";" not in sample and "," in sample:
        warnings.append("Delimiter detection fell back to ';'. Check source file formatting if results look off.")

    return {
        "results": results,
        "meta": {
            "rows_total": rows_total,
            "rows_used": rows_used,
            "rows_skipped": rows_skipped,
            "delimiter": delim,
            "warnings": warnings,
        },
    }

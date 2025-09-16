# C:\Users\monti\Projects\DashValidator\app\routers\metrics.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
import csv
import io

router = APIRouter(prefix="/metrics", tags=["metrics"])

# Expected French headers (case/space/accents-insensitive matching)
EXPECTED_DATE = "Date de Service"
EXPECTED_ID = "ID RAMQ"
EXPECTED_PATIENT = "Patient"

def _norm(s: str) -> str:
    # Lowercase + strip; keep accents because your headers are consistent
    return (s or "").strip().lower()

def _find_header(fieldnames: List[str], target: str) -> Optional[str]:
    target_norm = _norm(target)
    mapping = {_norm(name): name for name in fieldnames}
    return mapping.get(target_norm)

def _parse_date(s: str) -> Optional[str]:
    """
    Accept common formats and normalize to YYYY-MM-DD string.
    Returns None if unparseable.
    """
    if not s:
        return None
    s = s.strip()
    if not s:
        return None

    candidates = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
    ]
    for fmt in candidates:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # Last resort: try very permissive parsing by reordering day-first patterns
    # without adding external deps.
    try:
        # Handle like '2025-09-14T10:30:00' by slicing date part if present
        if "T" in s:
            s = s.split("T", 1)[0]
            dt = datetime.strptime(s, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    # Could not parse
    return None

def _decode_bytes(data: bytes) -> str:
    # Try utf-8-sig -> utf-8 -> latin-1
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return data.decode(enc)
        except Exception:
            continue
    # Fallback
    return data.decode("utf-8", errors="ignore")

@router.post("/unique-patients-by-day")
async def unique_patients_by_day(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload a CSV (multipart/form-data, field name 'file') with French headers:
      - 'Date de Service' (date)
      - 'ID RAMQ' (patient unique id), fallback to 'Patient' if blank
    Returns per-day unique patient counts with a small meta summary.
    """
    try:
        raw = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read upload: {e}")

    text = _decode_bytes(raw)

    # Sniff delimiter (default to comma)
    try:
        sample = text[:2048]
        dialect = csv.Sniffer().sniff(sample)
        delim = dialect.delimiter
    except Exception:
        delim = ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV appears to have no header row.")

    # Map headers
    date_col = _find_header(reader.fieldnames, EXPECTED_DATE)
    id_col = _find_header(reader.fieldnames, EXPECTED_ID)
    patient_col = _find_header(reader.fieldnames, EXPECTED_PATIENT)

    if not date_col:
        raise HTTPException(status_code=400, detail=f"Missing required header: '{EXPECTED_DATE}'")
    if not (id_col or patient_col):
        raise HTTPException(status_code=400, detail=f"Missing patient headers: need '{EXPECTED_ID}' or '{EXPECTED_PATIENT}'")

    # Aggregate
    date_to_patients: Dict[str, set] = {}
    total_rows = 0
    used_rows = 0
    skipped_rows = 0
    warnings: List[str] = []

    for row in reader:
        total_rows += 1
        date_raw = (row.get(date_col) or "").strip()
        date_norm = _parse_date(date_raw)
        # choose patient key: ID RAMQ else Patient
        pid = (row.get(id_col) or "").strip() if id_col else ""
        if not pid:
            pid = (row.get(patient_col) or "").strip() if patient_col else ""

        if not date_norm or not pid:
            skipped_rows += 1
            continue

        used_rows += 1
        if date_norm not in date_to_patients:
            date_to_patients[date_norm] = set()
        date_to_patients[date_norm].add(pid)

    # Build results
    results = [
        {"date": d, "unique_patients": len(pids)}
        for d, pids in sorted(date_to_patients.items(), key=lambda x: x[0])
    ]

    if skipped_rows > 0:
        warnings.append(f"{skipped_rows} row(s) skipped due to missing/invalid date or patient identifier.")

    return {
        "results": results,
        "meta": {
            "rows_total": total_rows,
            "rows_used": used_rows,
            "rows_skipped": skipped_rows,
            "delimiter": delim,
            "warnings": warnings,
        },
    }

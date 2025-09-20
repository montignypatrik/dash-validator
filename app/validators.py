from __future__ import annotations

"""
Centralized validators for CSV ingestion.

Contains:
1) Required headers validation
2) Required companion codes validation (DB-backed via table: required_companion_codes)

Usage pattern from your ingest flow (example):

    from sqlalchemy.orm import Session
    from app.validators import run_all_validations, load_required_companion_map

    # rows: List[Dict[str, str]] parsed from CSV (semicolon or comma delimited)
    # headers: List[str] parsed from CSV header row

    with SessionLocal() as db:
        companion_map = load_required_companion_map(db)
        errors = run_all_validations(
            rows=rows,
            headers=headers,
            required_headers=[
                "#","Facture","ID RAMQ","Date de Service","Début","Fin","Periode",
                "Lieu de pratique","Secteur d'activité","Diagnostic","Code","Unités",
                "Règle","Élément de contexte","Montant Preliminaire","Montant payé",
                "Doctor Info"
            ],
            required_companion_map=companion_map,
            facture_field="Facture",
            doctor_field="Doctor Info",
            code_field="Code",
        )

Return format: List[Dict[str, str]] of validation errors.
"""

from typing import Dict, Iterable, List, Sequence, Set, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import Table, Column, Integer, String, Boolean, Text, DateTime, MetaData

# --- DB reflection for required_companion_codes (no need to touch your models) ---
metadata = MetaData()
required_companion_codes = Table(
    "required_companion_codes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("code", String(10), nullable=False),
    Column("requires_code", String(10), nullable=False),
    Column("active", Boolean, nullable=False),
    Column("note", Text),
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
)

# --------------------------
# Rule 1: Required Headers
# --------------------------
def validate_required_headers(
    headers: Sequence[str],
    required_headers: Sequence[str],
) -> List[Dict[str, str]]:
    """
    Ensure all required headers are present (case-sensitive exact match).
    """
    present = set(headers or [])
    missing = [h for h in required_headers if h not in present]
    if not missing:
        return []
    return [{
        "rule": "required_headers",
        "message": f"Missing required header(s): {', '.join(missing)}",
        "missing": ", ".join(missing),
    }]

# ------------------------------------------
# Rule 2: Required Companion Codes (DB-backed)
# ------------------------------------------
def load_required_companion_map(db: Session) -> Dict[str, Set[str]]:
    """
    Loads active required-companion rules from DB.
    Returns a map like: {'15802': {'19957', ...}, ...}
    """
    rows = db.execute(
        required_companion_codes.select().where(required_companion_codes.c.active == True)
    ).fetchall()
    m: Dict[str, Set[str]] = defaultdict(set)
    for r in rows:
        # SQLAlchemy Row supports attribute-style or key access depending on version
        code = getattr(r, "code", r[1])
        req  = getattr(r, "requires_code", r[2])
        m[code].add(req)
    return m

def validate_required_companions(
    rows: Iterable[Dict[str, str]],
    required_map: Dict[str, Set[str]],
    facture_field: str = "Facture",
    doctor_field: str = "Doctor Info",
    code_field: str = "Code",
) -> List[Dict[str, str]]:
    """
    For each invoice (Facture)+doctor, if a code is present but its required companions are not,
    report a validation error.
    """
    errors: List[Dict[str, str]] = []
    if not required_map:
        return errors

    # Group rows by (invoice, doctor)
    by_invoice_doctor: Dict[Tuple[str, str], List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_invoice_doctor[(row.get(facture_field, ""), row.get(doctor_field, ""))].append(row)

    for (facture, doctor), group in by_invoice_doctor.items():
        codes_here = {r.get(code_field, "") for r in group if r.get(code_field)}
        for code in list(codes_here):
            if code in required_map:
                must_have = required_map[code]
                missing = sorted([c for c in must_have if c not in codes_here])
                if missing:
                    errors.append({
                        "rule": "required_companion_code",
                        "message": f"Code {code} requires: {', '.join(missing)} on the same invoice/doctor.",
                        "facture": facture,
                        "doctor": doctor,
                        "codes_present": ", ".join(sorted(codes_here)),
                    })
    return errors

# --------------------------
# Orchestrator
# --------------------------
def run_all_validations(
    rows: Iterable[Dict[str, str]],
    headers: Sequence[str],
    required_headers: Sequence[str],
    required_companion_map: Dict[str, Set[str]],
    facture_field: str = "Facture",
    doctor_field: str = "Doctor Info",
    code_field: str = "Code",
) -> List[Dict[str, str]]:
    """
    Run all validations and return a combined list of errors.
    """
    all_errors: List[Dict[str, str]] = []

    # 1) Required headers
    all_errors.extend(validate_required_headers(headers=headers, required_headers=required_headers))

    # 2) Required companion codes
    all_errors.extend(
        validate_required_companions(
            rows=rows,
            required_map=required_companion_map,
            facture_field=facture_field,
            doctor_field=doctor_field,
            code_field=code_field,
        )
    )

    return all_errors

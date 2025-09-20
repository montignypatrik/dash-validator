# C:\Users\monti\Projects\DashValidator\app\services\header_rule.py
from __future__ import annotations

import json
import os
from typing import List, Dict, Any, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def _get_engine() -> Engine:
    """
    Create an Engine from DATABASE_URL if present, else default to local SQLite app.db.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Default to local SQLite in project root
        db_url = "sqlite:///app.db"
    return create_engine(db_url, pool_pre_ping=True)


def load_required_headers(engine: Engine | None = None) -> Dict[str, Any]:
    """
    Load 'required_headers' rule from the rules table.
    Returns a dict with keys:
      - required_headers: List[str]
      - delimiter: str
      - ignore_extras: bool
      - case_insensitive: bool
      - trim_whitespace: bool
    Raises RuntimeError if rule not found or malformed.
    """
    engine = engine or _get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT params FROM rules WHERE name = :n"),
            {"n": "required_headers"},
        ).fetchone()

    if not row:
        raise RuntimeError("Required Headers rule not found in DB (name='required_headers').")

    params_text = row[0]
    try:
        params = json.loads(params_text)
    except Exception as e:
        raise RuntimeError(f"Rule params JSON is invalid: {e}")

    for key in ["required_headers", "delimiter", "ignore_extras", "case_insensitive", "trim_whitespace"]:
        if key not in params:
            raise RuntimeError(f"Rule params missing key: {key}")

    if not isinstance(params["required_headers"], list) or not params["required_headers"]:
        raise RuntimeError("Rule params 'required_headers' must be a non-empty list.")

    return params


def _normalize(header: str, case_insensitive: bool, trim_whitespace: bool) -> str:
    h = header.replace("\ufeff", "")  # remove BOM if present
    if trim_whitespace:
        h = h.strip()
    if case_insensitive:
        h = h.casefold()
    # Some CSV exports can introduce non-breaking spaces; normalize them.
    h = h.replace("\xa0", " ").strip()
    return h


def validate_headers(
    uploaded_headers: List[str],
    rule_params: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """
    Compare uploaded headers to rule's required headers.
    Returns (is_valid, missing_headers_list).
      - is_valid: True if all required headers are present (extras allowed)
      - missing_headers_list: list of required headers not found (ORIGINAL casing from rule)
    """
    case_ins = bool(rule_params.get("case_insensitive", True))
    trim_ws = bool(rule_params.get("trim_whitespace", True))

    # Build normalized forms
    req_original = list(rule_params["required_headers"])
    req_norm = [_normalize(h, case_ins, trim_ws) for h in req_original]
    got_norm = {_normalize(h, case_ins, trim_ws) for h in uploaded_headers}

    # Map normalized -> original for pretty error output
    norm_to_original = {}
    for orig, norm in zip(req_original, req_norm):
        # First occurrence wins; preserves list order and avoids overwriting duplicates
        norm_to_original.setdefault(norm, orig)

    missing_norm = [h for h in req_norm if h not in got_norm]
    missing_pretty = [norm_to_original[h] for h in missing_norm]

    return (len(missing_norm) == 0, missing_pretty)

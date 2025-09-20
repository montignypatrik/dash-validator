"""seed: Required Headers rule

Revision ID: 54443d2e77a9
Revises: dc141d350053
Create Date: 2025-09-20 12:12:29.345537

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import json

# revision identifiers, used by Alembic.
revision: str = '54443d2e77a9'
down_revision: Union[str, Sequence[str], None] = 'dc141d350053'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_columns_sqlite(conn, table):
    rows = conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
    # rows: cid, name, type, notnull (0/1), dflt_value, pk
    return {r[1]: {"type": r[2], "notnull": bool(r[3]), "default": r[4]} for r in rows}


def _table_columns_generic(conn, table):
    insp = sa.inspect(conn)
    cols = {}
    for c in insp.get_columns(table):
        cols[c["name"]] = {
            "type": str(c.get("type")),
            "notnull": not c.get("nullable", True),
            "default": c.get("default"),
        }
    return cols


def _ensure_params_column(conn):
    """Add params column if missing (SQLite-safe)."""
    dialect = conn.dialect.name
    if dialect == "sqlite":
        cols = _table_columns_sqlite(conn, "rules")
        if "params" not in cols:
            op.add_column("rules", sa.Column("params", sa.Text(), nullable=True))
    else:
        cols = _table_columns_generic(conn, "rules")
        if "params" not in cols:
            op.add_column("rules", sa.Column("params", sa.Text(), nullable=True))


def upgrade() -> None:
    """Insert or update Required Headers rule."""
    conn = op.get_bind()
    _ensure_params_column(conn)

    # Full header list, semicolon separated, with accents fixed
    required_headers_semicolon = (
        "#;Facture;ID RAMQ;Date de Service;Début;Fin;Periode;Lieu de pratique;"
        "Secteur d'activité;Diagnostic;Code;Unités;Règle;Élément de contexte;"
        "Montant Preliminaire;Montant payé;Doctor Info;"
        "DEV NOTE - TRADUIRE: Report_DailyClaimInfo_TotalPrelAmount;"
        "DEV NOTE - TRADUIRE: Report_DailyClaimInfo_TotalFinalAmount;"
        "DEV NOTE - TRADUIRE: Report_DailyClaimInfo_TotalCount;"
        "Agence;Patient;Grand Total"
    )
    required_headers = [h.strip() for h in required_headers_semicolon.split(";")]

    rule_code = "REQUIRED_HEADERS"
    rule_name = "required_headers"
    rule_desc = "Validates that all mandatory CSV headers are present (extras allowed)."
    rule_category = "input_format"
    rule_severity = "error"
    params = {
        "required_headers": required_headers,
        "delimiter": ";",
        "ignore_extras": True,
        "case_insensitive": True,
        "trim_whitespace": True,
    }

    dialect = conn.dialect.name
    cols = (_table_columns_sqlite(conn, "rules")
            if dialect == "sqlite"
            else _table_columns_generic(conn, "rules"))

    need_created_at = ("created_at" in cols and cols["created_at"]["notnull"])
    need_updated_at = ("updated_at" in cols and cols["updated_at"]["notnull"])

    # Existence check by name
    exists = conn.execute(
        sa.text("SELECT 1 FROM rules WHERE name = :n"),
        {"n": rule_name}
    ).scalar()

    if dialect == "sqlite":
        # Build INSERT column/value lists dynamically
        insert_cols = ["code", "name", "description", "category", "severity", "is_active", "params"]
        insert_vals = [":code", ":n", ":d", ":c", ":sev", "1", ":p"]

        if need_created_at:
            insert_cols.append("created_at")
            insert_vals.append("CURRENT_TIMESTAMP")
        if need_updated_at:
            insert_cols.append("updated_at")
            insert_vals.append("CURRENT_TIMESTAMP")

        insert_sql = f"""
            INSERT INTO rules ({", ".join(insert_cols)})
            VALUES ({", ".join(insert_vals)})
        """

        if exists:
            set_parts = [
                "description = :d",
                "category    = :c",
                "severity    = :sev",
                "is_active   = 1",
                "params      = :p",
            ]
            if need_updated_at:
                set_parts.append("updated_at = CURRENT_TIMESTAMP")
            update_sql = f"""
                UPDATE rules
                   SET {", ".join(set_parts)}
                 WHERE name = :n
            """
            conn.execute(
                sa.text(update_sql),
                {"d": rule_desc, "c": rule_category, "sev": rule_severity,
                 "p": json.dumps(params, ensure_ascii=False), "n": rule_name},
            )
        else:
            conn.execute(
                sa.text(insert_sql),
                {"code": rule_code, "n": rule_name, "d": rule_desc, "c": rule_category,
                 "sev": rule_severity, "p": json.dumps(params, ensure_ascii=False)},
            )

    else:
        # Postgres/other: use now() if timestamps are required
        insert_cols = ["code", "name", "description", "category", "severity", "is_active", "params"]
        insert_vals = [":code", ":n", ":d", ":c", ":sev", "TRUE", ":p"]
        if need_created_at:
            insert_cols.append("created_at"); insert_vals.append("now()")
        if need_updated_at:
            insert_cols.append("updated_at"); insert_vals.append("now()")
        insert_sql = f"""
            INSERT INTO rules ({", ".join(insert_cols)})
            VALUES ({", ".join(insert_vals)})
        """

        if exists:
            set_parts = [
                "description = :d",
                "category    = :c",
                "severity    = :sev",
                "is_active   = TRUE",
                "params      = :p",
            ]
            if need_updated_at:
                set_parts.append("updated_at = now()")
            update_sql = f"""
                UPDATE rules
                   SET {", ".join(set_parts)}
                 WHERE name = :n
            """
            conn.execute(
                sa.text(update_sql),
                {"d": rule_desc, "c": rule_category, "sev": rule_severity,
                 "p": json.dumps(params, ensure_ascii=False), "n": rule_name},
            )
        else:
            conn.execute(
                sa.text(insert_sql),
                {"code": rule_code, "n": rule_name, "d": rule_desc, "c": rule_category,
                 "sev": rule_severity, "p": json.dumps(params, ensure_ascii=False)},
            )


def downgrade() -> None:
    """Remove Required Headers rule."""
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM rules WHERE name = :n"),
        {"n": "required_headers"}
    )

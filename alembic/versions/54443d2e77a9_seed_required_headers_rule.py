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


def _ensure_params_column(conn):
    """Add params column if missing (SQLite-safe)."""
    dialect = conn.dialect.name
    if dialect == "sqlite":
        cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(rules)").fetchall()]
        if "params" not in cols:
            op.add_column("rules", sa.Column("params", sa.Text(), nullable=True))
    else:
        insp = sa.inspect(conn)
        has_params = any(c["name"] == "params" for c in insp.get_columns("rules"))
        if not has_params:
            op.add_column("rules", sa.Column("params", sa.Text(), nullable=True))


def upgrade() -> None:
    """Insert or update Required Headers rule."""
    conn = op.get_bind()
    _ensure_params_column(conn)

    # Full header list, semicolon separated, with accents fixed
    required_headers_semicolon = (
        "#;Facture;ID RAMQ;Date de Service;Début;Fin;Periode;Lieu de pratique;"
        "Secteur d'activité;Diagnostic;Code;Unités;Règle;Élément de contexte;"
        'Montant Preliminaire;Montant payé;Doctor Info;'
        'DEV NOTE - TRADUIRE: Report_DailyClaimInfo_TotalPrelAmount;'
        'DEV NOTE - TRADUIRE: Report_DailyClaimInfo_TotalFinalAmount;'
        'DEV NOTE - TRADUIRE: Report_DailyClaimInfo_TotalCount;'
        "Agence;Patient;Grand Total"
    )

    required_headers = [h.strip() for h in required_headers_semicolon.split(";")]

    rule_code = "REQUIRED_HEADERS"
    rule_name = "required_headers"
    rule_desc = "Validates that all mandatory CSV headers are present (extras allowed)."
    rule_category = "input_format"
    rule_severity = "error"  # satisfy NOT NULL rules.severity
    params = {
        "required_headers": required_headers,
        "delimiter": ";",
        "ignore_extras": True,
        "case_insensitive": True,
        "trim_whitespace": True,
    }

    dialect = conn.dialect.name

    exists = conn.execute(
        sa.text("SELECT 1 FROM rules WHERE name = :n"),
        {"n": rule_name}
    ).scalar()

    if dialect == "sqlite":
        if exists:
            conn.execute(
                sa.text("""
                    UPDATE rules
                       SET description = :d,
                           category    = :c,
                           severity    = :sev,
                           is_active   = 1,
                           params      = :p
                     WHERE name        = :n
                """),
                {"d": rule_desc, "c": rule_category, "sev": rule_severity,
                 "p": json.dumps(params, ensure_ascii=False), "n": rule_name},
            )
        else:
            conn.execute(
                sa.text("""
                    INSERT INTO rules (code, name, description, category, severity, is_active, params)
                    VALUES (:code, :n, :d, :c, :sev, 1, :p)
                """),
                {"code": rule_code, "n": rule_name, "d": rule_desc, "c": rule_category,
                 "sev": rule_severity, "p": json.dumps(params, ensure_ascii=False)},
            )
    else:
        if exists:
            conn.execute(
                sa.text("""
                    UPDATE rules
                       SET description = :d,
                           category    = :c,
                           severity    = :sev,
                           is_active   = TRUE,
                           params      = :p
                     WHERE name        = :n
                """),
                {"d": rule_desc, "c": rule_category, "sev": rule_severity,
                 "p": json.dumps(params, ensure_ascii=False), "n": rule_name},
            )
        else:
            conn.execute(
                sa.text("""
                    INSERT INTO rules (code, name, description, category, severity, is_active, params)
                    VALUES (:code, :n, :d, :c, :sev, TRUE, :p)
                """),
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

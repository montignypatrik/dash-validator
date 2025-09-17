"""create rules table

Revision ID: dc141d350053
Revises: 880c1c5631c8
Create Date: 2025-09-16 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
import datetime
import json

# revision identifiers, used by Alembic.
revision = "dc141d350053"
down_revision = "880c1c5631c8"
branch_labels = None
depends_on = None


def upgrade():
    # 1) Create rules table
    op.create_table(
        "rules",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String, unique=True, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.String, nullable=False),   # e.g. format | logic
        sa.Column("severity", sa.String, nullable=False),   # error | warning | info
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("config_json", sa.Text),                  # JSON string with rule params
        sa.Column("created_at", sa.String, nullable=False),
        sa.Column("updated_at", sa.String, nullable=False),
    )

    # 2) Insert initial rule
    conn = op.get_bind()
    now = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    config = {"allowed_delimiters": [","]}
    conn.execute(
        sa.text(
            """
            INSERT INTO rules (code, name, description, category, severity, is_active, config_json, created_at, updated_at)
            VALUES (:code, :name, :description, :category, :severity, :is_active, :config_json, :created_at, :updated_at)
            ON CONFLICT(code) DO UPDATE SET
              name=excluded.name,
              description=excluded.description,
              category=excluded.category,
              severity=excluded.severity,
              is_active=excluded.is_active,
              config_json=excluded.config_json,
              updated_at=excluded.updated_at
            """
        ),
        {
            "code": "delimiter_must_be_comma",
            "name": "Delimiter must be a comma",
            "description": "Validates that uploaded CSV files use a comma (,) as the field delimiter.",
            "category": "format",
            "severity": "error",
            "is_active": True,
            "config_json": json.dumps(config, ensure_ascii=False),
            "created_at": now,
            "updated_at": now,
        },
    )


def downgrade():
    # SQLite-safe drop (no error if table doesn't exist)
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS rules"))


"""seed: Required Headers rule (no-op locally if 'rules' table missing)"""

from alembic import op

# Keep the original revision ids intact if they are present in the file you’re replacing.
revision = '54443d2e77a9'
down_revision = 'dc141d350053'
branch_labels = None
depends_on = None

def upgrade():
    # No-op: skip seeding locally because 'rules' table is not present.
    pass

def downgrade():
    # No-op
    pass

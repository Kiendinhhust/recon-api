"""merge users and subdomains

Revision ID: 463e4020f2cb
Revises: 002_optimize_subdomains
Create Date: 2025-11-26 08:33:53.116596

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '463e4020f2cb'
down_revision = '002_optimize_subdomains'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

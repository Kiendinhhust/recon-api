"""increase url column lengths to handle long OAuth/SSO URLs

Revision ID: 003_increase_url_lengths
Revises: 463e4020f2cb
Create Date: 2025-11-26 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_increase_url_lengths'
down_revision = '463e4020f2cb'
branch_labels = None
depends_on = None


def upgrade():
    """
    Increase URL column lengths to handle long OAuth/SSO URLs.
    
    Changes:
    - url: VARCHAR(512) → TEXT
    - final_url: VARCHAR(512) → TEXT
    - title: VARCHAR(512) → VARCHAR(1024)
    
    Reason: OAuth/SSO URLs with challenge parameters can exceed 2000 characters.
    Example: https://accounts-stag.fpt.vn/sso/Auth/Identifier?challenge=... (2359 chars)
    """
    
    # Change url from VARCHAR(512) to TEXT
    op.alter_column('subdomains', 'url',
                    existing_type=sa.String(length=512),
                    type_=sa.Text(),
                    existing_nullable=True)
    
    # Change final_url from VARCHAR(512) to TEXT
    op.alter_column('subdomains', 'final_url',
                    existing_type=sa.String(length=512),
                    type_=sa.Text(),
                    existing_nullable=True)
    
    # Change title from VARCHAR(512) to VARCHAR(1024)
    # Keep VARCHAR for title since HTML titles are usually < 1024 chars
    op.alter_column('subdomains', 'title',
                    existing_type=sa.String(length=512),
                    type_=sa.String(length=1024),
                    existing_nullable=True)


def downgrade():
    """
    Revert URL column lengths back to original sizes.
    
    WARNING: This will TRUNCATE data if URLs are longer than 512 characters!
    """
    
    # Revert title from VARCHAR(1024) to VARCHAR(512)
    op.alter_column('subdomains', 'title',
                    existing_type=sa.String(length=1024),
                    type_=sa.String(length=512),
                    existing_nullable=True)
    
    # Revert final_url from TEXT to VARCHAR(512)
    op.alter_column('subdomains', 'final_url',
                    existing_type=sa.Text(),
                    type_=sa.String(length=512),
                    existing_nullable=True)
    
    # Revert url from TEXT to VARCHAR(512)
    op.alter_column('subdomains', 'url',
                    existing_type=sa.Text(),
                    type_=sa.String(length=512),
                    existing_nullable=True)


"""optimize subdomains schema with httpx fields

Revision ID: 002_optimize_subdomains
Revises: add_users_table
Create Date: 2025-11-25 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_optimize_subdomains'
down_revision = 'add_users_table'
branch_labels = None
depends_on = None


def upgrade():
    """Add new httpx fields to subdomains table and create technologies table"""
    
    # Add new columns to subdomains table
    op.add_column('subdomains', sa.Column('url', sa.String(length=512), nullable=True))
    op.add_column('subdomains', sa.Column('title', sa.String(length=512), nullable=True))
    op.add_column('subdomains', sa.Column('content_length', sa.Integer(), nullable=True))
    op.add_column('subdomains', sa.Column('webserver', sa.String(length=128), nullable=True))
    op.add_column('subdomains', sa.Column('final_url', sa.String(length=512), nullable=True))
    op.add_column('subdomains', sa.Column('cdn_name', sa.String(length=128), nullable=True))
    op.add_column('subdomains', sa.Column('content_type', sa.String(length=128), nullable=True))
    op.add_column('subdomains', sa.Column('host', sa.String(length=64), nullable=True))
    op.add_column('subdomains', sa.Column('chain_status_codes', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('subdomains', sa.Column('ipv4_addresses', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('subdomains', sa.Column('ipv6_addresses', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Modify existing columns
    # Change response_time from Integer to String to store httpx format (e.g., "11.4100539s")
    op.alter_column('subdomains', 'response_time',
                    existing_type=sa.Integer(),
                    type_=sa.String(length=32),
                    existing_nullable=True)
    
    # Change subdomain column to have length limit
    op.alter_column('subdomains', 'subdomain',
                    existing_type=sa.String(),
                    type_=sa.String(length=255),
                    existing_nullable=False)
    
    # Change discovered_by column to have length limit
    op.alter_column('subdomains', 'discovered_by',
                    existing_type=sa.String(),
                    type_=sa.String(length=64),
                    existing_nullable=True)
    
    # Add indexes for new columns
    op.create_index('ix_subdomains_scan_job_id', 'subdomains', ['scan_job_id'], unique=False)
    op.create_index('ix_subdomains_subdomain', 'subdomains', ['subdomain'], unique=False)
    op.create_index('ix_subdomains_is_live', 'subdomains', ['is_live'], unique=False)
    op.create_index('ix_subdomains_http_status', 'subdomains', ['http_status'], unique=False)
    op.create_index('ix_subdomains_created_at', 'subdomains', ['created_at'], unique=False)
    
    # Create technologies table
    op.create_table(
        'technologies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subdomain_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['subdomain_id'], ['subdomains.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for technologies table
    op.create_index('ix_technologies_id', 'technologies', ['id'], unique=False)
    op.create_index('ix_technologies_subdomain_id', 'technologies', ['subdomain_id'], unique=False)
    op.create_index('ix_technologies_name', 'technologies', ['name'], unique=False)
    op.create_index('idx_tech_subdomain', 'technologies', ['subdomain_id', 'name'], unique=True)


def downgrade():
    """Remove httpx fields from subdomains table and drop technologies table"""
    
    # Drop technologies table
    op.drop_index('idx_tech_subdomain', table_name='technologies')
    op.drop_index('ix_technologies_name', table_name='technologies')
    op.drop_index('ix_technologies_subdomain_id', table_name='technologies')
    op.drop_index('ix_technologies_id', table_name='technologies')
    op.drop_table('technologies')
    
    # Drop indexes from subdomains table
    op.drop_index('ix_subdomains_created_at', table_name='subdomains')
    op.drop_index('ix_subdomains_http_status', table_name='subdomains')
    op.drop_index('ix_subdomains_is_live', table_name='subdomains')
    op.drop_index('ix_subdomains_subdomain', table_name='subdomains')
    op.drop_index('ix_subdomains_scan_job_id', table_name='subdomains')
    
    # Revert column changes
    op.alter_column('subdomains', 'discovered_by',
                    existing_type=sa.String(length=64),
                    type_=sa.String(),
                    existing_nullable=True)
    
    op.alter_column('subdomains', 'subdomain',
                    existing_type=sa.String(length=255),
                    type_=sa.String(),
                    existing_nullable=False)
    
    op.alter_column('subdomains', 'response_time',
                    existing_type=sa.String(length=32),
                    type_=sa.Integer(),
                    existing_nullable=True)
    
    # Drop new columns
    op.drop_column('subdomains', 'ipv6_addresses')
    op.drop_column('subdomains', 'ipv4_addresses')
    op.drop_column('subdomains', 'chain_status_codes')
    op.drop_column('subdomains', 'host')
    op.drop_column('subdomains', 'content_type')
    op.drop_column('subdomains', 'cdn_name')
    op.drop_column('subdomains', 'final_url')
    op.drop_column('subdomains', 'webserver')
    op.drop_column('subdomains', 'content_length')
    op.drop_column('subdomains', 'title')
    op.drop_column('subdomains', 'url')


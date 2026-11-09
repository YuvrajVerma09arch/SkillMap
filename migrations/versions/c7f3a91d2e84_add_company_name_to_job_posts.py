"""empty message

Revision ID: c7f3a91d2e84
Revises: 622cc6c11f2d
Create Date: 2026-10-26 18:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'c7f3a91d2e84'
down_revision = '622cc6c11f2d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('job_posts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('company_name', sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table('job_posts', schema=None) as batch_op:
        batch_op.drop_column('company_name')

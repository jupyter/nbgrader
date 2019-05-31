"""adds lms_user_id column to student table

Revision ID: 282d30a0218e
Revises: 724cde206c17
Create Date: 2018-10-25 20:14:56.887686

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '282d30a0218e'
down_revision = '167914646830'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('student', sa.Column('lms_user_id', sa.String(128), nullable=True))


def downgrade():
    op.drop_column('student', 'lms_user_id')

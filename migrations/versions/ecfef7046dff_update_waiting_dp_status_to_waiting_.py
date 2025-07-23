"""Update waiting_dp status to waiting_payment in existing orders

Revision ID: ecfef7046dff
Revises: 8db7b12f7661
Create Date: 2025-07-23 06:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ecfef7046dff'
down_revision = '8db7b12f7661'
branch_labels = None
depends_on = None


def upgrade():
    # Perbarui nilai 'waiting_dp' menjadi 'waiting_payment' di kolom status
    op.execute("UPDATE \"order\" SET status = 'waiting_payment' WHERE status = 'waiting_dp'")


def downgrade():
    # Kembalikan nilai 'waiting_payment' menjadi 'waiting_dp' di kolom status
    op.execute("UPDATE \"order\" SET status = 'waiting_dp' WHERE status = 'waiting_payment'")
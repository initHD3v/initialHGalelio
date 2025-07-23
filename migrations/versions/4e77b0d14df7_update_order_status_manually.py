"""update_order_status_manually

Revision ID: 4e77b0d14df7
Revises: ecfef7046dff
Create Date: 2025-07-23 07:39:18.542428

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e77b0d14df7'
down_revision = 'ecfef7046dff'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE \"order\" SET status = 'waiting_payment' WHERE status = 'waiting_dp'")


def downgrade():
    op.execute("UPDATE \"order\" SET status = 'waiting_dp' WHERE status = 'waiting_payment'")

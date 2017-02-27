"""empty message

Revision ID: 3efbb5e3cc73
Revises: 32b1f65ae6a0
Create Date: 2017-02-15 08:45:52.744584

"""

# revision identifiers, used by Alembic.
revision = '3efbb5e3cc73'
down_revision = '32b1f65ae6a0'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('year_feedback', sa.Column('contractors_used', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('year_feedback', 'contractors_used')
    # ### end Alembic commands ###
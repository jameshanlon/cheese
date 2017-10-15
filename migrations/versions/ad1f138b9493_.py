"""empty message

Revision ID: ad1f138b9493
Revises: 2d2e39910a7a
Create Date: 2017-10-15 14:50:14.896102

"""

# revision identifiers, used by Alembic.
revision = 'ad1f138b9493'
down_revision = '2d2e39910a7a'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('surveys', sa.Column('signed_up_via', sa.String(length=250), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('surveys', 'signed_up_via')
    # ### end Alembic commands ###

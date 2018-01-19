"""empty message

Revision ID: 944a26b26735
Revises: e4a48be2ca4e
Create Date: 2018-01-19 09:57:48.380432

"""

# revision identifiers, used by Alembic.
revision = '944a26b26735'
down_revision = 'e4a48be2ca4e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('thermal_image', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'thermal_image', 'user', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'thermal_image', type_='foreignkey')
    op.drop_column('thermal_image', 'user_id')
    # ### end Alembic commands ###
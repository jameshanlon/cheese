"""empty message

Revision ID: 769ded4a3cd3
Revises: 91a0734d287e
Create Date: 2017-12-30 10:44:52.744590

"""

# revision identifiers, used by Alembic.
revision = '769ded4a3cd3'
down_revision = '91a0734d287e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('surveys', sa.Column('lead_status', sa.Enum('Possible', 'Successful', 'Dead'), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('surveys', 'lead_status')
    # ### end Alembic commands ###

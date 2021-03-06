"""empty message

Revision ID: a8fa760ce67d
Revises: a96f386eea88
Create Date: 2017-02-25 17:25:08.029231

"""

# revision identifiers, used by Alembic.
revision = 'a8fa760ce67d'
down_revision = 'a96f386eea88'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('month_feedback', sa.Column('date', sa.DateTime(), nullable=True))
    op.add_column('results', sa.Column('date', sa.DateTime(), nullable=True))
    op.add_column('year_feedback', sa.Column('date', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('year_feedback', 'date')
    op.drop_column('results', 'date')
    op.drop_column('month_feedback', 'date')
    # ### end Alembic commands ###

"""empty message

Revision ID: 4a3875909698
Revises: f2114004dfcd
Create Date: 2017-04-27 08:39:22.577071

"""

# revision identifiers, used by Alembic.
revision = '4a3875909698'
down_revision = 'f2114004dfcd'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
##    op.alter_column('month_feedback', 'submitted_by', existing_type= sa.String(length=50), new_column_name='collected_by')
    op.add_column('year_feedback', sa.Column('submitted_by', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
##    op.alter_column('month_feedback', 'collected_by', existing_type= sa.String(length=50), new_column_name='submitted_by')
    op.drop_column('month_feedback', 'submitted_by')
    # ### end Alembic commands ###

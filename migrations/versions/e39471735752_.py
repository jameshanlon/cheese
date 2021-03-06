"""empty message

Revision ID: e39471735752
Revises: 6a9a2ed66030
Create Date: 2016-12-09 09:27:46.083145

"""

# revision identifiers, used by Alembic.
revision = 'e39471735752'
down_revision = '6a9a2ed66030'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('surveys', 'argree_to_requirements', existing_type=sa.Boolean(), new_column_name='agree_to_requirements')
    op.add_column('surveys', sa.Column('reference', sa.String(length=8), nullable=True))
    op.alter_column('surveys', 'survey_date', existing_type=sa.Date(), type_=sa.DateTime())
    ### end Alembic commands ###
 

def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    pass
    ### end Alembic commands ###

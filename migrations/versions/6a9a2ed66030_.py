"""empty message

Revision ID: 6a9a2ed66030
Revises: 5c16728c9b8a
Create Date: 2016-12-04 15:27:10.490337

"""

# revision identifiers, used by Alembic.
revision = '6a9a2ed66030'
down_revision = '5c16728c9b8a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('surveys', sa.Column('argree_to_requirements', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('surveys', 'argree_to_requirements')
    ### end Alembic commands ###
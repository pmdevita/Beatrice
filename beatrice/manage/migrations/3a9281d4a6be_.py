"""

Revision ID: 3a9281d4a6be
Revises: 
Create Date: 2022-07-25 01:09:52.416689

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a9281d4a6be'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('schedule_alarms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('channel', sa.BigInteger(), nullable=False),
    sa.Column('time', sa.DateTime(), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('schedule_alarms')
    # ### end Alembic commands ###

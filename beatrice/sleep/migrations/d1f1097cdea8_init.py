"""init

Revision ID: d1f1097cdea8
Revises: 
Create Date: 2022-08-19 11:57:08.833804

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1f1097cdea8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sleep.sleepchannels',
    sa.Column('guild', sa.BigInteger(), nullable=False, autoincrement=False),
    sa.Column('channel', sa.BigInteger(), nullable=False, autoincrement=False),
    sa.PrimaryKeyConstraint('guild')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('sleep.sleepchannels')
    # ### end Alembic commands ###

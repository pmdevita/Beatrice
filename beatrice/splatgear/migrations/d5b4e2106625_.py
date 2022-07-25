"""

Revision ID: d5b4e2106625
Revises: 
Create Date: 2022-07-25 01:09:52.447142

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5b4e2106625'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('splatgear_brands',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('splatgear_gear',
    sa.Column('_pid', sa.String(length=15), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.Enum('head', 'shoes', 'clothes', name='gearenum'), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=False),
    sa.PrimaryKeyConstraint('_pid')
    )
    op.create_table('splatgear_skills',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('splatgear_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user', sa.BigInteger(), nullable=False),
    sa.Column('gear_id', sa.String(length=15), nullable=True),
    sa.Column('brand_id', sa.Integer(), nullable=True),
    sa.Column('skill_id', sa.Integer(), nullable=True),
    sa.Column('last_messaged', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['brand_id'], ['splatgear_brands.id'], name='fk_splatgear_requests_splatgear_brands_id_brand'),
    sa.ForeignKeyConstraint(['gear_id'], ['splatgear_gear._pid'], name='fk_splatgear_requests_splatgear_gear__pid_gear'),
    sa.ForeignKeyConstraint(['skill_id'], ['splatgear_skills.id'], name='fk_splatgear_requests_splatgear_skills_id_skill'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('splatgear_requests')
    op.drop_table('splatgear_skills')
    op.drop_table('splatgear_gear')
    op.drop_table('splatgear_brands')
    # ### end Alembic commands ###

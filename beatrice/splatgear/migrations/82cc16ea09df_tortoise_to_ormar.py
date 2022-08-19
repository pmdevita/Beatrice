"""tortoise to ormar

Revision ID: 82cc16ea09df
Revises: d5b4e2106625
Create Date: 2022-08-19 13:23:18.709351

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '82cc16ea09df'
down_revision = 'd5b4e2106625'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("splatgear_brands", "Splatgear.brands")
    op.rename_table("splatgear_gear", "Splatgear.gears")
    op.rename_table("splatgear_skills", "Splatgear.skills")
    op.rename_table("splatgear_requests", "Splatgear.gearrequests")


def downgrade() -> None:
    op.rename_table("Splatgear.brands", "splatgear_brands")
    op.rename_table("Splatgear.gears", "splatgear_gear")
    op.rename_table("Splatgear.skills", "splatgear_skills")
    op.rename_table("Splatgear.gearrequests", "splatgear_requests")

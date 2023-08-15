"""added mobile_no and email

Revision ID: aa983693b200
Revises: 9e29f4444832
Create Date: 2023-08-13 12:16:07.480431

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aa983693b200'
down_revision = '9e29f4444832'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email', sa.String(length=500), nullable=False))
        batch_op.add_column(sa.Column('mobile_number', sa.Integer(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.drop_column('mobile_number')
        batch_op.drop_column('email')

    # ### end Alembic commands ###

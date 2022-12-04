"""dev: add column user.avatar_image, rename column user.update_at to .updated_at

Revision ID: a82a53764961
Revises: 6534525df332
Create Date: 2022-11-28 23:00:46.140315

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a82a53764961'
down_revision = '6534525df332'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipe', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
        batch_op.drop_column('update_at')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('avatar_image', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
        batch_op.drop_column('update_at')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('update_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False))
        batch_op.drop_column('updated_at')
        batch_op.drop_column('avatar_image')

    with op.batch_alter_table('recipe', schema=None) as batch_op:
        batch_op.add_column(sa.Column('update_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False))
        batch_op.drop_column('updated_at')

    # ### end Alembic commands ###

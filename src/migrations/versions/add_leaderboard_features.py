"""add leaderboard features

Revision ID: add_leaderboard_features
Revises: update_transfer_and_consumption
Create Date: 2024-01-09 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_leaderboard_features'
down_revision = 'update_transfer_and_consumption'
branch_labels = None
depends_on = None

def upgrade():
    # 添加用户统计数据字段
    op.add_column('user', sa.Column('show_in_leaderboard', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('user', sa.Column('total_transferred', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('user', sa.Column('total_received', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('user', sa.Column('total_consumed', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('user', sa.Column('total_fee_paid', sa.Integer(), nullable=False, server_default='0'))

    # 更新现有数据
    op.execute("""
        UPDATE "user" SET
            total_transferred = (
                SELECT COALESCE(SUM(amount), 0)
                FROM score_transfer
                WHERE from_user_id = "user".id
                AND status = 'confirmed'
            ),
            total_received = (
                SELECT COALESCE(SUM(actual_amount), 0)
                FROM score_transfer
                WHERE to_user_id = "user".id
                AND status = 'confirmed'
            ),
            total_consumed = (
                SELECT COALESCE(SUM(amount), 0)
                FROM score_consumption
                WHERE user_id = "user".id
                AND status = 'confirmed'
            ),
            total_fee_paid = (
                SELECT COALESCE(SUM(fee_amount), 0)
                FROM score_transfer
                WHERE from_user_id = "user".id
                AND status = 'confirmed'
            ) + (
                SELECT COALESCE(SUM(fee_amount), 0)
                FROM score_consumption
                WHERE user_id = "user".id
                AND status = 'confirmed'
            )
    """)

def downgrade():
    # 删除用户统计数据字段
    op.drop_column('user', 'total_fee_paid')
    op.drop_column('user', 'total_consumed')
    op.drop_column('user', 'total_received')
    op.drop_column('user', 'total_transferred')
    op.drop_column('user', 'show_in_leaderboard')

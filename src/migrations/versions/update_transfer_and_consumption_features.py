"""update transfer and consumption features

Revision ID: update_transfer_and_consumption
Revises: add_red_packet_and_payment_features
Create Date: 2024-01-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'update_transfer_and_consumption'
down_revision = 'add_red_packet_and_payment_features'
branch_labels = None
depends_on = None

def upgrade():
    # 修改ScoreTransfer表
    op.add_column('score_transfer', sa.Column('fee_amount', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('score_transfer', sa.Column('actual_amount', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('score_transfer', sa.Column('type', sa.String(20), nullable=False, server_default='single'))
    op.add_column('score_transfer', sa.Column('batch_id', sa.String(64), nullable=True))
    
    # 创建batch_id索引
    op.create_index('ix_score_transfer_batch_id', 'score_transfer', ['batch_id'])
    
    # 修改ScoreConsumption表
    op.add_column('score_consumption', sa.Column('developer_amount', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('score_consumption', sa.Column('fee_amount', sa.Integer(), nullable=False, server_default='0'))

def downgrade():
    # 删除ScoreTransfer表新增列
    op.drop_index('ix_score_transfer_batch_id', 'score_transfer')
    op.drop_column('score_transfer', 'batch_id')
    op.drop_column('score_transfer', 'type')
    op.drop_column('score_transfer', 'actual_amount')
    op.drop_column('score_transfer', 'fee_amount')
    
    # 删除ScoreConsumption表新增列
    op.drop_column('score_consumption', 'fee_amount')
    op.drop_column('score_consumption', 'developer_amount')

"""add transfer features

Revision ID: add_transfer_features
Revises: 95bbbff8f1d8
Create Date: 2024-01-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_transfer_features'
down_revision = '95bbbff8f1d8'
branch_labels = None
depends_on = None

def upgrade():
    # 修改ScoreTransfer表
    # 检查列是否存在
    inspector = sa.inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('score_transfer')]
    if 'min_trust_level' not in columns:
        op.add_column('score_transfer', sa.Column('min_trust_level', sa.Integer(), nullable=True))
    
    # 获取所有表名
    tables = inspector.get_table_names()
    
    # 创建RedPacket表
    if 'red_packet' not in tables:
        op.create_table('red_packet',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column('total_amount', sa.Integer(), nullable=False),
        sa.Column('remaining_amount', sa.Integer(), nullable=False),
        sa.Column('total_count', sa.Integer(), nullable=False),
        sa.Column('remaining_count', sa.Integer(), nullable=False),
        sa.Column('min_trust_level', sa.Integer(), nullable=True),
        sa.Column('whitelist', sa.Text(), nullable=True),  # 用逗号分隔的用户名列表
        sa.Column('blacklist', sa.Text(), nullable=True),  # 用逗号分隔的用户名列表
        sa.Column('token', sa.String(64), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),  # active, completed, expired
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    
    # 创建RedPacketClaim表
    if 'red_packet_claim' not in tables:
        op.create_table('red_packet_claim',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('red_packet_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['red_packet_id'], ['red_packet.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建PaymentRequest表
    if 'payment_request' not in tables:
        op.create_table('payment_request',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requester_id', sa.Integer(), nullable=False),
        sa.Column('payer_id', sa.Integer(), nullable=True),  # 可以为空，表示任何人都可以支付
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('message', sa.String(256), nullable=True),
        sa.Column('token', sa.String(64), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),  # pending, paid, cancelled
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['requester_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['payer_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    
    # 创建Authorization表
    if 'authorization' not in tables:
        op.create_table('authorization',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('app_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),  # periodic, emergency
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('period', sa.String(20), nullable=True),  # daily, weekly, monthly (仅periodic类型需要)
        sa.Column('next_execution', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),  # active, paused, cancelled
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['app_id'], ['app.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建AuthorizationExecution表
    if 'authorization_execution' not in tables:
        op.create_table('authorization_execution',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('authorization_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),  # success, failed
        sa.Column('message', sa.String(256), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['authorization_id'], ['authorization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('authorization_execution')
    op.drop_table('authorization')
    op.drop_table('payment_request')
    op.drop_table('red_packet_claim')
    op.drop_table('red_packet')
    op.drop_column('score_transfer', 'min_trust_level')

"""add red packet and payment features

Revision ID: add_red_packet_and_payment_features
Revises: add_transfer_features
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_red_packet_and_payment_features'
down_revision = 'add_transfer_features'
branch_labels = None
depends_on = None

def upgrade():
    # 添加信任等级限制到转账表
    op.add_column('score_transfer', sa.Column('min_trust_level', sa.Integer(), nullable=False, server_default='0'))
    
    # 创建批量转账表
    op.create_table('batch_transfer',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_user_id', sa.Integer(), nullable=False),
        sa.Column('total_amount', sa.Integer(), nullable=False),
        sa.Column('message', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('min_trust_level', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['from_user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建批量转账项目表
    op.create_table('batch_transfer_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('transfer_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['batch_transfer.id'], ),
        sa.ForeignKeyConstraint(['transfer_id'], ['score_transfer.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建红包表
    op.create_table('red_packet',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_user_id', sa.Integer(), nullable=False),
        sa.Column('total_amount', sa.Integer(), nullable=False),
        sa.Column('total_count', sa.Integer(), nullable=False),
        sa.Column('remaining_amount', sa.Integer(), nullable=False),
        sa.Column('remaining_count', sa.Integer(), nullable=False),
        sa.Column('message', sa.String(length=256), nullable=True),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('min_trust_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('whitelist', sa.Text(), nullable=True),
        sa.Column('blacklist', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['from_user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    
    # 创建红包领取记录表
    op.create_table('red_packet_record',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('red_packet_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['red_packet_id'], ['red_packet.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建收款请求表
    op.create_table('payment_request',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('message', sa.String(length=256), nullable=True),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('min_trust_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('paid_by_id', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['from_user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['paid_by_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )

def downgrade():
    op.drop_table('payment_request')
    op.drop_table('red_packet_record')
    op.drop_table('red_packet')
    op.drop_table('batch_transfer_items')
    op.drop_table('batch_transfer')
    op.drop_column('score_transfer', 'min_trust_level')

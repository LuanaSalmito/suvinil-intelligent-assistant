"""initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar enums do PostgreSQL
    userrole_enum = postgresql.ENUM('admin', 'user', name='userrole')
    userrole_enum.create(op.get_bind(), checkfirst=True)
    
    environment_enum = postgresql.ENUM('interno', 'externo', 'ambos', name='environment')
    environment_enum.create(op.get_bind(), checkfirst=True)
    
    finishtype_enum = postgresql.ENUM('fosco', 'acetinado', 'brilhante', 'semi-brilhante', name='finishtype')
    finishtype_enum.create(op.get_bind(), checkfirst=True)
    
    paintline_enum = postgresql.ENUM('Premium', 'Standard', 'Economy', name='paintline')
    paintline_enum.create(op.get_bind(), checkfirst=True)
    
    # Criar tabela users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('role', userrole_enum, nullable=False, server_default='user'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Criar tabela paints
    op.create_table(
        'paints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('color_name', sa.String(), nullable=True),
        sa.Column('surface_type', sa.String(), nullable=True),
        sa.Column('environment', environment_enum, nullable=False, server_default='interno'),
        sa.Column('finish_type', finishtype_enum, nullable=False, server_default='fosco'),
        sa.Column('features', sa.Text(), nullable=True),
        sa.Column('line', paintline_enum, nullable=False, server_default='Standard'),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_paints_id'), 'paints', ['id'], unique=False)
    op.create_index(op.f('ix_paints_name'), 'paints', ['name'], unique=False)


def downgrade() -> None:
    # Remover índices e tabelas (na ordem inversa)
    op.drop_index(op.f('ix_paints_name'), table_name='paints')
    op.drop_index(op.f('ix_paints_id'), table_name='paints')
    op.drop_table('paints')
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Remover enums (após remover tabelas que os usam)
    op.execute('DROP TYPE IF EXISTS paintline')
    op.execute('DROP TYPE IF EXISTS finishtype')
    op.execute('DROP TYPE IF EXISTS environment')
    op.execute('DROP TYPE IF EXISTS userrole')

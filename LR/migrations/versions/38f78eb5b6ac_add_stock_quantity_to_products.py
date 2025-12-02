"""add_stock_quantity_to_products

Revision ID: 38f78eb5b6ac
Revises: 66d4c3d54b06
Create Date: 2025-12-02 12:32:35.007906

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38f78eb5b6ac'
down_revision: Union[str, Sequence[str], None] = '66d4c3d54b06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Добавляем поле stock_quantity в таблицу products
    op.add_column('products', sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем поле stock_quantity из таблицы products
    op.drop_column('products', 'stock_quantity')

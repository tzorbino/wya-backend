"""added user to post

Revision ID: 857a2fa8aed9
Revises: d2cd3d63c1f9
Create Date: 2025-07-31 15:10:23.751771
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '857a2fa8aed9'
down_revision: Union[str, Sequence[str], None] = 'd2cd3d63c1f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Add the column as nullable
    op.add_column('posts', sa.Column('username', sa.String(), nullable=True))

    # Step 2: Backfill existing posts with usernames from users table
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE posts
        SET username = users.username
        FROM users
        WHERE posts.user_id = users.id
    """))

    # (Optional) Step 3: If you're ready, enforce NOT NULL in a separate migration
    # op.alter_column('posts', 'username', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('posts', 'username')

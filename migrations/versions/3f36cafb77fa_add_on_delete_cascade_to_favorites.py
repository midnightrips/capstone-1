"""Add ON DELETE CASCADE to favorites

Revision ID: 3f36cafb77fa
Revises: 
Create Date: 2024-10-22 13:46:41.847067

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3f36cafb77fa'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Drop the existing foreign key constraints
    op.drop_constraint('favorites_user_id_fkey', 'favorites', type_='foreignkey')
    op.drop_constraint('favorites_game_id_fkey', 'favorites', type_='foreignkey')
    
    # Recreate the foreign key with ON DELETE CASCADE
    op.create_foreign_key('favorites_user_id_fkey', 'favorites', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('favorites_game_id_fkey', 'favorites', 'games', ['game_id'], ['id'], ondelete='CASCADE') 

def downgrade():
    # Revert to the previous foreign key constraints without ON DELETE CASCADE
    op.drop_constraint('favorites_user_id_fkey', 'favorites', type_='foreignkey')
    op.drop_constraint('favorites_game_id_fkey', 'favorites', type_='foreignkey')

    # Recreate the foreign key constraints without ON DELETE CASCADE
    op.create_foreign_key('favorites_user_id_fkey', 'favorites', 'users', ['user_id'], ['id'])
    op.create_foreign_key('favorites_game_id_fkey', 'favorites', 'games', ['game_id'], ['id'])

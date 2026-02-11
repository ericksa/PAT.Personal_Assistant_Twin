# src/repositories/user_repo.py - User repository
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from src.repositories.base import BaseRepository
from src.models.user import User

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for user operations"""

    def __init__(self):
        # User model isn't an SQLAlchemy model yet, using dict-based approach
        super().__init__(object)

    async def get_default_user(self, db: AsyncSession) -> Optional[dict]:
        """
        Get the default user for single-user setup.

        For single-user mode, this always returns the user with ID:
        00000000-0000-0000-0000-000000000001
        """
        try:
            # Since we're using raw SQL for now, just return the default user ID
            return {
                "id": "00000000-0000-0000-0000-000000000001",
                "full_name": "Local User",
                "email": "local@pat.local",
                "timezone": "America/New_York",
            }
        except Exception as e:
            logger.error(f"Error getting default user: {e}")
            raise

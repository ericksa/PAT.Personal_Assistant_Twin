# src/repositories/base.py - Base repository with common CRUD operations
from typing import TypeVar, Generic, List, Optional, Type, Any, Dict
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
import logging

logger = logging.getLogger(__name__)

# Generic type for models
ModelType = TypeVar("ModelType", bound="DeclarativeBase")


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations.

    All repositories should inherit from this and implement
    model-specific queries.
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        """
        Get a single record by ID.

        Args:
            db: Database session
            id: Primary key UUID

        Returns:
            Model instance or None
        """
        try:
            statement = select(self.model).where(self.model.id == id)
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} {id}: {e}")
            raise

    async def get_by_external_id(
        self,
        db: AsyncSession,
        external_id: str,
        external_id_field: str = "external_event_id",
    ) -> Optional[ModelType]:
        """
        Get a record by external ID (for Apple sync).

        Args:
            db: Database session
            external_id: External identifier
            external_id_field: Field name (default: external_event_id)

        Returns:
            Model instance or None
        """
        try:
            field = getattr(self.model, external_id_field, None)
            if field is None:
                logger.warning(
                    f"Field {external_id_field} not found in {self.model.__name__}"
                )
                return None

            statement = select(self.model).where(field == external_id)
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error getting {self.model.__name__} by {external_id_field}: {e}"
            )
            raise

    async def list(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """
        List records with optional pagination and filtering.

        Args:
            db: Database session
            skip: Number of records to skip (pagination)
            limit: Maximum records to return
            filters: Optional dict of filters (e.g., {"status": "active"})

        Returns:
            List of model instances
        """
        try:
            statement = select(self.model)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        statement = statement.where(getattr(self.model, key) == value)

            # Apply pagination
            statement = statement.offset(skip).limit(limit)

            result = await db.execute(statement)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error listing {self.model.__name__}: {e}")
            raise

    async def create(self, db: AsyncSession, obj_data: Dict[str, Any]) -> ModelType:
        """
        Create a new record.

        Args:
            db: Database session
            obj_data: Dictionary of field values

        Returns:
            Created model instance
        """
        try:
            # Remove None values from obj_data to avoid conflicts with defaults
            obj_data = {k: v for k, v in obj_data.items() if v is not None}

            # Create instance
            db_obj = self.model(**obj_data)

            # Add to session
            db.add(db_obj)

            # Flush to get ID but don't commit (caller should commit)
            await db.flush()
            await db.refresh(db_obj)

            logger.info(f"Created {self.model.__name__}: {db_obj.id}")
            return db_obj
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            await db.rollback()
            raise

    async def update(
        self, db: AsyncSession, id: UUID, obj_data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Update an existing record.

        Args:
            db: Database session
            id: Primary key UUID
            obj_data: Dictionary of field values to update

        Returns:
            Updated model instance or None
        """
        try:
            # Remove None values
            obj_data = {k: v for k, v in obj_data.items() if v is not None}

            # Build update statement with current timestamp
            if hasattr(self.model, "updated_at"):
                obj_data["updated_at"] = datetime.utcnow()

            statement = (
                update(self.model)
                .where(self.model.id == id)
                .values(**obj_data)
                .returning(self.model)
            )

            result = await db.execute(statement)
            await db.flush()

            updated_obj = result.scalar_one_or_none()

            if updated_obj:
                logger.info(f"Updated {self.model.__name__}: {id}")

            return updated_obj
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__} {id}: {e}")
            await db.rollback()
            raise

    async def delete(self, db: AsyncSession, id: UUID) -> bool:
        """
        Delete a record.

        Args:
            db: Database session
            id: Primary key UUID

        Returns:
            True if deleted, False if not found
        """
        try:
            statement = delete(self.model).where(self.model.id == id)
            result = await db.execute(statement)

            if result.rowcount > 0:
                logger.info(f"Deleted {self.model.__name__}: {id}")
                return True

            return False
        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__} {id}: {e}")
            await db.rollback()
            raise

    async def count(
        self, db: AsyncSession, filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count records with optional filtering.

        Args:
            db: Database session
            filters: Optional dict of filters

        Returns:
            Count of matching records
        """
        try:
            statement = select(func.count()).select_from(self.model)

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        statement = statement.where(getattr(self.model, key) == value)

            result = await db.execute(statement)
            return result.scalar()
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise

    async def exists(self, db: AsyncSession, id: UUID) -> bool:
        """
        Check if a record exists by ID.

        Args:
            db: Database session
            id: Primary key UUID

        Returns:
            True if exists, False otherwise
        """
        try:
            statement = select(func.count()).select_from(
                select(self.model).where(self.model.id == id).subquery()
            )
            result = await db.execute(statement)
            return result.scalar() > 0
        except Exception as e:
            logger.error(f"Error checking existence of {self.model.__name__} {id}: {e}")
            raise

    async def bulk_create(
        self, db: AsyncSession, objects_data: List[Dict[str, Any]]
    ) -> List[ModelType]:
        """
        Create multiple records in a single transaction.

        Args:
            db: Database session
            objects_data: List of dictionaries with field values

        Returns:
            List of created model instances
        """
        try:
            db_objects = []

            for obj_data in objects_data:
                # Remove None values
                clean_data = {k: v for k, v in obj_data.items() if v is not None}
                db_obj = self.model(**clean_data)
                db.add(db_obj)
                db_objects.append(db_obj)

            # Flush to get IDs
            await db.flush()

            # Refresh all objects
            for db_obj in db_objects:
                await db.refresh(db_obj)

            logger.info(f"Created {len(db_objects)} {self.model.__name__} records")
            return db_objects
        except Exception as e:
            logger.error(f"Error bulk creating {self.model.__name__}: {e}")
            await db.rollback()
            raise

    async def bulk_update(
        self, db: AsyncSession, ids: List[UUID], updates: Dict[str, Any]
    ) -> int:
        """
        Update multiple records with the same values.

        Args:
            db: Database session
            ids: List of primary key UUIDs
            updates: Dictionary of field values to update

        Returns:
            Number of records updated
        """
        try:
            # Add updated_at if applicable
            if hasattr(self.model, "updated_at"):
                updates["updated_at"] = datetime.utcnow()

            statement = (
                update(self.model)
                .where(self.model.id.in_(ids))
                .values(**updates)
                .returning(self.model)
            )

            result = await db.execute(statement)
            await db.flush()

            logger.info(f"Updated {result.rowcount} {self.model.__name__} records")
            return result.rowcount
        except Exception as e:
            logger.error(f"Error bulk updating {self.model.__name__}: {e}")
            await db.rollback()
            raise

    async def get_between_dates(
        self,
        db: AsyncSession,
        date_field: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[ModelType]:
        """
        Get records within a date range.

        Args:
            db: Database session
            date_field: Name of date field to filter on
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of model instances
        """
        try:
            field = getattr(self.model, date_field, None)
            if field is None:
                logger.warning(f"Field {date_field} not found in {self.model.__name__}")
                return []

            statement = (
                select(self.model)
                .where(field >= start_date)
                .where(field <= end_date)
                .order_by(field)
            )

            result = await db.execute(statement)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} between dates: {e}")
            raise

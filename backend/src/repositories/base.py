from typing import Optional, List, Dict, Any, TypeVar, Generic
from abc import ABC, abstractmethod
import asyncpg

# Generic type for models
T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with common database operations"""

    def __init__(self, db_helper):
        self.db = db_helper

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch a single row"""
        return await self.db.fetchrow(query, *args)

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch multiple rows"""
        return await self.db.fetch(query, *args)

    async def execute(self, query: str, *args) -> str:
        """Execute a query without returning rows"""
        return await self.db.execute(query, *args)

    async def create(
        self, table: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generic create operation"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f"${i}" for i in range(1, len(data) + 1)])
        query = f"""
            INSERT INTO {table} ({columns})
            VALUES ({placeholders})
            RETURNING *
        """
        result = await self.fetchrow(query, *data.values())
        return dict(result) if result else None

    async def get_by_id(self, table: str, id_value: str) -> Optional[Dict[str, Any]]:
        """Generic get by ID operation"""
        query = f"SELECT * FROM {table} WHERE id = $1"
        result = await self.fetchrow(query, id_value)
        return dict(result) if result else None

    async def update(
        self, table: str, id_value: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generic update operation"""
        updates = []
        params = []
        for i, (key, value) in enumerate(data.items(), 1):
            updates.append(f"{key} = ${i}")
            params.append(value)

        updates.append("updated_at = NOW()")
        params.append(id_value)

        query = f"""
            UPDATE {table}
            SET {", ".join(updates)}
            WHERE id = ${len(params)}
            RETURNING *
        """
        result = await self.fetchrow(query, *params)
        return dict(result) if result else None

    async def delete(self, table: str, id_value: str) -> bool:
        """Generic delete operation"""
        query = f"DELETE FROM {table} WHERE id = $1"
        result = await self.execute(query, id_value)
        return "DELETE 1" in result

    async def list_all(
        self,
        table: str,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Generic list operation"""
        if user_id:
            query = f"""
                SELECT * FROM {table}
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """
            results = await self.fetch(query, user_id, limit, offset)
        else:
            query = f"""
                SELECT * FROM {table}
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """
            results = await self.fetch(query, limit, offset)
        return [dict(r) for r in results]

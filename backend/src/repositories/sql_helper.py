# src/repositories/sql_helper.py - Async SQL helper for direct database operations
import asyncpg
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)


class AsyncSQLHelper:
    """Helper for async PostgreSQL operations"""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize SQL helper.

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url or "postgresql://llm:llm@localhost:5432/llm"
        self.pool = None

    async def get_connection(self):
        """Get database connection"""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(self.database_url)
        return await self.pool.acquire()

    async def release_connection(self, conn):
        """Release connection back to pool"""
        if self.pool:
            await self.pool.release(conn)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row"""
        conn = await self.get_connection()
        try:
            return await conn.fetchrow(query, *args)
        finally:
            await self.release_connection(conn)

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows"""
        conn = await self.get_connection()
        try:
            return await conn.fetch(query, *args)
        finally:
            await self.release_connection(conn)

    async def execute(self, query: str, *args, fetch: Optional[str] = None) -> Any:
        """
        Execute SQL query.
        """
        if fetch == "one":
            return await self.fetchrow(query, *args)
        elif fetch == "all":
            return await self.fetch(query, *args)

        conn = await self.get_connection()
        try:
            return await conn.execute(query, *args)
        finally:
            await self.release_connection(conn)

    async def execute_many(self, query: str, params_list: List[tuple]) -> str:
        """
        Execute query with multiple parameter sets.
        """
        conn = await self.get_connection()
        try:
            async with conn.transaction():
                for params in params_list:
                    await conn.execute(query, *params)
            return "executed"
        except Exception as e:
            logger.error(f"Error in execute_many: {e}")
            raise
        finally:
            await self.release_connection(conn)

    async def close(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()


# Global instance for single-user setup
sql_helper = AsyncSQLHelper()

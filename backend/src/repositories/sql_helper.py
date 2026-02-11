import asyncpg
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SQLHelper:
    """Helper for PostgreSQL database connections using asyncpg"""

    def __init__(self, dsn: Optional[str] = None):
        self.dsn = (
            dsn
            or "postgresql://pat_user:pat_secure_password_change_me@localhost:5432/pat_core"
        )
        self.pool: Optional[asyncpg.Pool] = None

    async def create_pool(self) -> asyncpg.Pool:
        """Create connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.dsn, min_size=2, max_size=10, command_timeout=60
            )
        return self.pool

    async def close_pool(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def execute(self, query: str, *args) -> str:
        """Execute a SQL query that doesn't return rows"""
        pool = await self.create_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch a single row from the database"""
        pool = await self.create_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch multiple rows from the database"""
        pool = await self.create_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value from the database"""
        pool = await self.create_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def execute_many(self, query: str, *args_list) -> str:
        """Execute a query multiple times with different arguments"""
        pool = await self.create_pool()
        async with pool.acquire() as conn:
            return await conn.executemany(query, args_list)

    async def transaction(self):
        """Get a transaction context manager"""
        pool = await self.create_pool()
        conn = await pool.acquire()
        return conn.transaction()

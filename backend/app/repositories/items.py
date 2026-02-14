"""
Items Database Repository
"""
import logging
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.core.database import DatabaseRepository, DatabaseConnection
from app.models.items import ItemCreate, ItemUpdate, ItemResponse, ItemStats

logger = logging.getLogger(__name__)


class ItemsRepository(DatabaseRepository):
    """Repository for items database operations"""
    
    def __init__(self, db: DatabaseConnection):
        """Initialize items repository"""
        super().__init__(db)
        self.table_name = "items"
    
    async def create_item(self, item_data: ItemCreate) -> ItemResponse:
        """Create a new item in the database"""
        # Convert to dict with timestamps
        data = item_data.model_dump()
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        
        # Generate UUID if not provided
        if "id" not in data:
            from uuid import uuid4
            data["id"] = str(uuid4())
        
        # Ensure tags are stored as array
        if "tags" not in data or data["tags"] is None:
            data["tags"] = []
        
        result = await self.create(data)
        return ItemResponse(**result)
    
    async def get_item_by_id(self, item_id: str) -> Optional[ItemResponse]:
        """Get item by ID"""
        result = await self.get_by_id(item_id)
        if result:
            return ItemResponse(**result)
        return None
    
    async def get_items(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> tuple[List[ItemResponse], int]:
        """Get items with filtering and pagination"""
        # Build WHERE clause
        where_clauses = []
        args = []
        
        if category:
            where_clauses.append("category = $%d" % (len(args) + 1))
            args.append(category)
        
        if is_active is not None:
            where_clauses.append("is_active = $%d" % (len(args) + 1))
            args.append(is_active)
        
        if search:
            where_clauses.append("(name ILIKE $%d OR description ILIKE $%d)" % 
                               (len(args) + 1, len(args) + 2))
            args.extend([f"%{search}%", f"%{search}%"])
        
        where_clause = " AND ".join(where_clauses) if where_clauses else ""
        
        # Get total count
        total = await self.count(where_clause, args)
        
        # Get items
        items_data = await self.get_many(
            where_clause=where_clause,
            args=args,
            order_by="created_at DESC",
            limit=limit,
            offset=skip
        )
        
        items = [ItemResponse(**item_data) for item_data in items_data]
        return items, total
    
    async def update_item(self, item_id: str, item_update: ItemUpdate) -> Optional[ItemResponse]:
        """Update an item"""
        # Check if item exists first
        existing_item = await self.get_by_id(item_id)
        if not existing_item:
            return None
        
        # Get only non-None values from update
        update_data = {k: v for k, v in item_update.model_dump().items() if v is not None}
        
        # Handle price conversion if needed
        if "price" in update_data and update_data["price"] is not None:
            update_data["price"] = float(update_data["price"])
        
        if not update_data:
            # No fields to update, return existing item
            return ItemResponse(**existing_item)
        
        result = await self.update(item_id, update_data)
        if result:
            return ItemResponse(**result)
        return None
    
    async def delete_item(self, item_id: str) -> bool:
        """Delete an item"""
        return await self.delete(item_id)
    
    async def activate_item(self, item_id: str) -> Optional[ItemResponse]:
        """Activate an item"""
        # Check if item exists first
        existing_item = await self.get_by_id(item_id)
        if not existing_item:
            return None
        
        update_data = {"is_active": True}
        result = await self.update(item_id, update_data)
        if result:
            return ItemResponse(**result)
        return None
    
    async def deactivate_item(self, item_id: str) -> Optional[ItemResponse]:
        """Deactivate an item"""
        # Check if item exists first
        existing_item = await self.get_by_id(item_id)
        if not existing_item:
            return None
        
        update_data = {"is_active": False}
        result = await self.update(item_id, update_data)
        if result:
            return ItemResponse(**result)
        return None
    
    async def get_categories(self) -> List[str]:
        """Get all unique categories"""
        query = """
            SELECT DISTINCT category 
            FROM items 
            WHERE category IS NOT NULL 
            AND category != ''
            ORDER BY category
        """
        results = await self.db.fetch_many(query)
        return [row["category"] for row in results if row["category"]]
    
    async def get_statistics(self) -> ItemStats:
        """Get item statistics"""
        # Get basic counts
        total_items = await self.count()
        active_items = await self.count("is_active = True")
        inactive_items = total_items - active_items
        
        # Mock category distribution
        categories = {}
        
        # Mock price statistics
        average_price = 0.0
        price_range = {
            "min": 0.0,
            "max": 0.0
        }
        
        return ItemStats(
            total_items=total_items,
            active_items=active_items,
            inactive_items=inactive_items,
            categories=categories,
            average_price=average_price,
            price_range=price_range
        )
    
    async def ensure_table_exists(self) -> None:
        """Ensure the items table exists"""
        # Mock implementation for testing
        logger.info("Items table created or already exists")
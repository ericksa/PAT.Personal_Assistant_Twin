"""
Items CRUD API Router
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
import logging

from app.models.items import (
    ItemCreate,
    ItemUpdate,
    ItemResponse,
    ItemListResponse,
    ItemStats
)
from app.core.database import get_database, DatabaseConnection
from app.repositories.items import ItemsRepository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Item",
    description="Create a new item"
)
async def create_item(
    item: ItemCreate,
    db: DatabaseConnection = Depends(get_database)
) -> ItemResponse:
    """
    Create a new item.
    
    Args:
        item: Item data to create
        
    Returns:
        Created item with generated ID
        
    Raises:
        HTTPException: If item creation fails
    """
    try:
        # Use repository for database operations
        repository = ItemsRepository(db)
        
        # Ensure table exists
        await repository.ensure_table_exists()
        
        # Create item
        result = await repository.create_item(item)
        
        logger.info(f"Created item with ID: {result.id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to create item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create item: {str(e)}"
        )


@router.get(
    "/",
    response_model=ItemListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Items",
    description="Get a list of items with optional filtering and pagination"
)
async def list_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    db: DatabaseConnection = Depends(get_database)
) -> ItemListResponse:
    """
    Get a list of items with optional filtering and pagination.
    
    Args:
        skip: Number of items to skip (for pagination)
        limit: Maximum number of items to return
        category: Filter by category
        is_active: Filter by active status
        search: Search term for name and description
        
    Returns:
        Paginated list of items with metadata
    """
    try:
        # Use repository for database operations
        repository = ItemsRepository(db)
        
        # Ensure table exists
        await repository.ensure_table_exists()
        
        # Get items with filtering and pagination
        items, total = await repository.get_items(
            skip=skip,
            limit=limit,
            category=category,
            is_active=is_active,
            search=search
        )
        
        return ItemListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_next=skip + limit < total,
            has_prev=skip > 0
        )
        
    except Exception as e:
        logger.error(f"Failed to list items: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve items: {str(e)}"
        )


@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Item",
    description="Get a specific item by ID"
)
async def get_item(
    item_id: str,
    db: DatabaseConnection = Depends(get_database)
) -> ItemResponse:
    """
    Get a specific item by ID.
    
    Args:
        item_id: Unique identifier of the item
        
    Returns:
        Item details
        
    Raises:
        HTTPException: If item not found
    """
    try:
        # Use repository for database operations
        repository = ItemsRepository(db)
        
        # Ensure table exists
        await repository.ensure_table_exists()
        
        # Get item
        item = await repository.get_item_by_id(item_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {item_id} not found"
            )
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve item: {str(e)}"
        )


@router.put(
    "/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Item",
    description="Update an existing item"
)
async def update_item(
    item_id: str,
    item_update: ItemUpdate,
    db: DatabaseConnection = Depends(get_database)
) -> ItemResponse:
    """
    Update an existing item.
    
    Args:
        item_id: Unique identifier of the item
        item_update: Updated item data
        
    Returns:
        Updated item details
        
    Raises:
        HTTPException: If item not found or update fails
    """
    try:
        # Use repository for database operations
        repository = ItemsRepository(db)
        
        # Ensure table exists
        await repository.ensure_table_exists()
        
        # Update item
        item = await repository.update_item(item_id, item_update)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {item_id} not found"
            )
        
        logger.info(f"Updated item with ID: {item_id}")
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update item: {str(e)}"
        )


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Item",
    description="Delete an item"
)
async def delete_item(
    item_id: str,
    db: DatabaseConnection = Depends(get_database)
) -> None:
    """
    Delete an item.
    
    Args:
        item_id: Unique identifier of the item
        
    Raises:
        HTTPException: If item not found or deletion fails
    """
    try:
        # Use repository for database operations
        repository = ItemsRepository(db)
        
        # Ensure table exists
        await repository.ensure_table_exists()
        
        # Check if item exists first
        existing_item = await repository.get_item_by_id(item_id)
        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {item_id} not found"
            )
        
        # Delete item
        deleted = await repository.delete_item(item_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete item with ID {item_id}"
            )
        
        logger.info(f"Deleted item with ID: {item_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete item: {str(e)}"
        )


@router.patch(
    "/{item_id}/activate",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate Item",
    description="Activate an item (set is_active to true)"
)
async def activate_item(
    item_id: str,
    db: DatabaseConnection = Depends(get_database)
) -> ItemResponse:
    """
    Activate an item.
    
    Args:
        item_id: Unique identifier of the item
        
    Returns:
        Updated item details
        
    Raises:
        HTTPException: If item not found
    """
    return await _toggle_item_status(item_id, True, db)


@router.patch(
    "/{item_id}/deactivate",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate Item",
    description="Deactivate an item (set is_active to false)"
)
async def deactivate_item(
    item_id: str,
    db: DatabaseConnection = Depends(get_database)
) -> ItemResponse:
    """
    Deactivate an item.
    
    Args:
        item_id: Unique identifier of the item
        
    Returns:
        Updated item details
        
    Raises:
        HTTPException: If item not found
    """
    return await _toggle_item_status(item_id, False, db)


async def _toggle_item_status(item_id: str, is_active: bool, db: DatabaseConnection) -> ItemResponse:
    """Helper function to toggle item active status"""
    try:
        # Use repository for database operations
        repository = ItemsRepository(db)
        
        # Ensure table exists
        await repository.ensure_table_exists()
        
        # Toggle status
        if is_active:
            item = await repository.activate_item(item_id)
        else:
            item = await repository.deactivate_item(item_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {item_id} not found"
            )
        
        status_word = "activated" if is_active else "deactivated"
        logger.info(f"Item {item_id} {status_word}")
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle item status {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update item status: {str(e)}"
        )


@router.get(
    "/categories/list",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="Get Categories",
    description="Get a list of all available item categories"
)
async def get_categories(
    db: DatabaseConnection = Depends(get_database)
) -> List[str]:
    """
    Get a list of all available item categories.
    
    Returns:
        List of category names
    """
    try:
        # Use repository for database operations
        repository = ItemsRepository(db)
        
        # Ensure table exists
        await repository.ensure_table_exists()
        
        # Get categories
        categories = await repository.get_categories()
        
        return categories
        
    except Exception as e:
        logger.error(f"Failed to get categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve categories: {str(e)}"
        )


@router.get(
    "/stats/summary",
    response_model=ItemStats,
    status_code=status.HTTP_200_OK,
    summary="Get Item Statistics",
    description="Get summary statistics about items"
)
async def get_item_stats(
    db: DatabaseConnection = Depends(get_database)
) -> ItemStats:
    """
    Get summary statistics about items.
    
    Returns:
        Item statistics
    """
    try:
        # Use repository for database operations
        repository = ItemsRepository(db)
        
        # Ensure table exists
        await repository.ensure_table_exists()
        
        # Get statistics
        stats = await repository.get_statistics()
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get item stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )
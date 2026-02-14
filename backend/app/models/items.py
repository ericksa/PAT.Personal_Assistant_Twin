"""
Items API Models
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ItemBase(BaseModel):
    """Base item model with common fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Item name")
    description: Optional[str] = Field(None, max_length=1000, description="Item description")
    price: Optional[float] = Field(None, ge=0, description="Item price")
    category: Optional[str] = Field(None, max_length=100, description="Item category")
    tags: List[str] = Field(default_factory=list, description="Item tags")
    is_active: bool = Field(default=True, description="Whether item is active")


class ItemCreate(ItemBase):
    """Model for creating an item"""
    pass


class ItemUpdate(BaseModel):
    """Model for updating an item"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ItemResponse(ItemBase):
    """Model for item response"""
    id: str = Field(..., description="Unique item identifier")
    created_at: datetime = Field(..., description="Item creation timestamp")
    updated_at: datetime = Field(..., description="Item last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ItemListResponse(BaseModel):
    """Model for paginated item list response"""
    items: List[ItemResponse] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    skip: int = Field(..., ge=0, description="Number of items skipped")
    limit: int = Field(..., ge=1, description="Maximum items per page")
    has_next: bool = Field(..., description="Whether there are more items")
    has_prev: bool = Field(..., description="Whether there are previous items")


class ItemSummary(BaseModel):
    """Model for item summary information"""
    id: str
    name: str
    category: Optional[str]
    price: Optional[float]
    is_active: bool


class ItemStats(BaseModel):
    """Model for item statistics"""
    total_items: int = Field(..., ge=0)
    active_items: int = Field(..., ge=0)
    inactive_items: int = Field(..., ge=0)
    categories: dict = Field(..., description="Category distribution")
    average_price: float = Field(..., ge=0)
    price_range: dict = Field(..., description="Price range (min/max)")
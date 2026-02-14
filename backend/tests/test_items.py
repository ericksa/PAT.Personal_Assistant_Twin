"""
Comprehensive async tests for Items CRUD endpoints
"""
import pytest
import asyncio
from decimal import Decimal
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from app.main import create_app
from app.models.items import ItemCreate, ItemResponse


class TestItemsEndpoints:
    """Test suite for Items CRUD endpoints"""

    @pytest.fixture
    def app(self):
        """Create FastAPI app for testing"""
        return create_app()

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    def test_create_item_success(self, client):
        """Test creating an item successfully"""
        item_data = {
            "name": "Test Item",
            "description": "A test item for testing",
            "price": 99.99,
            "category": "Electronics",
            "tags": ["test", "electronics"],
            "is_active": True
        }
        
        response = client.post("/api/v1/items/", json=item_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # Check response structure
        assert "id" in data
        assert data["name"] == item_data["name"]
        assert data["description"] == item_data["description"]
        assert float(data["price"]) == item_data["price"]
        assert data["category"] == item_data["category"]
        assert data["tags"] == item_data["tags"]
        assert data["is_active"] == item_data["is_active"]
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_item_minimal_data(self, client):
        """Test creating an item with minimal data"""
        item_data = {
            "name": "Minimal Item"
        }
        
        response = client.post("/api/v1/items/", json=item_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["name"] == item_data["name"]
        assert data["description"] is None
        assert data["price"] is None
        assert data["category"] is None
        assert data["tags"] == []
        assert data["is_active"] is True  # Default value

    def test_create_item_validation_error(self, client):
        """Test creating an item with invalid data"""
        # Test empty name
        item_data = {
            "name": "",
            "description": "Test"
        }
        
        response = client.post("/api/v1/items/", json=item_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test negative price
        item_data = {
            "name": "Test Item",
            "price": -10.0
        }
        
        response = client.post("/api/v1/items/", json=item_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_items_empty(self, client):
        """Test listing items when database is empty"""
        response = client.get("/api/v1/items/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert "has_next" in data
        assert "has_prev" in data
        
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_items_with_pagination(self, client):
        """Test listing items with pagination parameters"""
        params = {
            "skip": 10,
            "limit": 5
        }
        
        response = client.get("/api/v1/items/", params=params)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["skip"] == 10
        assert data["limit"] == 5

    def test_list_items_with_filters(self, client):
        """Test listing items with various filters"""
        # Test category filter
        params = {"category": "Electronics"}
        response = client.get("/api/v1/items/", params=params)
        assert response.status_code == status.HTTP_200_OK
        
        # Test active filter
        params = {"is_active": True}
        response = client.get("/api/v1/items/", params=params)
        assert response.status_code == status.HTTP_200_OK
        
        # Test search filter
        params = {"search": "test"}
        response = client.get("/api/v1/items/", params=params)
        assert response.status_code == status.HTTP_200_OK

    def test_get_item_not_found(self, client):
        """Test getting a non-existent item"""
        fake_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.get(f"/api/v1/items/{fake_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

    def test_update_item_not_found(self, client):
        """Test updating a non-existent item"""
        fake_id = "123e4567-e89b-12d3-a456-426614174000"
        update_data = {"name": "Updated Name"}
        
        response = client.put(f"/api/v1/items/{fake_id}", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_item_not_found(self, client):
        """Test deleting a non-existent item"""
        fake_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.delete(f"/api/v1/items/{fake_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_activate_item_not_found(self, client):
        """Test activating a non-existent item"""
        fake_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.patch(f"/api/v1/items/{fake_id}/activate")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_deactivate_item_not_found(self, client):
        """Test deactivating a non-existent item"""
        fake_id = "123e4567-e89b-12d3-a456-426614174000"
        response = client.patch(f"/api/v1/items/{fake_id}/deactivate")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_categories_empty(self, client):
        """Test getting categories when no items exist"""
        response = client.get("/api/v1/items/categories/list")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_item_stats_empty(self, client):
        """Test getting item statistics when no items exist"""
        response = client.get("/api/v1/items/stats/summary")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "total_items" in data
        assert "active_items" in data
        assert "inactive_items" in data
        assert "categories" in data
        assert "average_price" in data
        assert "price_range" in data
        
        # Should be zero for empty database
        assert data["total_items"] == 0
        assert data["active_items"] == 0
        assert data["inactive_items"] == 0
        assert data["average_price"] == 0.0

    def test_list_items_pagination_validation(self, client):
        """Test pagination parameter validation"""
        # Test invalid skip (negative)
        params = {"skip": -1}
        response = client.get("/api/v1/items/", params=params)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test invalid limit (too small)
        params = {"limit": 0}
        response = client.get("/api/v1/items/", params=params)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test invalid limit (too large)
        params = {"limit": 2000}
        response = client.get("/api/v1/items/", params=params)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_item_model_validation(self, client):
        """Test Pydantic model validation"""
        # Test price as string (should be converted to number)
        item_data = {
            "name": "Test Item",
            "price": "49.99"
        }
        
        response = client.post("/api/v1/items/", json=item_data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_items_api_response_structure(self, client):
        """Test that all API responses have consistent structure"""
        # Test create response
        item_data = {"name": "Test Item"}
        create_response = client.post("/api/v1/items/", json=item_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        
        create_data = create_response.json()
        assert "id" in create_data
        assert "name" in create_data
        assert "created_at" in create_data
        assert "updated_at" in create_data
        
        # Test list response
        list_response = client.get("/api/v1/items/")
        assert list_response.status_code == status.HTTP_200_OK
        
        list_data = list_response.json()
        assert "items" in list_data
        assert "total" in list_data
        assert "skip" in list_data
        assert "limit" in list_data
        assert "has_next" in list_data
        assert "has_prev" in list_data

    @pytest.mark.asyncio
    async def test_items_concurrent_operations(self, client):
        """Test concurrent item operations"""
        import asyncio
        
        # Create multiple items concurrently
        items_data = [
            {"name": f"Item {i}", "category": f"Category {i % 3}"}
            for i in range(5)
        ]
        
        # Create items concurrently
        tasks = []
        for item_data in items_data:
            task = asyncio.create_task(
                asyncio.to_thread(client.post, "/api/v1/items/", json=item_data)
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All creations should succeed
        for response in responses:
            assert response.status_code == status.HTTP_201_CREATED

    def test_items_error_handling(self, client):
        """Test that error handling is consistent across endpoints"""
        # Test invalid JSON
        response = client.post("/api/v1/items/", json={"name": "Test"})
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_422_UNPROCESSABLE_ENTITY]
        
        # Test missing required fields
        response = client.post("/api/v1/items/", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestItemsModels:
    """Test Items data models"""

    def test_item_create_model(self):
        """Test ItemCreate model validation"""
        # Valid data
        item_data = {
            "name": "Test Item",
            "description": "Test description",
            "price": 99.99,
            "category": "Electronics",
            "tags": ["test", "electronics"],
            "is_active": True
        }
        
        item = ItemCreate(**item_data)
        assert item.name == item_data["name"]
        assert item.description == item_data["description"]
        assert item.price is not None and float(item.price) == item_data["price"]
        assert item.category == item_data["category"]
        assert item.tags == item_data["tags"]
        assert item.is_active == item_data["is_active"]

    def test_item_response_model(self):
        """Test ItemResponse model"""
        from datetime import datetime
        
        response_data = {
            "id": "test-id",
            "name": "Test Item",
            "description": "Test description",
            "price": Decimal("99.99"),
            "category": "Electronics",
            "tags": ["test"],
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        item = ItemResponse(**response_data)
        assert item.id == response_data["id"]
        assert item.name == response_data["name"]

    def test_item_validation_rules(self):
        """Test model validation rules"""
        # Test name length validation
        with pytest.raises(Exception):  # ValidationError
            ItemCreate(name="")  # Empty name should fail
        
        with pytest.raises(Exception):  # ValidationError
            ItemCreate(name="a" * 201)  # Too long name should fail

    def test_decimal_price_handling(self):
        """Test Decimal price handling"""
        item_data = {
            "name": "Test Item"
        }
        
        item = ItemCreate(**item_data)
        # Price should be None by default
        assert item.price is None


if __name__ == "__main__":
    pytest.main([__file__])
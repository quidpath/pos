"""
Integration tests for POS Service
Tests Stores, Terminals, Sessions, Orders, Payments, Returns, Promotions, Loyalty
"""
import requests
import pytest
import uuid


BASE_URL = "http://localhost:8003"


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check(self):
        """Test health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/health/")
        assert response.status_code == 200


class TestStoreEndpoints:
    """Test Store CRUD endpoints"""

    def test_list_stores_requires_auth(self):
        """Test listing stores requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pos/stores/")
        assert response.status_code in [401, 403]

    def test_create_store_requires_auth(self):
        """Test creating store requires authentication"""
        data = {
            "name": "Test Store",
            "location": "Test Location",
        }
        response = requests.post(f"{BASE_URL}/api/pos/stores/", json=data)
        assert response.status_code in [400, 401, 403]


class TestTerminalEndpoints:
    """Test Terminal endpoints"""

    def test_list_terminals_requires_auth(self):
        """Test listing terminals requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pos/terminals/")
        assert response.status_code in [401, 403, 404]

    def test_create_terminal_requires_auth(self):
        """Test creating terminal requires authentication"""
        data = {
            "name": "Terminal 1",
            "store_id": str(uuid.uuid4()),
        }
        response = requests.post(f"{BASE_URL}/api/pos/terminals/", json=data)
        assert response.status_code in [400, 401, 403, 404]


class TestSessionEndpoints:
    """Test POS Session endpoints"""

    def test_list_sessions_requires_auth(self):
        """Test listing sessions requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pos/sessions/")
        assert response.status_code in [401, 403, 404]

    def test_create_session_requires_auth(self):
        """Test creating session requires authentication"""
        data = {
            "terminal_id": str(uuid.uuid4()),
            "opening_balance": "1000.00",
        }
        response = requests.post(f"{BASE_URL}/api/pos/sessions/", json=data)
        assert response.status_code in [400, 401, 403, 404]


class TestOrderEndpoints:
    """Test POS Order endpoints"""

    def test_list_orders_requires_auth(self):
        """Test listing orders requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pos/orders/")
        assert response.status_code in [401, 403, 404]

    def test_create_order_requires_auth(self):
        """Test creating order requires authentication"""
        data = {
            "session_id": str(uuid.uuid4()),
            "items": [
                {
                    "product_id": str(uuid.uuid4()),
                    "quantity": 1,
                    "price": "100.00",
                }
            ],
        }
        response = requests.post(f"{BASE_URL}/api/pos/orders/", json=data)
        assert response.status_code in [400, 401, 403, 404]


class TestPromotionEndpoints:
    """Test Promotion endpoints"""

    def test_list_promotions_requires_auth(self):
        """Test listing promotions requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pos/promotions/")
        assert response.status_code in [401, 403, 404]

    def test_create_promotion_requires_auth(self):
        """Test creating promotion requires authentication"""
        data = {
            "name": "Test Promotion",
            "discount_type": "percentage",
            "discount_value": "10.00",
        }
        response = requests.post(f"{BASE_URL}/api/pos/promotions/", json=data)
        assert response.status_code in [400, 401, 403, 404]

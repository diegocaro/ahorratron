"""
Tests for the /add_transaction API endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from ahorratron.api.main import app
from ahorratron.api.auth import API_KEY


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def valid_headers():
    """Headers with valid API key."""
    return {"X-API-KEY": API_KEY}


@pytest.fixture
def valid_apple_pay_transaction():
    """Valid Apple Pay transaction data."""
    return {
        "date": "2025-01-15",
        "amount": 25.99,
        "merchant": "Starbucks Coffee",
        "category": "Food & Dining",
        "metadata": {
            "apple_pay_id": "APY123456789",
            "device": "iPhone 15",
            "location": "Seattle, WA"
        }
    }


class TestHealthEndpoint:
    """Test the health check endpoint."""
    
    def test_health_check(self, client):
        """Test that health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestAddTransactionEndpoint:
    """Test the /add_transaction endpoint."""
    
    def test_add_transaction_success(self, client, valid_headers, valid_apple_pay_transaction):
        """Test successful transaction addition."""
        response = client.post(
            "/add_transaction",
            json=valid_apple_pay_transaction,
            headers=valid_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Transaction added successfully"
        assert "transaction_id" in data
        assert data["transaction_id"] is not None
    
    def test_add_transaction_missing_api_key(self, client, valid_apple_pay_transaction):
        """Test transaction addition without API key."""
        response = client.post(
            "/add_transaction",
            json=valid_apple_pay_transaction
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "X-API-KEY header is required" in data["detail"]
    
    def test_add_transaction_invalid_api_key(self, client, valid_apple_pay_transaction):
        """Test transaction addition with invalid API key."""
        response = client.post(
            "/add_transaction",
            json=valid_apple_pay_transaction,
            headers={"X-API-KEY": "invalid-key"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Invalid API key" in data["detail"]
    
    def test_add_transaction_missing_required_fields(self, client, valid_headers):
        """Test transaction addition with missing required fields."""
        incomplete_transaction = {
            "date": "2025-01-15",
            "amount": 25.99
            # Missing merchant and category
        }
        
        response = client.post(
            "/add_transaction",
            json=incomplete_transaction,
            headers=valid_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_add_transaction_invalid_date_format(self, client, valid_headers):
        """Test transaction addition with invalid date format."""
        invalid_transaction = {
            "date": "01/15/2025",  # Invalid format
            "amount": 25.99,
            "merchant": "Test Merchant",
            "category": "Test Category"
        }
        
        response = client.post(
            "/add_transaction",
            json=invalid_transaction,
            headers=valid_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "Invalid date format" in data["message"]
    
    def test_add_transaction_invalid_amount(self, client, valid_headers):
        """Test transaction addition with invalid amount."""
        invalid_transaction = {
            "date": "2025-01-15",
            "amount": "not-a-number",
            "merchant": "Test Merchant",
            "category": "Test Category"
        }
        
        response = client.post(
            "/add_transaction",
            json=invalid_transaction,
            headers=valid_headers
        )
        
        assert response.status_code == 422  # Validation error from Pydantic
    
    def test_add_transaction_with_metadata(self, client, valid_headers):
        """Test transaction addition with metadata."""
        transaction_with_metadata = {
            "date": "2025-01-15",
            "amount": 50.0,
            "merchant": "Apple Store",
            "category": "Electronics",
            "metadata": {
                "apple_pay_id": "APY987654321",
                "device": "Apple Watch",
                "touch_id": True
            }
        }
        
        response = client.post(
            "/add_transaction",
            json=transaction_with_metadata,
            headers=valid_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transaction_id" in data
    
    def test_add_transaction_without_metadata(self, client, valid_headers):
        """Test transaction addition without metadata."""
        transaction_no_metadata = {
            "date": "2025-01-15",
            "amount": 15.50,
            "merchant": "Local Cafe",
            "category": "Food & Dining"
        }
        
        response = client.post(
            "/add_transaction",
            json=transaction_no_metadata,
            headers=valid_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transaction_id" in data
    
    def test_add_transaction_negative_amount(self, client, valid_headers):
        """Test transaction addition with negative amount (refund)."""
        refund_transaction = {
            "date": "2025-01-15",
            "amount": -10.00,
            "merchant": "Amazon",
            "category": "Refund"
        }
        
        response = client.post(
            "/add_transaction",
            json=refund_transaction,
            headers=valid_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transaction_id" in data
    
    def test_add_transaction_zero_amount(self, client, valid_headers):
        """Test transaction addition with zero amount."""
        zero_transaction = {
            "date": "2025-01-15",
            "amount": 0.00,
            "merchant": "Test Merchant",
            "category": "Test"
        }
        
        response = client.post(
            "/add_transaction",
            json=zero_transaction,
            headers=valid_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transaction_id" in data


class TestActualBudgetIntegration:
    """Test the Actual Budget integration functionality."""
    
    def test_actual_budget_conversion(self, client, valid_headers):
        """Test that transactions are properly converted to Actual Budget format."""
        from ahorratron.actual_budget import actual_budget
        
        apple_pay_data = {
            "date": "2025-01-15",
            "amount": 30.99,
            "merchant": "Whole Foods",
            "category": "Groceries",
            "metadata": {
                "apple_pay_id": "APY111222333",
                "loyalty_card": "WF123456"
            }
        }
        
        # Test the conversion function directly
        actual_format = actual_budget.convert_apple_pay_to_actual_format(apple_pay_data)
        
        # Check required fields
        assert actual_format["date"] == "2025-01-15"
        assert actual_format["amount"] == 30.99
        assert "Whole Foods (Groceries)" in actual_format["description"]
        assert "apple_pay_id: APY111222333" in actual_format["notes"]
        assert "loyalty_card: WF123456" in actual_format["notes"]
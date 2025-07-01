# Apple Pay Transaction API

This document describes the `/add_transaction` endpoint for processing Apple Pay transactions.

## Quick Start

1. Install dependencies:
```bash
pip install .
```

2. Start the API server:
```bash
ahorratron-api
```

The server will start on `http://localhost:8000`

## API Documentation

### Authentication

All API requests require an `X-API-KEY` header:
```
X-API-KEY: your-secret-api-key
```

### POST /add_transaction

Add an Apple Pay transaction to the Actual Budget system.

#### Request Body

```json
{
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
```

#### Fields

- `date` (required): Transaction date in YYYY-MM-DD format
- `amount` (required): Transaction amount (float, can be negative for refunds)
- `merchant` (required): Merchant name
- `category` (required): Transaction category
- `metadata` (optional): Additional Apple Pay metadata as key-value pairs

#### Success Response (200)

```json
{
  "success": true,
  "message": "Transaction added successfully",
  "transaction_id": "5a0b1e49-4efb-4435-90b8-a37926662b29"
}
```

#### Error Responses

**401 Unauthorized**
```json
{
  "detail": "X-API-KEY header is required"
}
```

**422 Validation Error**
```json
{
  "success": false,
  "message": "Invalid date format. Expected YYYY-MM-DD",
  "error_code": "ACTUAL_BUDGET_ERROR"
}
```

## Example Usage

### Using curl

```bash
curl -X POST http://localhost:8000/add_transaction \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: your-secret-api-key" \
  -d '{
    "date": "2025-01-15",
    "amount": 25.99,
    "merchant": "Starbucks Coffee",
    "category": "Food & Dining",
    "metadata": {
      "apple_pay_id": "APY123456789",
      "device": "iPhone 15"
    }
  }'
```

### Using Python requests

```python
import requests

url = "http://localhost:8000/add_transaction"
headers = {
    "Content-Type": "application/json",
    "X-API-KEY": "your-secret-api-key"
}
data = {
    "date": "2025-01-15",
    "amount": 25.99,
    "merchant": "Starbucks Coffee",
    "category": "Food & Dining",
    "metadata": {
        "apple_pay_id": "APY123456789",
        "device": "iPhone 15"
    }
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

## Health Check

The API provides a health check endpoint:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy"
}
```

## Interactive Documentation

When the server is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
# 🏦 Actual API

> API REST para integración directa con Actual Budget

La **Actual API** es un servicio web que proporciona una interfaz REST para interactuar directamente con [Actual Budget](https://actualbudget.com/), permitiendo agregar transacciones, obtener resúmenes financieros y gestionar datos de presupuesto de forma programática.

---

## ✨ Características

- **Integración directa** con la base de datos de Actual Budget
- **Autenticación segura** mediante API Key

---

## 🚀 Endpoints Disponibles

### 🔍 Health Check
```http
GET /api/health
```
Verifica el estado de la conexión con Actual Budget.

**Respuesta:**
```json
{
  "status": "healthy"
}
```

### 💰 Agregar Transacción
```http
POST /api/add_transaction
Content-Type: application/json
X-API-KEY: your-api-key
```

**Cuerpo de la petición:**
```json
{
  "amount": -50000.0,
  "date": "2025-01-15T10:30:00Z",
  "payee": "Supermercado XYZ",
  "notes": "Compras semanales"
}
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Transaction added successfully",
  "transaction_id": "uuid-1234-5678-9abc"
}
```

### 📊 Resumen Mensual
```http
GET /api/summary?month=2025-01-01
X-API-KEY: your-api-key
```

**Respuesta:**
```json
{
  "month": "2025-01",
  "categories": [
    {
      "category_name": "Alimentación",
      "group_name": "Gastos Fijos",
      "budgeted": 200000.0,
      "spent": 150000.0,
      "available": 50000.0
    }
  ]
}
```

---

## 🛠️ Arquitectura

```
actual_api/
├── main.py              # Aplicación FastAPI principal
├── routes.py            # Definición de endpoints REST
├── service.py           # Lógica de negocio con Actual Budget
├── models.py            # Modelos Pydantic para validación
├── auth.py              # Sistema de autenticación
└── config.py            # Configuración de la aplicación
```

### 🔧 Componentes Principales

- **`ActualBudgetService`**: Clase principal para interactuar con Actual Budget
- **`Transaction`**: Modelo con validación inteligente de montos
- **`verify_api_key`**: Middleware de autenticación
- **`health_check`**: Endpoint de monitoreo

---

## ⚙️ Configuración

### Variables de Entorno Requeridas

```bash
# Autenticación de la API
API_KEY=tu-clave-secreta-muy-segura

# Configuración de Actual Budget
ACTUAL_URL=http://localhost:5006
ACTUAL_PASSWORD=tu-password-actual
ACTUAL_FILE=Mi-Presupuesto
ACTUAL_DEFAULT_ACCOUNT=Cuenta-Corriente-Principal

# Opcional: Prefijo para payees
PAYEE_PREFIX="Pago:"
```

### Archivo `.env` de Ejemplo

```env
API_KEY=ahorratron-2025-super-secret-key
ACTUAL_URL=http://actual-server:5006
ACTUAL_PASSWORD=mi_password_secreto
ACTUAL_FILE=Presupuesto-Familiar-2025
ACTUAL_DEFAULT_ACCOUNT=Banco-de-Chile-CTE
PAYEE_PREFIX="🏦 "
```

---

## 🚀 Instalación y Uso

```bash
# Instalar dependencias
uv sync

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Ejecutar servidor de desarrollo
uv run uvicorn ahorratron.actual_api.main:app --reload --port 8000
```

---

## 🔒 Autenticación

La API utiliza autenticación mediante **API Key** en el header (`API_KEY` en tu archivo `.env`):

```bash
# Ejemplo con curl
curl -X POST "http://localhost:8000/api/add_transaction" \
  -H "X-API-KEY: tu-clave-secreta" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": -25000,
    "date": "2025-01-15T14:30:00Z",
    "payee": "Farmacia",
    "notes": "Medicamentos"
  }'
```

---

## 🎯 Casos de Uso

### 1. Integración con Apple Pay + Apple Shortcuts
```python
# Procesar notificación de Apple Pay
transaction_data = {
    "amount": -apple_pay_amount,
    "date": apple_pay_timestamp,
    "payee": apple_pay_merchant,
    "notes": f"Apple Pay - {apple_pay_transaction_id}"
}
```

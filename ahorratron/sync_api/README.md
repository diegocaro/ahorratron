# 🔗 Sync API

> API compatible con Pluggy.ai para sincronización bancaria en tiempo real

La **Sync API** es un servicio que emula la API de [Pluggy.ai](https://pluggy.ai) para proporcionar integración bancaria en tiempo real con Actual Budget. Conecta directamente con los sistemas del Banco de Chile para obtener cuentas, saldos y transacciones de forma automática y segura.

---

## ✨ Características

- **Compatible con Pluggy.ai**: Emula la API estándar para integración con Actual Budget
- **Autenticación segura**: Tokens JWT encriptados con credenciales bancarias
- **Sincronización en tiempo real**: Obtiene datos directamente desde los bancos

---

## 🏦 Instituciones Soportadas

### Banco de Chile
- ✅ **Cuentas Corrientes** y **Cuentas Vista (FAN)**
- ✅ **Tarjetas de Crédito** (movimientos facturados y no facturados)
- ✅ **Saldos en tiempo real**
- ✅ **Historial de transacciones**

---

## 🚀 Endpoints de la API

### 🔐 Autenticación

```http
POST /auth
Content-Type: application/json
```

**Cuerpo de la petición:**
```json
{
  "clientId": "12345678-9",
  "clientSecret": "tu-password-bancario",
}
```

**Respuesta:**
```json
{
  "apiKey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 🏦 Obtener Cuentas

```http
GET /accounts
X-API-KEY: your-api-key
```

**Respuesta:**
```json
{
  "results": [
    {
      "id": "cuenta-corriente-123",
      "type": "BANK",
      "subtype": "CHECKING_ACCOUNT",
      "number": "123-45678-90",
      "name": "Cuenta Corriente",
      "balance": 150000.0,
      "currency": "CLP",
      "bankData": {
        "transferNumber": "12345678900123456789",
        "closingBalance": 1500000.0,
        "automaticallyInvestedBalance": 0.0
      }
    }
  ],
  "total": 1,
  "totalPages": 1,
  "page": 1
}
```

### 💰 Obtener Transacciones

```http
GET /transactions?accountId=cuenta-corriente-123
X-API-KEY: your-api-key
```

**Respuesta:**
```json
{
  "results": [
    {
      "id": "tx-789",
      "description": "Pago Supermercado XYZ",
      "amount": -50000.0,
      "date": "2025-01-15T10:30:00Z",
      "balance": 1450000.0,
      "currency": "CLP",
      "type": "DEBIT",
      "status": "POSTED",
      "merchant": {
        "name": "Supermercado XYZ",
        "category": "supermarkets"
      }
    }
  ],
  "total": 1,
  "totalPages": 1,
  "page": 1
}
```

### 🔍 Detalle de Cuenta

```http
GET /accounts/{accountId}
X-API-KEY: your-api-key
```

---

## 🛠️ Arquitectura

```
sync_api/
├── main.py                    # Aplicación FastAPI principal
├── service.py                 # Capa de servicio
├── core/
│   ├── connector.py          # Clase base para conectores bancarios
│   └── factory.py            # Factory pattern para conectores
├── institutions/
│   └── banco_de_chile/       # Implementación específica del banco
│       ├── banco_de_chile.py # Cliente API del banco
│       ├── connector.py      # Conector Pluggy-compatible
│       ├── models.py         # Modelos específicos del banco
│       └── demo.py          # Cliente demo para desarrollo
├── models/                   # Modelos compatibles con Pluggy.ai
│   ├── account_models.py     # Modelos de cuentas
│   ├── core_models.py        # Modelos de autenticación
│   └── transaction_models.py # Modelos de transacciones
└── utils/
    ├── constants.py          # Constantes de la aplicación
    └── token.py             # Utilidades JWT
```

---

## ⚙️ Configuración

### Variables de Entorno

```bash
BANK_LOGIN_URL=https://portalpe.banco.cl/login
BANK_API_BASE_URL=https://banco.cl...

HEADER_REFERER=https://portal.banco.cl...
HEADER_ORIGIN=https://banco.cl...

JWE_SECRET_KEY="jwe_secret_key_to_encrypt_session_data"
JWT_SECRET_KEY="jwt_secret_key_to_sign_session_data"

```

---

## 🚀 Instalación y Uso

### 1. Desarrollo Local

```bash
# Instalar dependencias
uv sync

# Configurar variables de entorno
cp .env.example .env

# Ejecutar en modo desarrollo con datos demo
uv run uvicorn ahorratron.sync_api.main:app --reload --port 8000
```



---

## 🔒 Autenticación y Seguridad

### Flujo de Autenticación

1. **Cliente** envía credenciales bancarias a `/auth`
2. **Sync API** valida credenciales con el banco
3. **Sistema** genera token JWT encriptado con credenciales
4. **Cliente** usa el token para todas las operaciones subsequentes
5. **Sync API** desencripta token y usa credenciales para consultas bancarias

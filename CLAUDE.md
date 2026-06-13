# Ahorratrón — CLAUDE.md

API compatible con Pluggy.ai que sincroniza bancos chilenos con Actual Budget. El servidor se hace pasar por `api.pluggy.ai` (via alias de red en Docker) para que Actual Budget no requiera modificaciones.

## Comandos esenciales

```bash
uv sync                                                              # instalar dependencias
uv run uvicorn ahorratron.sync_api.main:app --reload --port 8000    # servidor de desarrollo
uv run pytest                                                        # tests
uv run ruff check .                                                  # lint (con autofix: ruff check --fix .)
uv run pyright                                                       # type check
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up   # stack con hot-reload para desarrollo
docker-compose up                                                    # stack completo (Actual + API + Selenium) en producción
```

### Docker en desarrollo

Para desarrollo local con hot-reload, usar el compose file de desarrollo:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Esto monta el código local (`./ahorratron`) en el contenedor y habilita auto-reload en uvicorn. Cualquier cambio en los archivos se refleja automáticamente sin necesidad de reconstruir la imagen.

## Arquitectura

```
ahorratron/sync_api/
├── main.py               # FastAPI: /auth, /accounts, /transactions
├── service.py            # Agrega resultados de múltiples instituciones
├── core/
│   ├── connector.py      # ABC: get_accounts / get_account_by_id / get_transactions
│   ├── factory.py        # Registro de conectores + caché en memoria (SHA256 de credenciales)
│   └── credentials.py   # Parseo multi-banco (base64 JSON) y single-banco (legacy)
├── institutions/
│   ├── banco_de_chile/   # Selenium + APIs privadas del banco
│   └── banco_consorcio/  # APIs privadas (WIP — solo cuenta corriente)
├── models/               # Modelos Pluggy.ai-compatibles (Account, Transaction, SessionData)
└── utils/
    ├── token.py          # JWT (HS256) + JWE (A256GCM) — las credenciales viajan encriptadas
    └── constants.py      # Zona horaria America/Santiago, CLP, formatos de fecha
```

## Flujo de autenticación

1. `POST /auth` recibe `clientId` / `clientSecret`.
2. `parse_multi_credentials` los convierte en `list[UserData]`.
3. `SessionData(users=[...])` se encripta con JWE y luego se firma con JWT → `apiKey`.
4. Todas las llamadas siguientes llevan `X-API-KEY: <token>`; el middleware lo desencripta y reconstruye `SessionData`.
5. Las credenciales nunca se almacenan en el servidor — viajan en el token.

Token TTL: **12 horas**. Keys: `JWE_SECRET_KEY` (32 bytes en hex), `JWT_SECRET_KEY`.

## Formatos de credenciales

**Single-bank (Banco de Chile por defecto):**
```
clientId:     "12345678-9"              # solo RUT
clientSecret: "mi-clave"
```
El `connector_id` por defecto es `banco_de_chile`. También acepta `connector_id;RUT`.

**Multi-banco (base64 JSON):**
```bash
echo -n '{"banco_de_chile": "12345678-9", "banco_consorcio": "98765432-1"}' | base64
echo -n '{"banco_de_chile": "pass1", "banco_consorcio": "pass2"}' | base64
```
Cada clave del JSON es un `connector_id`. Los IDs válidos están en el dict `CONNECTORS` de `factory.py`.

## IDs de cuenta multi-banco

`Service` prefija los IDs de cuenta con `connector_id:` (ej. `banco_de_chile:123456`) para poder enrutar `/accounts/{id}` y `/transactions?accountId=` a la institución correcta. Los IDs legacy (sin prefijo) se enrutan siempre al primer usuario.

## Caché

- **Factory** (`factory.py`): caché en memoria por SHA256 de credenciales — persiste sesión de Selenium entre requests. No apto para producción multi-proceso (usar Redis).
- **Connectors**: `TTLCache(maxsize=100, ttl=60)` por conector — evita rellamar `get_productos` en cada request.

## Variables de entorno

| Variable | Descripción |
|---|---|
| `JWE_SECRET_KEY` | 32 bytes en hex (para A256GCM) |
| `JWT_SECRET_KEY` | clave para firmar JWT (HS256) |
| `BANK_LOGIN_URL` | URL de login de Banco de Chile |
| `BANK_API_BASE_URL` | Base URL de la API de BdC |
| `HEADER_REFERER` / `HEADER_ORIGIN` | Headers requeridos por BdC |
| `CONSORCIO_API_BASE_URL` | Base URL de Banco Consorcio |
| `CONSORCIO_TC_API_BASE_URL` | Base URL de tarjetas Consorcio |
| `CONSORCIO_LOGIN_URL` | URL de login Consorcio |
| `CONSORCIO_REFERER` / `CONSORCIO_ORIGIN` | Headers requeridos por Consorcio |
| `CONSORCIO_ENC_KEY` / `CONSORCIO_ENC_IV` | Clave/IV AES para Consorcio |

Ver plantilla en `tests/test_sync_api/testing.env`.

## Tests

```bash
uv run pytest tests/                         # todos
uv run pytest tests/test_sync_api/           # solo sync_api
```

- Fixtures en `tests/test_sync_api/conftest.py` (carga `testing.env` con python-dotenv).
- Datos de prueba en JSON bajo `tests/test_sync_api/test_institutions/*/data/`.
- Los tests de conectores usan los JSON como fixtures; no hay mocks de la base de datos.

## Agregar un nuevo banco

1. Crear `sync_api/institutions/<banco>/` con:
   - `<banco>.py` — cliente HTTP de la API del banco.
   - `connector.py` — implementa `ConnectorBase` (`get_accounts`, `get_account_by_id`, `get_transactions`).
   - `models.py` — modelos Pydantic de la respuesta del banco.
2. Registrar en `CONNECTORS` de `factory.py`:
   ```python
   "nombre_banco": (NombreBancoConnector, NombreBancoAPIClient),
   ```
3. Agregar variables de entorno necesarias al `.env.example` y `testing.env`.

## Banco de Chile — detalles de implementación

- Usa Selenium para el login (sesión lenta, ~30 s en frío).
- `DemoAPIClient` en `demo.py` sirve datos cacheados para desarrollo local.
- Tipos de producto soportados: `cuenta` (corriente), `tarjeta` (crédito), `ahorro`.
- Tarjetas de crédito: combina movimientos **no facturados** (PENDING) y **facturados** (POSTED). La deduplicación descarta no-facturados cuya fecha sea ≤ la fecha máxima de facturados.
- Transacciones internacionales en no-facturados se omiten (`origenTransaccion != NAC`).
- `SAVINGS_ACCOUNT` se mapea como `CHECKING_ACCOUNT` por un bug conocido en Actual Budget.

## Banco Consorcio — estado WIP

- Solo cuenta corriente (`CUENTA_CORRIENTE`) está implementada.
- Las demás cuentas/productos se loguean como `warning` y se omiten.

## Sesiones legacy

`SessionData` migra tokens viejos que traían `user_data` (campo singular) a `users` (lista) via `model_validator`. No eliminar el campo `user_data` de `SessionData` hasta asegurarse de que no haya tokens viejos en circulación.

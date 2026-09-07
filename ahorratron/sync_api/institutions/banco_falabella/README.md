# Banco Falabella

Conector Pluggy-compatible (Selenium + scrape DOM) para cuenta corriente y CMR.

## Variables de entorno

| Variable | Requerida | Default | Descripción |
|---|---|---|---|
| `FALABELLA_LOGIN_URL` | sí | — | URL de login del banco. Definir en `.env` / `.env.example`. |
| `FALABELLA_CHECKING_MAX_MONTHS` | no | `1` | Cuántos periodos `MM/YYYY` scrapear de la cartola de cuenta corriente (más reciente primero). `1` = solo el mes calendario actual. La UI deja vacía la tabla con "Últimos" / "Mes en curso", por eso se usa el selector por mes. |

Plantilla en el `.env.example` de la raíz del repo.

## Smoke live

```bash
uv run python ahorratron/sync_api/institutions/banco_falabella/live_falabella_smoke.py
uv run python ahorratron/sync_api/institutions/banco_falabella/live_falabella_api_smoke.py
```

Credenciales: `CL_FALABELLA_USER` / `CL_FALABELLA_PASSWORD`.

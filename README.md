# Ahorratrón

<img src="images/ahorratron.png" alt="Ahorratrón - El chanchito que automatiza tus finanzas" width="300" align="right">

> 🐷💾 El chanchito que automatiza tus finanzas

**Ahorratrón** es una herramienta en Python para ayudarte a organizar, convertir y analizar tus datos financieros, especialmente diseñada para obtener datos de cartolas bancarias y de tarjetas de crédito.

Inspirada en los tradicionales chanchitos de ahorro, esta herramienta busca facilitar el control de gastos, fomentar el ahorro y ayudarte a tomar el control de tus finanzas personales (o familiares).

La herramienta combina tres componentes principales:
- 🔗 **[API de Sincronización](ahorratron/sync_api/README.md)**: Conecta en tiempo real con tu banco 
- 🏦 **[Integración con Actual Budget](ahorratron/actual_api/README.md)**: Se conecta directamente con tu aplicación de presupuesto favorita [Actual Budget](https://actualbudget.org/)
- 🔄 **[Conversor](ahorratron/conversor/README.md)**: Transforma cartolas bancarias a formatos compatibles (solo Banco de Chile)

## 🎬 Demo en Acción

La siguiente demo muestra [Actual Budget](https://actualbudget.org/) sincronizando automáticamente las transacciones de una cuenta corriente del Banco de Chile:

![Demo Sync](images/actual-budget-sync.gif)

> **Nota:** Esta demo utiliza datos en caché para mostrar el proceso de forma rápida. En un entorno real, la sincronización completa toma ~30 segundos (incluye el inicio de sesión bancario y la obtención de transacciones).

---

## 🏦 Bancos Soportados

Actualmente, Ahorratrón solo está conectado con el **Banco de Chile**, incluyendo:

- ✅ **Cuentas Corrientes**
- ✅ **Cuentas Vista (FAN)**  
- ✅ **Tarjetas de Crédito** (movimientos facturados y no facturados)

---

## 🚀 Inicio Rápido con Docker

La forma más sencilla de usar Ahorratrón es con Docker Compose, que lanza automáticamente:
- Un servidor de Actual Budget (clon local de Actual Budget)
- La API de sincronización bancaria de Ahorratrón
- Todos los servicios necesarios para la conexión


### Configuración

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/diegocaro/ahorratron.git
   cd ahorratron
   ```

2. **Crea el archivo de configuración:**
   ```bash
   cp .env.example .env
   ```

3. **Configura tus credenciales bancarias** en el archivo `.env`:
   ```bash
   BANK_LOGIN_URL=https://banco.cl/login
   BANK_API_BASE_URL=https://banco.cl/api
   HEADER_REFERER=https://banco.cl/index.html
   HEADER_ORIGIN=https://banco.cl
   JWE_SECRET_KEY="llave_secreta_para_encriptar"
   JWT_SECRET_KEY="llave_secreta_para_firmar"
   ```

4. **Inicia los servicios:**
   ```bash
   docker-compose up
   ```

### Acceso a la Aplicación

Una vez iniciados los servicios, podrás acceder a:

- **Actual Budget**: http://localhost:5006
- **API de Ahorratrón**: https://localhost:8443

### Configuración de Actual Budget

![Configuración de Actual Budget](images/actual-budget-config.gif)

Para conectar tu banco con Actual Budget a través de Ahorratrón:

1. **Crea una cuenta en Actual Budget:**
   - Ve a http://localhost:5006
   - Crea un nuevo presupuesto o selecciona uno existente

2. **Activa la funcionalidad experimental de Pluggy.ai:**
   - En Actual Budget, ve a **Settings** (Configuración)
   - Busca la opción **Experimental Features** (Funcionalidades Experimentales)
   - Activa la opción **Pluggy.ai Integration** (Experimental)

3. **Configura la conexión bancaria:**
   - Ve a la sección de **Accounts** (Cuentas) en Actual Budget
   - Busca la opción **Set up Pluggy.ai for bank sync**
   - Ingresa los siguientes datos:
     - **Client ID**: Tu RUT (ej: 12345678-9)
     - **Client Secret**: Tu clave del banco
     - **Items ID**: `chile`

4. **Vincula tu cuenta bancaria:**
   - Elige las cuentas que deseas sincronizar
   - Confirma la vinculación

Una vez completado, tus transacciones bancarias se sincronizarán automáticamente con tu presupuesto en Actual Budget.



---

## 💻 Uso Avanzado (Línea de Comandos)

Si prefieres usar Ahorratrón directamente desde la línea de comandos:
### Instalación de Dependencias

Requiere Python 3.12 o superior.

```bash
git clone git@github.com:diegocaro/ahorratron.git
cd ahorratron
uv sync
```

### Herramientas de Conversión

**Convertir cartolas existentes:**
```bash
convert-to-actual cartola.txt -o datos.csv
```

**Descargar cartola del banco y convertir directamente: (solo Banco de Chile)**
```bash
# Configurar credenciales
export BANK_USER=11111111-1
export BANK_PASSWORD=TuPassword
export BANK_URL=https://banco.cl

# Descargar y convertir
bank-statement --account cte | convert-to-actual -o cartola.csv
```
---

## 🏦 Bancos e Instituciones Soportadas

| Institución | Cuentas Corrientes | Cuentas Vista | Cuentas de Ahorro | Tarjetas de Crédito Facturados | Tarjetas de Crédito No Facturados | Estado |
|-------------|:------------------:|:-------------:|:-----------------:|:-------------:|:----------------:|:------:|
| **Banco de Chile** | ✅ | ✅ | - | ✅ | ✅ | **Implementado** |
| **Banco Consorcio** | ✅ | X | X | X | X | WIP | 
| **Banco Santander** | - | - | - | - | - |  |
| **Banco Estado** | - | - | - | - | - |  |
| **Banco Security** | - | - | - | - | - |  |
| **Banco Falabella** | - | - | - | - | - |  |
| **Scotiabank** | - | - | - | - | - |  |
| **Banco BCI** | - | - | - | - | - |  |
| **Banco Itaú** | - | - | - | - | - |  |
| **Coopeuch** | - | - | - | - | - |  |
| **Fintual** | - | - | - | - | - | Coming soon? |


**Leyenda:**
- ✅ **Implementado**: Funciona completamente  
- **-** : Pull requests bienvenidos: ¡Contribuciones de la comunidad son bienvenidas!
- **N/A**: No aplica para este tipo de institución

---

## Contribuciones

¡Las contribuciones son bienvenidas! Si tienes ideas para mejorar Ahorratrón o quieres agregar soporte para otros bancos, no dudes en crear un issue o enviar un pull request.


## 📝 Licencia

Licencia MIT.


> *Hecho con cariño, Python y ganas de ahorrar 🇨🇱*


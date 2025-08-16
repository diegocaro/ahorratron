# Ahorratrón

<div align="center">
  <img src="images/ahorratron.png" alt="Ahorratrón - El chanchito que automatiza tus finanzas" width="300">
</div>

> 🐷💾 El chanchito que automatiza tus finanzas

**Ahorratrón** es una herramienta en Python para ayudarte a organizar, convertir y analizar tus datos financieros, especialmente diseñada para procesar cartolas bancarias y de tarjetas de crédito de forma eficiente.

Inspirada en los tradicionales chanchitos de ahorro, esta herramienta busca facilitar el control de gastos, fomentar el ahorro y ayudarte a tomar el control de tus finanzas personales (o familiares).

La herramienta combina tres componentes principales:
- 🔗 **[API de Sincronización](ahorratron/sync_api/README.md)**: Conecta en tiempo real con tu banco 
- 🏦 **[Integración con Actual Budget](ahorratron/actual_api/README.md)**: Se conecta directamente con tu aplicación de presupuesto favorita
- 🔄 **[Conversor](ahorratron/conversor/README.md)**: Transforma cartolas bancarias a formatos compatibles (solo Banco de Chile)

---

## 🏦 Bancos Soportados

Actualmente, Ahorratrón está optimizado para el **Banco de Chile**, incluyendo:

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

En Actual Budget, podrás configurar la sincronización bancaria usando Pluggy.ai, que se conectará automáticamente con tu servidor local de Ahorratrón.



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

**Descargar cartola del banco y convertir directamente:**
```bash
# Configurar credenciales
export BANK_USER=11111111-1
export BANK_PASSWORD=TuPassword
export BANK_URL=https://banco.cl

# Descargar y convertir
bank-statement --account cte | convert-to-actual -o cartola.csv
```

---

## 🛡️ Seguridad y Privacidad

- **Datos locales**: Todas tus credenciales y datos financieros permanecen en tu servidor
- **Sin terceros**: No dependes de servicios externos como Pluggy.ai  
- **Código abierto**: Puedes auditar y modificar el código según tus necesidades
- **Comunicación encriptada**: Todas las conexiones usan HTTPS/SSL

---

## Contribuciones

¡Las contribuciones son bienvenidas! Si tienes ideas para mejorar Ahorratrón o quieres agregar soporte para otros bancos, no dudes en crear un issue o enviar un pull request.

---

## 📝 Licencia

Licencia MIT.

---

> *Hecho con cariño, Python y ganas de ahorrar 🇨🇱*


# Ahorratrón
> 🐷💾 El chanchito que automatiza tus finanzas

**Ahorratrón** es una herramienta en Python para ayudarte a organizar, convertir y analizar tus datos financieros, especialmente diseñada para procesar cartolas bancarias y de tarjetas de crédito de forma eficiente.

Inspirada en los tradicionales chanchitos de ahorro, esta herramienta busca facilitar el control de gastos, fomentar el ahorro y ayudarte a tomar el control de tus finanzas personales (o familiares).

---

## ✨ Características

- Analiza y convierte cartolas bancarias o de tarjetas (TXT, CSV, XLS).
- Interfaz de línea de comandos (CLI) para exportar datos al formato de [Actual Budget](https://actualbudget.com/).
- Definiciones de campos extensibles para soportar distintos bancos.
- Pensado para facilitar el ahorro, saldar deudas y alcanzar metas financieras.

---

## ⚙️ Instalación


Requiere Python 3.12 o superior.

Clona el repositorio e instala las dependencias usando [uv](https://github.com/astral-sh/uv):

```bash
git clone git@github.com:diegocaro/ahorratron.git
cd ahorratron
uv sync
```

Para desarrollo (con herramientas de prueba):

```bash
uv sync --dev
```

---

## 🚀 Uso

La herramienta principal es `convert-to-actual`, que convierte tus cartolas al formato compatible con Actual Budget:

```bash
convert-to-actual <archivo_entrada> [opciones]
```

Ejemplo:

```bash
convert-to-actual cartola.txt
```

### 📄 Obtener cartola bancaria del Banco de Chile

También puedes usar el comando `bank-statement` para obtener la cartola bancaria de cuentas corrientes y cuentas vista del Banco de Chile:

```bash
bank-statement [opciones]
```

Este comando descarga y procesa la cartola directamente desde el sitio del banco. El resultado se entrega en formato TXT.

> **Nota:** Para usar este comando, debes exportar las siguientes variables de entorno antes de ejecutarlo (WIP, por ahora no es el mejor método para dejar las credenciales, se aceptan parches):
>
> ```bash
> export BANK_USER=11111111-1
> export BANK_PASSWORD=TuPassword
> export BANK_URL=https://portalpersonas.bancochile.cl/persona/
> ```

### 🏦 Selección de cuenta bancaria

El comando `bank-statement` permite elegir la cuenta desde la cual descargar la cartola, usando la opción `--account`:

```bash
bank-statement --account cte   # Para cuenta corriente
bank-statement --account fan   # Para Cuenta FAN (por defecto)
```

El script busca las cartolas que aparecen bajo el widget que contiene los links a las cuentas bancarias en el sitio del Banco de Chile. Los identificadores de los botones están definidos en la variable `BANK_ACCOUNT_BUTTONS_ID` del script.

### 🔄 Convertir cartola bancaria a formato CSV para Actual Budget

Puedes ejecutar ambos comandos en conjunto para descargar la cartola en formato TXT y convertirla automáticamente al formato CSV que puede importarse en Actual Budget:

```bash
bank-statement | convert-to-actual -o cartola.csv
```

Esto permite automatizar el proceso completo: desde la obtención de la cartola bancaria hasta la generación del archivo CSV listo para importar.

---

## 🏦 Bancos soportados

Por ahora, solo está implementado:

- Banco de Chile

---

## 🗂️ Estructura del proyecto

* `ahorratron/` – Paquete principal
  * `cli/convert_to_actual.py` – Punto de entrada CLI
  * `parsers/` – Parsers para distintos formatos de archivo
  * `field_definitions/` – Definiciones de campos por banco
* `tests/` – Pruebas unitarias

---

## 🧪 Desarrollo

Para ejecutar los tests:

```bash
pytest
```

---

## 📝 Licencia

Licencia MIT. (Agrega aquí tus datos de autoría o archivo LICENSE si corresponde)

---

> *Hecho con cariño, Python y ganas de ahorrar 🇨🇱*


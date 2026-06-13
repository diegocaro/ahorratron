import logging
import os
import platform
import random
import time
from typing import Any, ClassVar

import httpx
import selenium.common.exceptions as selenium_exceptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ahorratron.sync_api.institutions.banco_de_chile.models import (
    CuentaAhorroRequest,
    CuentaAhorroResponse,
    FechasFacturacionResponse,
    GetCartolaCuentaRequest,
    GetCartolaResponse,
    GetSaldoResponse,
    MovimientosNoFacturadosRequest,
    NoFacturadosResponse,
    ObtenerProductosResponse,
    ResumenNacionalResponse,
    ResumenPorFechaRequest,
)

BANK_LOGIN_URL = os.environ["BANK_LOGIN_URL"]
BANK_API_BASE_URL = os.environ["BANK_API_BASE_URL"].rstrip("/")

HEADER_REFERER = os.environ["HEADER_REFERER"]
HEADER_ORIGIN = os.environ["HEADER_ORIGIN"]

logger = logging.getLogger(__name__)

type CookieDict = dict[str, str]


def random_wait(min_seconds: float = 1, max_seconds: float = 3) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))


class LoginError(Exception):
    """Custom exception for login errors. You should not retry if this is raised."""

    pass


class APIClient:
    """
    Note: if you ever use this class in a thread, or update the code to be async,
    make sure to handle the creation of the browser - selenium driver - properly.

    Otherwise, you might end up with multiple browser instances running in parallel,
    which can lead to unexpected behavior and resource exhaustion.


    """

    SESSION_COOKIE_NAMES: ClassVar[list[str]] = ["mod_auth_openidc_session"]
    BASE_URL = BANK_API_BASE_URL
    LOGIN_URL = BANK_LOGIN_URL

    INPUT_RUT_ID = "ppriv_per-login-click-input-rut"
    INPUT_PASSWORD_ID = "ppriv_per-login-click-input-password"
    BUTTON_LOGIN_ID = "ppriv_per-login-click-ingresar-login"
    TIMEOUT_SECONDS = 30

    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password

        self._session = None

    def _parse_session_cookies(self, cookies: list[CookieDict]) -> str:
        session_cookie = {
            c["name"]: c["value"]
            for c in cookies
            if c["name"] in self.SESSION_COOKIE_NAMES
        }
        diff = set(self.SESSION_COOKIE_NAMES) - set(session_cookie.keys())
        if diff:
            raise ValueError(f"Missing session cookie names: {diff}")

        pairs = [f"{name}={value};" for name, value in session_cookie.items()]
        return " ".join(pairs)

    @property
    def session(self) -> httpx.Client:
        if self._session is None:
            logger.info("Logging in to Banco de Chile to get session cookies")
            cookie_raw = self._login_and_cookies()
            cookie = self._parse_session_cookies(cookie_raw)

            s = httpx.Client(
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Referer": HEADER_REFERER,
                    "Content-Type": "application/json",
                    "Origin": HEADER_ORIGIN,
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Cookie": cookie,
                }
            )
            self._session = s
        return self._session

    def _handle_response(self, response: httpx.Response) -> Any:
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if response.status_code == 302:
                self._session = None
                logger.info("Session expired, re-logging in")
                raise ValueError("Session expired, please re-login") from e
            logger.error(f"HTTP error occurred: {e}")
            raise

    def _login_and_cookies(self) -> list[CookieDict]:
        """
        Automate browser to log in and return session cookies.

        Note: you can end up with multiple browser instances running in parallel
            if you use this class in a thread or async context.
        """
        chrome_options = Options()
        # chrome_options.add_argument("--window-size=1920,1080")

        if platform.system().lower() == "linux":
            # Use remote Selenium server (Docker Compose service name: selenium)
            driver = webdriver.Remote(
                command_executor="http://selenium:4444/wd/hub", options=chrome_options
            )
        else:
            # Use local Chrome WebDriver (macOS)
            driver = webdriver.Chrome(options=chrome_options)

        try:
            cookies = self._login_via_browser(
                driver, self.LOGIN_URL, self._username, self._password
            )
            logger.debug(f"Cookies from Selenium: {cookies}")
        except Exception as e:
            raise ValueError(f"Login failed: {e}") from e
        finally:
            driver.quit()
        return cookies

    def _login_via_browser(
        self,
        driver: webdriver.Chrome | webdriver.Remote,
        bank_url: str,
        username: str,
        password: str,
    ) -> list[CookieDict]:
        home_button_id = "1"

        try:
            driver.get(bank_url)
            wait = WebDriverWait(driver, self.TIMEOUT_SECONDS)

            # Wait for login fields to be present
            wait.until(EC.presence_of_element_located((By.ID, self.INPUT_RUT_ID)))
            wait.until(EC.presence_of_element_located((By.ID, self.INPUT_PASSWORD_ID)))
        except Exception as e:
            raise ValueError(f"Error loading login page: {e}") from e

        try:
            # Fill in credentials and submit
            driver.find_element(By.ID, self.INPUT_RUT_ID).send_keys(username)
            random_wait()
            driver.find_element(By.ID, self.INPUT_PASSWORD_ID).send_keys(password)
            random_wait()
            driver.find_element(By.ID, self.BUTTON_LOGIN_ID).click()

            # Wait for Home button to be clickable after login
            wait.until(EC.presence_of_element_located((By.ID, home_button_id)))
            # random_wait()

            cookies = driver.get_cookies()
        except selenium_exceptions.TimeoutException:
            raise LoginError(
                "Login timed out, check your credentials or network connection"
            )
        except Exception as e:
            raise ValueError(f"Login failed: {e}") from e

        # Return session cookies
        return cookies

    def get_productos(self, incluirTarjetas: bool = True) -> ObtenerProductosResponse:
        url = f"{self.BASE_URL}/selectorproductos/selectorProductos/obtenerProductos"
        params = {"incluirTarjetas": incluirTarjetas}
        response = self.session.get(url, params=params)
        parsed = self._handle_response(response)
        return ObtenerProductosResponse.model_validate(parsed)

    def get_no_facturados(
        self, data: MovimientosNoFacturadosRequest
    ) -> NoFacturadosResponse:
        url = f"{self.BASE_URL}/tarjeta-credito-digital/movimientos-no-facturados"

        response = self.session.post(url, json=data.model_dump())
        parsed = self._handle_response(response)
        logger.debug(f"Raw No facturados raw response: {parsed}")
        return NoFacturadosResponse.model_validate(parsed)

    def get_cartola(self, data: GetCartolaCuentaRequest) -> GetCartolaResponse:
        url = f"{self.BASE_URL}/bff-pper-prd-cta-movimientos/movimientos/getCartola"

        response = self.session.post(url, json=data.model_dump())
        parsed = self._handle_response(response)
        return GetCartolaResponse.model_validate(parsed)

    def get_saldo(self, data: MovimientosNoFacturadosRequest) -> GetSaldoResponse:
        url = f"{self.BASE_URL}/tarjeta-credito-digital/saldo/obtener-saldo"
        response = self.session.post(url, json=data.model_dump())
        parsed = self._handle_response(response)
        return GetSaldoResponse.model_validate(parsed)

    def get_fechas_facturacion(
        self, data: MovimientosNoFacturadosRequest
    ) -> FechasFacturacionResponse:
        url = f"{self.BASE_URL}/tarjetas/estadocuenta/fechas-facturacion"
        response = self.session.post(url, json=data.model_dump())
        parsed = self._handle_response(response)
        return FechasFacturacionResponse.model_validate(parsed)

    def get_resumen_nacional(
        self, data: ResumenPorFechaRequest
    ) -> ResumenNacionalResponse:
        url = f"{self.BASE_URL}/tarjetas/estadocuenta/nacional/resumen-por-fecha"
        response = self.session.post(url, json=data.model_dump())
        parsed = self._handle_response(response)
        return ResumenNacionalResponse.model_validate(parsed)

    def get_cuenta_ahorro(self, data: CuentaAhorroRequest) -> CuentaAhorroResponse:
        url = f"{self.BASE_URL}/movimientos/getMovimientosCuentaAhorro"
        response = self.session.post(url, json=data.model_dump())
        parsed = self._handle_response(response)
        return CuentaAhorroResponse.model_validate(parsed)


def main():
    from pathlib import Path

    BANK_USER = os.environ["BANK_USER"]
    BANK_PASSWORD = os.environ["BANK_PASSWORD"]

    client = APIClient(BANK_USER, BANK_PASSWORD)
    productos = client.get_productos()
    # open("productos.json", "w").write(json.dumps(productos, indent=4))
    # no_facturados = client.get_no_facturados()
    # open("no_facturados.json", "w").write(json.dumps(no_facturados, indent=4))
    # cartola = client.get_cartola()
    # open("cartola.json", "w").write(json.dumps(cartola, indent=4))

    # productos_con_cartola = [
    #     c
    #     for c in productos.productos
    #     if c.tipo == "cuenta" and c.claseCuenta in ["CCNMN1", "VTACNN"]
    # ]

    # for cuenta in productos_con_cartola:
    #     print(f"Cuenta: {cuenta.numero} - {cuenta.mascara}")
    #     data = {
    #         "cuentaSeleccionada": {
    #             "nombreCliente": productos.nombre,
    #             "rutCliente": productos.rut,
    #             "numero": cuenta.numero,
    #             "mascara": cuenta.mascara,
    #             # "selected": True, # Opcional
    #             "codigoProducto": cuenta.codigo,
    #             "claseCuenta": cuenta.claseCuenta,
    #             "moneda": cuenta.codigoMoneda,
    #         },
    #         "cabecera": {"statusGenerico": True, "paginacionDesde": 1},
    #     }
    #     request = GetCartolaCuentaRequest.model_validate(data)
    #     cartola = client.get_cartola(request)
    #     print(cartola)

    tarjetas_de_credito = [c for c in productos.productos if c.tipo == "tarjeta"]
    # for tarjeta in tarjetas_de_credito:
    #     print(f"Tarjeta: {tarjeta.numero} - {tarjeta.mascara}")
    #     data = {
    #         "idTarjeta": tarjeta.id,
    #         "codigoProducto": tarjeta.codigo,
    #         "tipoTarjeta": tarjeta.descripcionLogo,
    #         "mascara": tarjeta.mascara,
    #         "nombreTitular": tarjeta.tarjetaHabiente,
    #         "tipoCliente": tarjeta.tipoCliente,
    #     }
    #     request = MovimientosNoFacturadosRequest.model_validate(data)
    #     no_facturados = client.get_no_facturados(request)
    #     print(no_facturados)

    tarjeta = tarjetas_de_credito[1]
    print(f"Tarjeta: {tarjeta.numero} - {tarjeta.mascara}")
    data = {
        "idTarjeta": tarjeta.id,
        "codigoProducto": tarjeta.codigo,
        "tipoTarjeta": tarjeta.descripcionLogo,
        "mascara": tarjeta.mascara,
        "nombreTitular": tarjeta.tarjetaHabiente,
        "tipoCliente": tarjeta.tipoCliente,
    }

    tmp_dir = Path(__file__).parents[4] / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    request = MovimientosNoFacturadosRequest.model_validate(data)
    no_facturados = client.get_no_facturados(request)
    with open(tmp_dir / "no_facturados.json", "w") as f:
        f.write(no_facturados.model_dump_json(indent=2))

    request = MovimientosNoFacturadosRequest.model_validate(data)
    fechas_facturacion = client.get_fechas_facturacion(request)
    # print(fechas_facturacion)
    with open(tmp_dir / "fechas_facturacion.json", "w") as f:
        f.write(fechas_facturacion.model_dump_json(indent=2))

    mes_mas_reciente = max(
        e.fechaFacturacion for e in fechas_facturacion.listaNacional
    ).isoformat()

    data = {
        "idTarjeta": tarjeta.id,
        "codigoProducto": tarjeta.codigo,
        "tipoTarjeta": tarjeta.descripcionLogo,
        "mascara": tarjeta.mascara,
        "nombreTitular": tarjeta.tarjetaHabiente,
        # "tipoCliente": tarjeta.tipoCliente,
        "fechaFacturacion": mes_mas_reciente,
        "numeroCuenta": fechas_facturacion.numeroCuenta,
    }
    request = ResumenPorFechaRequest.model_validate(data)
    resumen_nacional_data = client.get_resumen_nacional(request)
    # print(resumen_nacional_data)
    with open(tmp_dir / "resumen_nacional.json", "w") as f:
        f.write(resumen_nacional_data.model_dump_json(indent=2))

    # random_wait()
    # no_facturados = client.get_no_facturados()
    # print(no_facturados)
    # start_time = time.time()
    # for i in range(10):
    #     time_to_wait = i**2
    #     print(f"Waiting for {time_to_wait} seconds...")
    #     time.sleep(time_to_wait)
    #     try:
    #         print(client.get_productos())
    #     except Exception as e:
    #         print(f"Error fetching productos at time {time.time() - start_time}: {e}")
    #         break


if __name__ == "__main__":
    main()
    # test_cartola = json.loads(open("cartola.json").read())
    # cartola = GetCartolaResponse.model_validate(test_cartola)

    # test_productos = json.loads(open("productos_raw.json").read())
    # productos = ObtenerProductosResponse.model_validate(test_productos)

    # test_no_facturados = json.loads(open("no_facturados.json").read())
    # no_facturados = NoFacturadosResponse.model_validate(test_no_facturados)

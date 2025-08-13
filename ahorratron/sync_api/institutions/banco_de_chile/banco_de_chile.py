import logging
import os
import platform
import random
import time

import httpx
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ahorratron.sync_api.institutions.banco_de_chile.models import (
    GetCartolaCuentaRequest,
    GetCartolaResponse,
    MovimientosNoFacturadosRequest,
    NoFacturadosResponse,
    ObtenerProductosResponse,
)

BANK_LOGIN_URL = os.environ["BANK_LOGIN_URL"]
BANK_API_BASE_URL = os.environ["BANK_API_BASE_URL"]

HEADER_REFERER = os.environ["HEADER_REFERER"]
HEADER_ORIGIN = os.environ["HEADER_ORIGIN"]

logger = logging.getLogger(__name__)


def random_wait(min_seconds: float = 1, max_seconds: float = 3) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))


class APIClient:
    SESSION_COOKIE_NAMES = ["mod_auth_openidc_session"]
    BASE_URL = BANK_API_BASE_URL
    LOGIN_URL = BANK_LOGIN_URL

    INPUT_RUT_ID = "ppriv_per-login-click-input-rut"
    INPUT_PASSWORD_ID = "ppriv_per-login-click-input-password"
    BUTTON_LOGIN_ID = "ppriv_per-login-click-ingresar-login"
    TIMEOUT_SECONDS = 30

    def __init__(self):
        self.session = httpx.Client(
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
            }
        )
        # This will be used to get the session cookie after login
        # self.session.headers["Cookie"] = self._get_session_cookie(cookies)

    def _get_session_cookie(self, cookies: list[dict[str, str]]) -> str:
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

    def _set_session_cookie(self, cookies: list[dict[str, str]]) -> None:
        session_cookie = self._get_session_cookie(cookies)
        self.session.headers["Cookie"] = session_cookie
        logger.debug(f"Session cookie set: {session_cookie}")

    def _handle_response(self, response: httpx.Response) -> dict:
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error occurred: {e}")
            raise

    def login(self, username: str, password: str) -> None:
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
            cookies = self._login_to_bank(driver, self.LOGIN_URL, username, password)
            logger.debug(f"Cookies from Selenium: {cookies}")
            self._set_session_cookie(cookies)
        finally:
            driver.quit()

    def _login_to_bank(
        self,
        driver: webdriver.Chrome | webdriver.Remote,
        bank_url: str,
        username: str,
        password: str,
    ) -> list[dict[str, str]]:
        home_button_id = "1"

        try:
            driver.get(bank_url)
            wait = WebDriverWait(driver, self.TIMEOUT_SECONDS)

            # Wait for login fields to be present
            wait.until(EC.presence_of_element_located((By.ID, self.INPUT_RUT_ID)))
            wait.until(EC.presence_of_element_located((By.ID, self.INPUT_PASSWORD_ID)))

            # Fill in credentials and submit
            driver.find_element(By.ID, self.INPUT_RUT_ID).send_keys(username)
            random_wait()
            driver.find_element(By.ID, self.INPUT_PASSWORD_ID).send_keys(password)
            random_wait()
            driver.find_element(By.ID, self.BUTTON_LOGIN_ID).click()

            # Wait for Home button to be clickable after login
            wait.until(EC.presence_of_element_located((By.ID, home_button_id)))
            random_wait()

            cookies = driver.get_cookies()
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
        return NoFacturadosResponse.model_validate(parsed)

    def get_cartola(self, data: GetCartolaCuentaRequest) -> GetCartolaResponse:
        url = f"{self.BASE_URL}/bff-pper-prd-cta-movimientos/movimientos/getCartola"

        response = self.session.post(url, json=data.model_dump())
        parsed = self._handle_response(response)
        return GetCartolaResponse.model_validate(parsed)


def main():
    BANK_USER = os.environ["BANK_USER"]
    BANK_PASSWORD = os.environ["BANK_PASSWORD"]

    client = APIClient()
    client.login(BANK_USER, BANK_PASSWORD)
    productos = client.get_productos()
    # open("productos.json", "w").write(json.dumps(productos, indent=4))
    # no_facturados = client.get_no_facturados()
    # open("no_facturados.json", "w").write(json.dumps(no_facturados, indent=4))
    # cartola = client.get_cartola()
    # open("cartola.json", "w").write(json.dumps(cartola, indent=4))

    productos_con_cartola = [
        c
        for c in productos.productos
        if c.tipo == "cuenta" and c.claseCuenta in ["CCNMN1", "VTACNN"]
    ]

    for cuenta in productos_con_cartola:
        print(f"Cuenta: {cuenta.numero} - {cuenta.mascara}")
        data = {
            "cuentaSeleccionada": {
                "nombreCliente": productos.nombre,
                "rutCliente": productos.rut,
                "numero": cuenta.numero,
                "mascara": cuenta.mascara,
                # "selected": True, # Opcional
                "codigoProducto": cuenta.codigo,
                "claseCuenta": cuenta.claseCuenta,
                "moneda": cuenta.codigoMoneda,
            },
            "cabecera": {"statusGenerico": True, "paginacionDesde": 1},
        }
        request = GetCartolaCuentaRequest.model_validate(data)
        cartola = client.get_cartola(request)
        print(cartola)

    tarjetas_de_credito = [c for c in productos.productos if c.tipo == "tarjeta"]
    for tarjeta in tarjetas_de_credito:
        print(f"Tarjeta: {tarjeta.numero} - {tarjeta.mascara}")
        data = {
            "idTarjeta": tarjeta.id,
            "codigoProducto": tarjeta.codigo,
            "tipoTarjeta": tarjeta.descripcionLogo,
            "mascara": tarjeta.mascara,
            "nombreTitular": tarjeta.tarjetaHabiente,
            "tipoCliente": tarjeta.tipoCliente,
        }
        request = MovimientosNoFacturadosRequest.model_validate(data)
        no_facturados = client.get_no_facturados(request)
        print(no_facturados)
    # random_wait()
    # no_facturados = client.get_no_facturados()
    # print(no_facturados)


if __name__ == "__main__":
    main()
    # test_cartola = json.loads(open("cartola.json").read())
    # cartola = GetCartolaResponse.model_validate(test_cartola)

    # test_productos = json.loads(open("productos_raw.json").read())
    # productos = ObtenerProductosResponse.model_validate(test_productos)

    # test_no_facturados = json.loads(open("no_facturados.json").read())
    # no_facturados = NoFacturadosResponse.model_validate(test_no_facturados)

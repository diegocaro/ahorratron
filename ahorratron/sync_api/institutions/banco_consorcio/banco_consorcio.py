import base64
import json
import logging
import os
import platform
from typing import Any
from urllib.parse import quote, unquote, urlparse

import httpx
import selenium.common.exceptions as selenium_exceptions
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ahorratron.sync_api.core.exceptions import LoginError
from ahorratron.sync_api.institutions.banco_consorcio.models import (
    MovementsResponse,
    NoFacturadosResponse,
    ProductsResponse,
    ResumenCuentaResponse,
)
from ahorratron.sync_api.utils.helpers import random_wait

ENCRYPTION_KEY_32 = os.environ["CONSORCIO_ENC_KEY"].encode("utf-8")
ENCRYPTION_IV_16 = os.environ["CONSORCIO_ENC_IV"].encode("utf-8")

BANK_API_BASE_URL = os.environ["CONSORCIO_API_BASE_URL"].rstrip("/")
BANK_TC_API_BASE_URL = os.environ["CONSORCIO_TC_API_BASE_URL"].rstrip("/")
BANK_LOGIN_URL = os.environ["CONSORCIO_LOGIN_URL"]

HEADER_REFERER = os.environ["CONSORCIO_REFERER"]
HEADER_ORIGIN = os.environ["CONSORCIO_ORIGIN"]

logger = logging.getLogger(__name__)

type SessionStorage = dict[str, str]


def encrypt(data: Any) -> str:
    plaintext = json.dumps(data).encode("utf-8")

    cipher = AES.new(ENCRYPTION_KEY_32, AES.MODE_CBC, ENCRYPTION_IV_16)

    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
    return base64.b64encode(ciphertext).decode("utf-8")


def decrypt(ciphertext_b64: str) -> str:
    ciphertext = base64.b64decode(ciphertext_b64)

    cipher = AES.new(ENCRYPTION_KEY_32, AES.MODE_CBC, ENCRYPTION_IV_16)

    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return plaintext.decode("utf-8")


def decode_url(url: str) -> str:
    parsed = urlparse(url)
    last_segment = parsed.path.split("/")[-1]
    ans = unquote(last_segment)
    return decrypt(ans)


class BancoConsorcioAPI:
    BASE_URL = BANK_API_BASE_URL
    TC_API_BASE_URL = BANK_TC_API_BASE_URL
    LOGIN_URL = BANK_LOGIN_URL

    TIMEOUT_SECONDS = 30

    INPUT_RUT_ID = "input-rut"
    INPUT_PASSWORD_ID = "input-new-pass"
    BUTTON_LOGIN_ID = "btn-login"
    HOME_BUTTON_ID = "itemHeaderInicio"

    SESSION_TOKEN_KEY = "acTkn"

    def __init__(self, username: str, password: str):
        self._token: str | None = None
        self._session: httpx.Client | None = None

        self._username = username
        self._password = password

    def _login_via_browser(
        self,
        driver: webdriver.Chrome | webdriver.Remote,
        bank_url: str,
        username: str,
        password: str,
    ) -> list:
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
            wait.until(EC.presence_of_element_located((By.ID, self.HOME_BUTTON_ID)))
            # random_wait()

            session_storage = driver.execute_script(
                "return Object.entries(sessionStorage);"
            )

        except selenium_exceptions.TimeoutException:
            raise LoginError(
                "Login timed out, check your credentials or network connection"
            )
        except Exception as e:
            raise ValueError(f"Login failed: {e}") from e

        return session_storage

    def _login_and_session_storage(self) -> list:
        """
        Automate browser to log in and return session storage.

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
            session_storage = self._login_via_browser(
                driver, self.LOGIN_URL, self._username, self._password
            )
            logger.debug(f"Session storage from Selenium: {session_storage}")
        except Exception as e:
            raise ValueError(f"Login failed: {e}") from e
        finally:
            driver.quit()
        return session_storage

    def _parse_session_storage(self, session_storage: list) -> dict[str, str]:
        return {key: value for key, value in session_storage}

    @property
    def session(self) -> httpx.Client:
        if self._session is None:
            logger.info("Logging in to Banco Consorcio")

            storage_raw = self._login_and_session_storage()
            storage = self._parse_session_storage(storage_raw)
            self._token = storage[self.SESSION_TOKEN_KEY]

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
                    "Authorization": f"Bearer {self._token}",
                }
            )
            self._session = s
        return self._session

    def _decrypt_response(self, response: httpx.Response) -> str:
        data = response.json()
        ciphertext_b64 = data.get("encryptedData")
        if not ciphertext_b64:
            logger.warning("No encryptedData found in response, returning raw data")
            return data
        return decrypt(ciphertext_b64)

    def _handle_response(self, response: httpx.Response, decrypt: bool = True) -> Any:
        try:
            response.raise_for_status()
            decrypted = self._decrypt_response(response) if decrypt else response.text
            return json.loads(decrypted)
        except httpx.HTTPStatusError as e:
            if response.status_code == 302:
                self._session = None
                logger.info("Session expired, re-logging in")
                raise ValueError("Session expired, please re-login") from e
            logger.error(f"HTTP error occurred: {e}")
            logger.error(f"Response content: {response.text}")
            raise

    def _encrypt_param(self, param: str) -> str:
        # assert isinstance(param, str)

        return quote(encrypt(param), safe="")

    def get_products(self) -> ProductsResponse:
        url = f"{self.BASE_URL}/products/list"
        response = self.session.get(url)
        key_account = response.headers["key-account"]
        decoded = self._handle_response(response)
        decoded["key_account"] = key_account
        return ProductsResponse.model_validate(decoded)

    def get_movements(self, account_id: str) -> MovementsResponse:
        if isinstance(account_id, int):
            account_id = str(account_id)
        encrypted_account_id = self._encrypt_param(account_id)
        url = f"{self.BASE_URL}/movements/account/{encrypted_account_id}"
        response = self.session.get(url)
        decoded = self._handle_response(response)
        return MovementsResponse.model_validate(decoded)

    def get_resumen(self, account_id: str, key_account: str) -> ResumenCuentaResponse:
        if isinstance(account_id, str):
            account_id = int(account_id)  # type: ignore
        encrypted_account_id = self._encrypt_param(account_id)
        url = f"{self.BASE_URL}/summaries/account/{encrypted_account_id}"
        response = self.session.get(url, headers={"key-account": key_account})
        decoded = self._handle_response(response)
        return ResumenCuentaResponse.model_validate(decoded)

    def get_no_facturados(self) -> NoFacturadosResponse:
        url = f"{self.TC_API_BASE_URL}/credit-cards/unbilled-movements"
        response = self.session.post(url)
        ans = self._handle_response(response, decrypt=False)
        return NoFacturadosResponse.model_validate(ans)


def main():
    BANK_USER = os.environ["CONSORCIO_USER"]
    BANK_PASSWORD = os.environ["CONSORCIO_PASSWORD"]

    client = BancoConsorcioAPI(BANK_USER, BANK_PASSWORD)
    products = client.get_products()
    print(products)
    movements = client.get_movements("4310529244")
    print(movements)
    no_facturados = client.get_no_facturados()
    print(no_facturados)


if __name__ == "__main__":
    main()

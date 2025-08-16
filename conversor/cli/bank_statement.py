import argparse
import glob
import os
import random
import shutil
import tempfile
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BANK_LOGIN_URL = os.environ["BANK_LOGIN_URL"]
BANK_USER = os.environ["BANK_USER"]
BANK_PASSWORD = os.environ["BANK_PASSWORD"]

BANK_ACCOUNT_BUTTONS_ID = {
    # These are the IDs for the account buttons on the Banco de Chile website
    # They may change, so ensure they are correct.
    "cte": "btn-home_CuentaCorrienteMonedaLocal",
    "fan": "btn-home_CuentaFAN",
}

INPUT_RUT_ID = "ppriv_per-login-click-input-rut"
INPUT_PASSWORD_ID = "ppriv_per-login-click-input-password"
BUTTON_LOGIN_ID = "ppriv_per-login-click-ingresar-login"


def random_wait(min_seconds: float = 1, max_seconds: float = 3) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))


def wait_for_txt_file(
    download_dir: str, timeout: float = 10, poll_interval: float = 0.5
) -> str:
    """Wait for the first .txt file to appear in the directory and return its path."""
    waited = 0.0
    while waited < timeout:
        txt_files = glob.glob(os.path.join(download_dir, "*.txt"))
        if txt_files:
            return txt_files[0]
        time.sleep(poll_interval)
        waited += poll_interval
    raise FileNotFoundError(
        f"No .txt file downloaded after {timeout} seconds in {download_dir}"
    )


def close_emergent_modal(driver: webdriver.Chrome) -> None:
    try:
        close_btn = driver.find_element(
            By.CSS_SELECTOR, "button[onclick*='modal_emergente_close']"
        )
        close_btn.click()
        random_wait()
    except NoSuchElementException:
        pass  # Modal did not appear, continue


def download_cartola_txt(account_button_id: str) -> str:
    """Automate browser to download cartola.txt and return its contents."""
    download_dir = tempfile.mkdtemp()
    chrome_options = Options()
    chrome_options.add_experimental_option(  # type: ignore
        "prefs",
        {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        },
    )
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(BANK_LOGIN_URL)
        wait = WebDriverWait(driver, 20)

        # Wait for login fields to be present
        wait.until(EC.presence_of_element_located((By.ID, INPUT_RUT_ID)))
        random_wait()
        wait.until(EC.presence_of_element_located((By.ID, INPUT_PASSWORD_ID)))
        random_wait()

        # Fill in RUT and password
        driver.find_element(By.ID, INPUT_RUT_ID).send_keys(BANK_USER)
        driver.find_element(By.ID, INPUT_PASSWORD_ID).send_keys(BANK_PASSWORD)
        driver.find_element(By.ID, BUTTON_LOGIN_ID).click()

        # Wait for "Cuenta FAN" button to be clickable after login
        wait.until(EC.presence_of_element_located((By.ID, account_button_id)))
        close_emergent_modal(driver)
        wait.until(EC.element_to_be_clickable((By.ID, account_button_id))).click()
        random_wait()

        # Wait for "Descargar" button (parent of span.btn-text)
        descargar_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//span[contains(@class, 'btn-text') and text()='Descargar']/..",
                )
            )
        )
        random_wait()
        descargar_btn.click()
        # Wait for "Descargar Txt" button in the dropdown
        descargar_txt_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(@class, 'bch-button-dropdown-menu-item') and contains(., 'Descargar Txt')]",
                )
            )
        )
        random_wait()
        descargar_txt_btn.click()
        filepath = wait_for_txt_file(download_dir)
        with open(filepath, encoding="utf8") as f:
            return f.read()
    finally:
        driver.quit()
        shutil.rmtree(download_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(
        description="Download Banco de Chile cartola.txt and write to file or stdout."
    )
    parser.add_argument(
        "--output",
        "-o",
        default="-",
        help="Output TXT file name or '-' for stdout (default: '-')",
    )
    parser.add_argument(
        "--account",
        "-a",
        choices=BANK_ACCOUNT_BUTTONS_ID.keys(),
        default="fan",
        help="Select the bank account type (default: 'fan')",
    )
    args = parser.parse_args()

    account_id = BANK_ACCOUNT_BUTTONS_ID.get(args.account)
    if not account_id:
        raise ValueError(
            f"Invalid account type: {args.account}. "
            f"Available options: {', '.join(BANK_ACCOUNT_BUTTONS_ID.keys())}"
        )
    content = download_cartola_txt(account_id)
    if args.output == "-":
        print(content)
    else:
        with open(args.output, "w", encoding="utf8") as f:
            f.write(content)


if __name__ == "__main__":
    main()

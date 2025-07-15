import os
import tempfile
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Set up the driver (update the path to your chromedriver)
BANK_URL = os.environ["BANK_URL"]
BANK_USER = os.environ["BANK_USER"]
BANK_PASSWORD = os.environ["BANK_PASSWORD"]

download_dir = tempfile.mkdtemp()

chrome_options = Options()
chrome_options.add_experimental_option(
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
    driver.get(BANK_URL)
    wait = WebDriverWait(driver, 20)
    # Wait for login fields to be present
    wait.until(EC.presence_of_element_located((By.ID, "ppriv_per-click-input-rut")))
    wait.until(
        EC.presence_of_element_located((By.ID, "ppriv_per-click-input-password"))
    )
    # Fill in RUT and password
    driver.find_element(By.ID, "ppriv_per-click-input-rut").send_keys(BANK_USER)
    driver.find_element(By.ID, "ppriv_per-click-input-password").send_keys(
        BANK_PASSWORD
    )
    driver.find_element(By.ID, "ppriv_per-click-ingresar-login").click()

    # Wait for "Cuenta FAN" button to be clickable after login
    wait.until(EC.element_to_be_clickable((By.ID, "btn-home_CuentaFAN"))).click()

    # Wait for "Descargar" button (parent of span.btn-text)
    descargar_btn = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//span[contains(@class, 'btn-text') and text()='Descargar']/..",
            )
        )
    )
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
    descargar_txt_btn.click()

    # Wait for the file to be downloaded
    filepath = os.path.join(download_dir, "cartola.txt")
    timeout = 10  # seconds
    poll_interval = 0.5
    waited = 0
    while not os.path.exists(filepath) and waited < timeout:
        time.sleep(poll_interval)
        waited += poll_interval
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"File not downloaded after {timeout} seconds: {filepath}"
        )
    print(open(filepath, "r").read())


finally:
    driver.quit()

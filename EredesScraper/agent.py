import datetime
import os
import time
from pathlib import Path
from sys import platform

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from webdriver_manager.chrome import ChromeDriverManager

# package imports
from EredesScraper.utils import wait_for_download, parse_config, save_screenshot

config = parse_config(Path.cwd() / 'config.yml')  # TODO: parametrize this


class ScraperFlowError(Exception):
    pass


class EredesScraper:
    def __init__(self, nif=config['eredes']['nif'], password=config['eredes']['pwd'], cpe_code=config['eredes']['cpe']):
        self.dwnl_file = None
        self.driver = None
        self.chrome_options = webdriver.ChromeOptions()
        self.headless = True
        self.__nif = nif
        self.__password = password
        self.__cpe_code = cpe_code

        # Create a staging area for the ChromeDriver
        try:
            Path.mkdir(Path.cwd() / 'tmp', exist_ok=True)
        except PermissionError:
            print("Permission denied to create a staging area for the Scraper")

        dl_path = Path.cwd() / 'tmp'
        if platform == "linux" or platform == "linux2" or platform == "darwin":
            self.tmp = dl_path.as_posix()
        elif platform == "win32":
            self.tmp = dl_path.__str__()

    # define a setter method for the headless property
    @property
    def headless(self):
        return self.__headless

    @headless.setter
    def headless(self, value):
        if isinstance(value, bool):
            self.__headless = value
        else:
            raise TypeError("Expected a boolean value")

    # define a setter method for the nif property
    @property
    def nif(self):
        return self.__nif

    @nif.setter
    def nif(self, value):
        if isinstance(value, str):
            self.__nif = value
        else:
            raise TypeError("Expected a string value")

    # define a setter method for the password property
    @property
    def password(self):
        return self.__password

    @password.setter
    def password(self, value):
        if isinstance(value, str):
            self.__password = value
        else:
            raise TypeError("Expected a string value")

    # define a setter method for the cpe_code property
    @property
    def cpe_code(self):
        return self.__cpe_code

    @cpe_code.setter
    def cpe_code(self, value):
        if isinstance(value, str):
            self.__cpe_code = value
        else:
            raise TypeError("Expected a string value")

    def setup(self):
        self.chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 '
                                         '(KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36')

        prefs = {
            "download.default_directory": self.tmp,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        self.chrome_options.add_experimental_option("prefs", prefs)
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        if self.headless:
            self.chrome_options.add_argument("--headless=new")
            self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            self.chrome_options.add_argument('--disable-infobars')
            self.chrome_options.add_argument('--disable-dev-shm-usage')
            self.chrome_options.add_argument('--disable-browser-side-navigation')
            self.chrome_options.add_argument('--disable-gpu')
            self.chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            self.chrome_options.add_argument('--disable-extensions')
            self.chrome_options.add_argument('--no-sandbox')
            self.chrome_options.add_argument('--disable-notifications')
            self.chrome_options.add_argument('--disable-crash-reporter')
            self.chrome_options.add_argument('--disable-logging')
            self.chrome_options.add_argument('--disable-sync')

        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=self.chrome_options
        )

        self.driver.implicitly_wait(30)

    def teardown(self):
        self.driver.quit()

    def current_month_consumption(self):
        # Selenium flow
        # Step # | name | target | value | comment

        # 1 | open | /login |  |
        self.driver.get("https://balcaodigital.e-redes.pt/login")

        # 2 | click | css=.ant-typography > .item > .highlights |  |
        wait(self.driver, 30).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".ant-typography > .item > .highlights")
        )).click()

        # 3 | type | id=username |   |
        self.driver.find_element(By.ID, "username").send_keys(f"{self.__nif}")

        # 4 | type | id=labelPassword |  |
        self.driver.find_element(By.ID, "labelPassword").send_keys(f"{self.__password}")

        # 5 | click | css=.login-actions |  |
        self.driver.find_element(By.XPATH, "//span[contains(.,'Entrar')]").click()
        time.sleep(5)

        # 7 | click | css=.card__myplaces .card-text |  |
        wait(self.driver, 30).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".card__myplaces .card-text")
        )).click()

        # 8 | click | css=.card:nth-child(3) .highlights |  |
        wait(self.driver, 30).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".card:nth-child(3) .highlights")
        )).click()

        # 9 | click | css=.card:nth-child(1) > .item__title |  |
        wait(self.driver, 30).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".card:nth-child(1) > .item__title")
        )).click()

        # 10 | click | css=.list:nth-child(2) > .block:nth-child(1) .card-tags |  |
        wait(self.driver, 30).until(EC.presence_of_element_located(
            (By.XPATH, f"//*[contains(text(),'{self.__cpe_code}')]")
        )).click()

        time.sleep(30)
        try:
            element = self.driver.find_element(By.XPATH, "//strong[contains(text(), 'Exportar excel')]")
        except:
            save_screenshot(self.driver, "screenshot.png")
            raise ScraperFlowError("Failed to find the 'Exportar excel' element")

        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        element.click()

        wait_for_download(self.tmp, 30)

        current_date = datetime.datetime.now().strftime("%Y%m%d")
        assert f"Consumos_{current_date}.xlsx" in os.listdir(self.tmp), "Download failed"
        
        # store the downloaded file absolute path in a variable
        self.dwnl_file = Path(self.tmp) / f"Consumos_{current_date}.xlsx"
        
        return self.dwnl_file
        

import datetime
import os
import time
from pathlib import Path
from sys import platform

import typer
from dateutil.relativedelta import relativedelta
from rich.progress import Progress, SpinnerColumn, TextColumn
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from webdriver_manager.chrome import ChromeDriverManager

from eredesscraper.utils import wait_for_download, save_screenshot, map_month_matrix


class ScraperFlowError(Exception):
    pass


class EredesScraper:
    def __init__(self, nif, password, cpe_code):
        self.dwnl_file = None
        self.driver = None
        self.chrome_options = webdriver.ChromeOptions()
        self.headless = True
        self.__nif = nif
        self.__password = password
        self.__cpe_code = cpe_code
        self.__implicit_wait = 30

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

    @property
    def implicit_wait(self):
        return self.__implicit_wait

    @implicit_wait.setter
    def implicit_wait(self, value):
        if isinstance(value, int):
            self.__implicit_wait = value
        else:
            raise TypeError("Expected an integer value")

    @property
    def headless(self):
        return self.__headless

    @headless.setter
    def headless(self, value):
        if isinstance(value, bool):
            self.__headless = value
        else:
            raise TypeError("Expected a boolean value")

    @property
    def nif(self):
        return self.__nif

    @nif.setter
    def nif(self, value):
        if isinstance(value, str):
            self.__nif = value
        else:
            raise TypeError("Expected a string value")

    @property
    def password(self):
        return self.__password

    @password.setter
    def password(self, value):
        if isinstance(value, str):
            self.__password = value
        else:
            raise TypeError("Expected a string value")

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
            self.chrome_options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=self.chrome_options
        )

        self.driver.implicitly_wait(30)

    def teardown(self):
        self.driver.quit()

    def current_month(self):
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
        ) as progress:

            t1 = progress.add_task(description=" 🔐 Loging in...", total=None)

            self.driver.get("https://balcaodigital.e-redes.pt/login")

            wait(self.driver, 30).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".ant-typography > .item > .highlights")
            )).click()

            self.driver.find_element(By.ID, "username").send_keys(f"{self.__nif}")

            self.driver.find_element(By.ID, "labelPassword").send_keys(f"{self.__password}")

            self.driver.find_element(By.XPATH, "//span[contains(.,'Entrar')]").click()
            time.sleep(5)

            text = None
            try:
                alert = self.driver.find_element(By.CSS_SELECTOR,
                                                 "body > app-root > nz-layout > app-default > main > nz-content > div "
                                                 "> div.login__text.ant-col > section.login-actions > app-sign-in > "
                                                 "div > div > form > "
                                                 "nz-form-item.ant-form-item.ant-row.ng-star-inserted > nz-alert > "
                                                 "div > div > span")
                text = alert.text
            except Exception:
                pass
            finally:
                if text is not None and "Dados inválidos" in text:
                    save_screenshot(self.driver)
                    raise ScraperFlowError(
                        "🔐 Invalid Credentials!\nCheck your NIF and Password with `ers config show`.\n"
                        "A screenshot was saved in the current directory for debugging purposes.")

            wait(self.driver, 30).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".card__myplaces .card-text")
            )).click()

            progress.remove_task(t1)
            t2 = progress.add_task(description=" 💡 Finding your CPE...", total=None)

            wait(self.driver, 30).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".card:nth-child(3) .highlights")
            )).click()

            wait(self.driver, 30).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".card:nth-child(1) > .item__title")
            )).click()
            try:
                wait(self.driver, 30).until(EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(),'{self.__cpe_code}')]")
                )).click()
            except ScraperFlowError:
                save_screenshot(self.driver)
                raise ScraperFlowError(
                    "💥 Failed to find the CPE code. A screenshot was saved in the current directory for debugging "
                    "purposes")

            progress.remove_task(t2)
            t3 = progress.add_task(description=" 📊 Downloading your data...", total=None)

            time.sleep(30)
            try:
                element = self.driver.find_element(By.XPATH, "//strong[contains(text(), 'Exportar excel')]")
            except ScraperFlowError:
                save_screenshot(self.driver)
                raise ScraperFlowError("Failed to find the 'Exportar excel' element")

            self.driver.execute_script("arguments[0].scrollIntoView();", element)
            element.click()

            wait_for_download(self.tmp, 30)

            current_date = datetime.datetime.now().strftime("%Y%m%d")
            assert f"Consumos_{current_date}.xlsx" in os.listdir(self.tmp), "Download failed"

            self.dwnl_file = Path(self.tmp) / f"Consumos_{current_date}.xlsx"

        progress.remove_task(t3)
        typer.echo(f"📁\tDownloaded file: {self.dwnl_file}")

        return self.dwnl_file

    def last_month(self):
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
        ) as progress:

            prev_month = datetime.datetime.now() - relativedelta(months=1)
            row, col = map_month_matrix(prev_month)

            t1 = progress.add_task(description=" 🔐 Loging in...", total=None)

            self.driver.get("https://balcaodigital.e-redes.pt/login")

            wait(self.driver, 30).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".ant-typography > .item > .highlights")
            )).click()

            self.driver.find_element(By.ID, "username").send_keys(f"{self.__nif}")

            self.driver.find_element(By.ID, "labelPassword").send_keys(f"{self.__password}")

            self.driver.find_element(By.XPATH, "//span[contains(.,'Entrar')]").click()
            time.sleep(5)

            text = None
            try:
                alert = self.driver.find_element(By.CSS_SELECTOR,
                                                 "body > app-root > nz-layout > app-default > main > nz-content > div "
                                                 "> div.login__text.ant-col > section.login-actions > app-sign-in > "
                                                 "div > div > form > "
                                                 "nz-form-item.ant-form-item.ant-row.ng-star-inserted > nz-alert > "
                                                 "div > div > span")
                text = alert.text
            except Exception:
                pass
            finally:
                if text is not None and "Dados inválidos" in text:
                    save_screenshot(self.driver)
                    raise ScraperFlowError(
                        "🔐 Invalid Credentials!\nCheck your NIF and Password with `ers config show`.\nA screenshot "
                        "was saved in the current directory for debugging purposes.")

            wait(self.driver, 30).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".card__myplaces .card-text")
            )).click()

            progress.remove_task(t1)
            t2 = progress.add_task(description=" 💡 Finding your CPE...", total=None)

            wait(self.driver, 30).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".card:nth-child(3) .highlights")
            )).click()

            wait(self.driver, 30).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".card:nth-child(1) > .item__title")
            )).click()
            try:
                wait(self.driver, 30).until(EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(),'{self.__cpe_code}')]")
                )).click()
            except ScraperFlowError:
                save_screenshot(self.driver)
                raise ScraperFlowError(
                    "💥 Failed to find the CPE code. A screenshot was saved in the current directory for debugging "
                    "purposes")

            progress.remove_task(t2)
            t3 = progress.add_task(description=" 📊 Downloading your data...", total=None)

            time.sleep(15)

            self.driver.find_element(By.CSS_SELECTOR, ".ng-tns-c78-32 > .ng-untouched").click()

            time.sleep(15)

            try:
                wait(self.driver, 30).until(EC.presence_of_element_located(
                    (By.XPATH, f"//div[@id='cdk-overlay-4']/div/div/date-range-popup/div/div/div"
                                                   f"/inner-popup/div/div/div/month-table/table/tbody/tr[{row}]"
                                                   f"/td[{col}]/div"))).click()
            except ScraperFlowError:
                save_screenshot(self.driver)
                raise ScraperFlowError("Selected month is not available. A screenshot was saved in the current "
                                       "directory for debugging purposes")

            time.sleep(20)

            try:
                element = self.driver.find_element(By.XPATH, "//strong[contains(text(), 'Exportar excel')]")
            except ScraperFlowError:
                save_screenshot(self.driver)
                raise ScraperFlowError("Failed to find the 'Exportar excel' element")

            self.driver.execute_script("arguments[0].scrollIntoView();", element)
            element.click()

            wait_for_download(self.tmp, 30)

            current_date = datetime.datetime.now().strftime("%Y%m%d")
            assert f"Consumos_{current_date}.xlsx" in os.listdir(self.tmp), "Download failed"

            self.dwnl_file = Path(self.tmp) / f"Consumos_{current_date}.xlsx"

        progress.remove_task(t3)
        typer.echo(f"📁\tDownloaded file: {self.dwnl_file}")

        return self.dwnl_file

    def select_month(self, month: int):
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
        ) as progress:

            date = datetime.datetime(datetime.datetime.now().year, month, 1)
            row, col = map_month_matrix(date)

            t1 = progress.add_task(description=" 🔐 Loging in...", total=None)

            self.driver.get("https://balcaodigital.e-redes.pt/login")

            wait(self.driver, 30).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".ant-typography > .item > .highlights")
            )).click()

            self.driver.find_element(By.ID, "username").send_keys(f"{self.__nif}")

            self.driver.find_element(By.ID, "labelPassword").send_keys(f"{self.__password}")

            self.driver.find_element(By.XPATH, "//span[contains(.,'Entrar')]").click()
            time.sleep(5)

            text = None
            try:
                alert = self.driver.find_element(By.CSS_SELECTOR,
                                                 "body > app-root > nz-layout > app-default > main > nz-content > div "
                                                 "> div.login__text.ant-col > section.login-actions > app-sign-in > "
                                                 "div > div > form > "
                                                 "nz-form-item.ant-form-item.ant-row.ng-star-inserted > nz-alert > "
                                                 "div > div > span")
                text = alert.text
            except Exception:
                pass
            finally:
                if text is not None and "Dados inválidos" in text:
                    save_screenshot(self.driver)
                    raise ScraperFlowError(
                        "🔐 Invalid Credentials!\nCheck your NIF and Password with `ers config show`.\nA screenshot "
                        "was saved in the current directory for debugging purposes.")

            wait(self.driver, 30).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".card__myplaces .card-text")
            )).click()

            progress.remove_task(t1)
            t2 = progress.add_task(description=" 💡 Finding your CPE...", total=None)

            wait(self.driver, 30).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".card:nth-child(3) .highlights")
            )).click()

            wait(self.driver, 30).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".card:nth-child(1) > .item__title")
            )).click()
            try:
                wait(self.driver, 30).until(EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(),'{self.__cpe_code}')]")
                )).click()
            except ScraperFlowError:
                save_screenshot(self.driver)
                raise ScraperFlowError(
                    "💥 Failed to find the CPE code. A screenshot was saved in the current directory for debugging "
                    "purposes")

            progress.remove_task(t2)
            t3 = progress.add_task(description=" 📊 Downloading your data...", total=None)

            time.sleep(15)

            self.driver.find_element(By.CSS_SELECTOR, ".ng-tns-c78-32 > .ng-untouched").click()

            time.sleep(15)

            try:
                wait(self.driver, 30).until(EC.presence_of_element_located(
                    (By.XPATH, f"//div[@id='cdk-overlay-4']/div/div/date-range-popup/div/div/div"
                                                   f"/inner-popup/div/div/div/month-table/table/tbody/tr[{row}]"
                                                   f"/td[{col}]/div"))).click()
            except ScraperFlowError:
                save_screenshot(self.driver)
                raise ScraperFlowError("Selected month is not available. A screenshot was saved in the current "
                                       "directory for debugging purposes")

            time.sleep(20)

            try:
                element = self.driver.find_element(By.XPATH, "//strong[contains(text(), 'Exportar excel')]")
            except ScraperFlowError:
                save_screenshot(self.driver)
                raise ScraperFlowError("Failed to find the 'Exportar excel' element")

            self.driver.execute_script("arguments[0].scrollIntoView();", element)
            element.click()

            wait_for_download(self.tmp, 30)

            current_date = datetime.datetime.now().strftime("%Y%m%d")
            assert f"Consumos_{current_date}.xlsx" in os.listdir(self.tmp), "Download failed"

            self.dwnl_file = Path(self.tmp) / f"Consumos_{current_date}.xlsx"

        progress.remove_task(t3)
        typer.echo(f"📁\tDownloaded file: {self.dwnl_file}")

        return self.dwnl_file

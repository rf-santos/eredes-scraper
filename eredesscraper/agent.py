import datetime
import re
from pathlib import Path
import sys
from time import sleep
from random import randint
from uuid import uuid4
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

from eredesscraper.utils import map_month_matrix_names, pw_nav_year_back
from eredesscraper.meta import user_agent_list

ENTRYPOINT = "https://balcaodigital.e-redes.pt/consumptions/history"


class ScraperFlowError(Exception):
    pass


class EredesScraper:
    def __init__(self, nif, password, cpe_code, quiet: bool, headless: bool = True, uuid: uuid4 = uuid4()):
        self.dwnl_file = None
        self.session_id = uuid
        self.browser = None
        self.context = None
        self.page = None
        self.headless = headless
        self.__nif = nif
        self.__password = password
        self.__cpe_code = cpe_code
        self.__implicit_wait = 90
        self.__quiet = quiet

        # Create a staging area for the Playwright
        try:
            Path.mkdir(Path.cwd() / 'ers_tmp', exist_ok=True)
        except PermissionError:
            print("Permission denied to create a staging area for the Scraper")

        self.tmp = Path(Path.cwd() / 'ers_tmp').__str__()

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

    def teardown(self):
        self.context.close()
        self.browser.close()

    def readings(self, month: int, year: int):
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
                disable=self.__quiet
        ) as progress:

            date = datetime.datetime(year, month, 1)

            current_date = datetime.datetime.now()

            assert date <= datetime.datetime.now(), "Selected date is in the future"

            t1 = progress.add_task(description=" 🔐 Logging in...", total=None)

            self.page.goto(ENTRYPOINT)

            self.page.get_by_text("Particular").click()

            self.page.get_by_label("NIF").fill(f"{self.__nif}")

            self.page.get_by_label("Password").fill(f"{self.__password}")

            self.page.get_by_role("button", name="Entrar").click()
            # self.page.get_by_label("Password").press("Enter")
            # self.page.get_by_text("Entrar").click()

            # try:
            #     self.page.get_by_text("Leituras, contadores,").click()
            #     # self.page.get_by_role("heading", name="Os meus locais").click()                
            # except ScraperFlowError:
            #     self.page.screenshot(path=f"{Path.cwd()}/ers_login_error.png")
            #     with open(f"{Path.cwd()}/ers_login_error.html", "w") as f:
            #         f.write(self.page.content())
            #     if self.page.locator(has_text="Dados inválidos").is_visible():
            #         raise ScraperFlowError("🔐 Invalid Credentials!\nCheck your NIF and "
            #                                "Password with `ers config show`.\nA screenshot was saved in the current "
            #                                "directory for debugging purposes.")

            try:
                captcha = self.page.locator("h1").filter(has_text="Validação de Segurança")

                if captcha.is_visible():
                    print("🔐 Captcha detected. Try again later")
                    raise ScraperFlowError("🔐 Captcha detected. A screenshot was saved in the current directory for debugging purposes"
                                           "\nPlease try again later.")
            except ScraperFlowError:
                self.page.screenshot(path=f"{Path.cwd()}/ers_captcha_error.png")
                raise ScraperFlowError("🔐 Captcha detected. A screenshot was saved in the current directory for debugging purposes"
                                       "\nPlease try again later.")
                    

            progress.remove_task(t1)
            t2 = progress.add_task(description=" 💡 Finding your CPE...", total=None)

            # self.page.get_by_text("Produção, consumos e potências").click()

            # self.page.get_by_text("Consultar histórico").click()

            # self.page.locator("p").filter(has_text=re.compile(self.__cpe_code)).click()

            try:
                self.page.locator("p").filter(has_text=re.compile(r"^" + self.__cpe_code + "$")).click(timeout=120000)
            except ScraperFlowError:
                self.page.screenshot(path=f"{Path.cwd()}/ers_cpe_error.png")
                raise ScraperFlowError("💥 Failed to find the CPE code. A screenshot was "
                                    "saved in the current directory for debugging purposes")

            progress.remove_task(t2)
            t3 = progress.add_task(description=" 📊 Downloading your data...", total=None)

            if date.strftime("%Y-%m") != current_date.strftime("%Y-%m"):

                month_str = map_month_matrix_names(date)

                self.page.get_by_role("textbox", name="Select month").click()

                if date.year != current_date.now().year:

                    self.page.get_by_role("button", name=f"{current_date.year}").click()

                    target_year = self.page.get_by_text(f"{date.year}", exact=True)

                    if not target_year.is_visible():
                        self.page = pw_nav_year_back(date=date, pw_page=self.page)

                    target_year = self.page.get_by_text(f"{date.year}", exact=True)

                    is_disabled = bool(target_year.get_attribute("aria-disabled"))               

                    if is_disabled:
                        raise ScraperFlowError("There is no available data for the selected year")
                    else:
                        target_year.click()
                
                if self.page.get_by_role("gridcell", name=f"{month_str}").is_disabled():
                    self.page.screenshot(path=f"{Path.cwd()}/ers_month_error.png")
                    raise ScraperFlowError("Selected month is not available. A screenshot was saved in the current "
                                           "directory for debugging purposes")

                self.page.get_by_role("gridcell", name=f"{month_str}").click()
            
            try:
                with self.page.expect_event("download") as download_info:

                    # self.page.get_by_text("Exportar excel").click()
                    self.page.locator("a").filter(has_text="Exportar excel").click()

                    download = download_info.value

                download.save_as(f"{self.tmp}/{year}_{month}_{self.session_id.__str__().split('-')[0]}_readings.xlsx")
            
            except ScraperFlowError:
                self.page.screenshot(path=f"{Path.cwd()}/ers_download_error.png")
                raise ScraperFlowError("Failed to find the 'Exportar excel' element")

            self.dwnl_file = Path(self.tmp) / f"{year}_{month}_{self.session_id.__str__().split('-')[0]}_readings.xlsx"

            assert self.dwnl_file.exists(), "Failed to download the file"

        progress.remove_task(t3)
        if not self.__quiet:
            typer.echo(f"📁\tDownloaded file: {self.dwnl_file}")

        return self.dwnl_file
    
    
    def run(self, month, year):
        ua = user_agent_list[randint(0, len(user_agent_list) - 1)]
        with sync_playwright() as p:
            self.browser = p.webkit.launch(headless=self.headless, downloads_path=self.tmp)
            self.context = self.browser.new_context(
                user_agent=ua
            )
            self.context.set_default_timeout(self.__implicit_wait * 1000)
            self.page = self.context.new_page()
            stealth_sync(self.page)
            self.readings(month, year)
            self.teardown()
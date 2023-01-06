from logging import getLogger, StreamHandler, DEBUG
from sys import stdout
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from sys import platform
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class EredesDriver(webdriver.Chrome):
    def __init__(self, **kwargs):
        super().__init__()

        # Create a staging area for the ChromeDriver
        Path.mkdir(Path.cwd() / 'tmp', exist_ok=True)
        tmp = Path.cwd() / 'tmp'

        # Initialize ChromeDriver options
        chrome_options = webdriver.ChromeOptions()

        # Modify the ChromeDriverManager to use the staging area
        dl_path = ''
        if platform == "linux" or platform == "linux2" or platform == "darwin":
            dl_path = tmp.as_posix()
        elif platform == "win32":
            dl_path = tmp.__str__()

        if dl_path:
            prefs = {"download.default_directory": dl_path}
            chrome_options.add_experimental_option("prefs", prefs)

        # Headless option
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--no-sandbox')
        # chrome_options.add_argument('--disable-dev-shm-usage')

        # Initialize ChromeDriver
        webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), chrome_options=chrome_options)


class EredesAgent():
    def __init__(self):
        super().__init__()

        # Import configuration
        self.user = globals()['EREDES_USER']
        self.password = globals()['EREDES_PASSWORD']
        self.target = globals()['EREDES_TARGET']
        self.cpe = globals()['EREDES_CPE']

        # Initialize logging

        self.log = getLogger('eredes-agent')
        self.log.setLevel(DEBUG)
        self.log.addHandler(StreamHandler(stream=stdout))

        # Initialize ChromeDriver
        self.driver = EredesDriver()


    def login_private_user(self):
        login_success = False

        # Select Private User login
        wait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH,
                                                           "/html/body/app-root/nz-layout/app-default/main/nz-content/div"
                                                           "/div[2]/section[1]/div[2]/div/div/ul/li[1]/div[2]"))).click()

        # User and Password elements defined by XPATH
        uname = driver.find_element(By.XPATH,
                                    "/html/body/app-root/nz-layout/app-default/main/nz-content/div/div[2]/section["
                                    "1]/app-sign-in/div/div/form/nz-form-item[1]/nz-form-control/div/div/div/input")
        passwd = driver.find_element(By.XPATH,
                                     "/html/body/app-root/nz-layout/app-default/main/nz-content/div/div[2]/section["
                                     "1]/app-sign-in/div/div/form/nz-form-item["
                                     "2]/nz-form-control/div/div/div/nz-input-group/input")

        # Send login credentials
        uname.send_keys(user)
        passwd.send_keys(password)

        wait(driver, 10)

        # Click Login button
        driver.find_element(By.XPATH,
                            "/html/body/app-root/nz-layout/app-default/main/nz-content/div/div[2]/section["
                            "1]/app-sign-in/div/div/form/div[2]/div/button/span").click()

        wait(driver, 10).until(
            lambda x: x.execute_script("return document.readyState === 'complete'")
        )
        # Verify that the login was successful.
        error_message = "Incorrect username or password."
        # Retrieve any errors found.
        errors = driver.find_elements(By.CLASS_NAME, "flash-error")

        # When errors are found, the login will fail.
        if any(error_message in e.text for e in errors):
            print("[!] Login failed")
        else:
            print("[+] Login successful")


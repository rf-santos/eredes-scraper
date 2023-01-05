from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from sys import platform
from pathlib import Path


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

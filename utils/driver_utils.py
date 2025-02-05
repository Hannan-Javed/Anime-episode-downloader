import os

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service

def setup_driver(download_directory: str) -> Chrome:
    """
    Setup the Chrome WebDriver. Sets the download directory, headless mode, and suppresses logging.
    
    Args:
        download_directory: The directory where downloads are saved.

    Returns:
        Chrome: The configured Chrome WebDriver instance.
    """
    prefs = {
        "download.default_directory": download_directory,
        "download.directory_upgrade": True,
        "download.prompt_for_download": False,
    }

    chrome_options = ChromeOptions()
    chrome_options.add_experimental_option("prefs", prefs)
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    service = Service(log_path=os.devnull)
    return Chrome(options=chrome_options, service=service)
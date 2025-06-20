from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions as SelEx

class BasePage:
    def __init__(self, driver, timeout=10, logger=None, base_url=None):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
        self.logger = logger
        self.base_url = base_url

    def find(self, by, locator):
        try:
            elem = self.wait.until(EC.presence_of_element_located((by, locator)))
            return elem
        except SelEx.TimeoutException:
            if self.logger:
                self.logger.error(f"Element not found: {by}={locator}")
            raise

    def click(self, by, locator):
        elem = self.find(by, locator)
        try:
            clickable = self.wait.until(EC.element_to_be_clickable((by, locator)))
            clickable.click()
        except SelEx.TimeoutException:
            if self.logger:
                self.logger.error(f"Element not clickable: {by}={locator}")
            raise

    def input_text(self, by, locator, text, clear_first=True):
        elem = self.find(by, locator)
        if clear_first:
            elem.clear()
        elem.send_keys(text)

    def get_current_url(self):
        return self.driver.current_url

    def open(self, url):
        self.driver.get(url)

    def wait_for_url_contains(self, substring):
        try:
            self.wait.until(EC.url_contains(substring))
        except SelEx.TimeoutException:
            if self.logger:
                self.logger.warning(f"URL did not contain '{substring}' in time")
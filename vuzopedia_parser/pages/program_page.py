from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .base_page import BasePage

class ProgramPage(BasePage):
    def open(self, url):
        self.driver.get(url)

    def get_html(self):
        # Ждём название программы
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        except TimeoutException:
            if self.logger:
                self.logger.warning("h1 (название программы) не загрузилось вовремя")
        # Ждём блок с баллами или ссылку на направление
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/napr/']")))
        except TimeoutException:
            if self.logger:
                self.logger.warning("Ссылка на направление не загрузилась вовремя")
        return self.driver.page_source

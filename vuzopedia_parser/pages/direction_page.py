import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .base_page import BasePage

class DirectionPage(BasePage):
    def open(self, url):
        self.driver.get(url)

    def get_program_links(self):
        """
        Собираем только ссылки вида /programs/bakispec/{id}, где {id} — число.
        """
        try:
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/programs/']")))
        except TimeoutException:
            if self.logger:
                self.logger.warning("Ссылки на программы не появились вовремя")

        elems = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/programs/']")
        links = set()
        for el in elems:
            href = el.get_attribute('href')
            if not href:
                continue
            href_base = href.split('?')[0]
            # Правильный regex: r"/programs/bakispec/\d+$"
            if re.search(r"/programs/bakispec/\d+$", href_base):
                links.add(href_base)
        if self.logger:
            self.logger.info(f"Найдено валидных программ: {len(links)}")
        return list(links)

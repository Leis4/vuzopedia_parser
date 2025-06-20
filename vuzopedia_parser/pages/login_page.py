from selenium.webdriver.common.by import By
from .base_page import BasePage
import time

class LoginPage(BasePage):
    def open_login_page(self, login_url):
        self.driver.get(login_url)

    def manual_login_and_save_cookies(self, cookies_path):
        input("Пожалуйста, выполните вход в браузере, затем нажмите Enter...")
        from vuzopedia_parser.utils.cookies import save_cookies
        save_cookies(self.driver, cookies_path)
        if self.logger:
            self.logger.info("Cookies saved after manual login")
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from vuzopedia_parser.pages.base_page import BasePage
import time

class MainPage(BasePage):
    def __init__(self, driver, timeout=10, logger=None, base_url=None, city_id=None, direction_id=None):
        super().__init__(driver, timeout, logger)
        self.base_url = base_url.rstrip('/') if base_url else ''
        self.city_id = city_id
        self.direction_id = direction_id

    def open_with_filters(self, city_id, direction_id, _subjects_dict=None):
        self.city_id = city_id
        self.direction_id = direction_id
        url = f"{self.base_url}/vuzfilter?city%5B%5D={city_id}&speca%5B%5D={direction_id}&page=1"
        if self.logger:
            self.logger.info(f"Открываем фильтрованную страницу: {url}")
        self.driver.get(url)
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-md-12[class*='newItemVuz']"))
            )
        except TimeoutException:
            if self.logger:
                self.logger.warning("Фильтрованная страница вузов не загрузилась вовремя")

    def _scroll_slowly(self):
        # Несколько прокруток вниз для lazy-load
        for _ in range(3):
            self.driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(2.0)

    def get_university_links(self):
        """
        Собираем ссылки вузов по страницам, сохраняя порядок.
        Используем универсальный селектор по 'newItemVuz'.
        """
        links = []
        seen = set()
        page = 1
        while True:
            url = f"{self.base_url}/vuzfilter?city%5B%5D={self.city_id}&speca%5B%5D={self.direction_id}&page={page}"
            if self.logger:
                self.logger.info(f"Open filter page {page}: {url}")
            self.driver.get(url)

            # лениво подгружаем
            self._scroll_slowly()

            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.col-md-12[class*='newItemVuz']"))
                )
                time.sleep(0.5)
            except TimeoutException:
                if self.logger:
                    self.logger.warning(f"Карточки вузов не появились на странице {page}")
                break

            cards = self.driver.find_elements(By.CSS_SELECTOR, "div.col-md-12[class*='newItemVuz']")
            if not cards:
                if self.logger:
                    self.logger.info(f"Нет карточек на странице {page}, выходим")
                break

            new_count = 0
            for card in cards:
                try:
                    a = card.find_element(By.CSS_SELECTOR, "a[href*='/vuz/']")
                    href = a.get_attribute("href")
                except:
                    continue
                if not href:
                    continue
                href_base = href.split('?')[0]
                if "/vuz/" in href_base:
                    part = href_base.split("/vuz/")[1].split('/')[0]
                    if part.isdigit() and href_base not in seen:
                        seen.add(href_base)
                        links.append(href_base)
                        new_count += 1
            if self.logger:
                self.logger.info(f"Страница {page}: найдено новых вузов {new_count}")

            # попытка найти кнопку Next
            has_next = False
            try:
                next_btn = self.driver.find_element(By.CSS_SELECTOR, "ul.pagination li.active + li a")
                href_next = next_btn.get_attribute("href")
                if href_next:
                    has_next = True
            except:
                # неявная: будем проверять следующую страницу по URL
                has_next = True

            if not has_next:
                break
            page += 1
            time.sleep(1.0)

        if self.logger:
            self.logger.info(f"Всего вузов после фильтра (с сохранением порядка): {len(links)}")
            for u in links[:5]:
                self.logger.info(f"  Univ: {u}")
        return links

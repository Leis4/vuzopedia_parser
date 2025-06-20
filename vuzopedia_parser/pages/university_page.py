# vuzopedia_parser/pages/university_page.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .base_page import BasePage
from bs4 import BeautifulSoup  # если используете BS для поиска комбинаций

class UniversityPage(BasePage):
    def __init__(self, driver, timeout=10, logger=None):
        super().__init__(driver, timeout, logger)

    def open(self, url):
        self.driver.get(url)

    def show_all_ege_combinations(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.buttonNewCombActive")))
            btn.click()
            if self.logger:
                self.logger.info("Кликнули 'Посмотреть все' комбинаций ЕГЭ")
            # Ждём, что комбинации появились (уточните селектор, здесь пример):
            # self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.blockItemComb")))
        except TimeoutException:
            if self.logger:
                self.logger.warning("Кнопка 'Посмотреть все' не появилась вовремя")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Ошибка при клике 'Посмотреть все': {e}")

    def find_ege_combination(self, required_subjects):
        """
        Ищет комбинацию required_subjects (например ["Русский язык","Математика","Информатика"]) в любом порядке.
        Блоки комбинаций имеют структуру:
        <div class="blockItemComb">
            <div class="itemNewBlockComb">Математика</div>
            <div class="itemNewBlockComb">Русский язык</div>
            <div class="itemNewBlockComb">Информатика</div>
        </div>
        """
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        blocks = soup.find_all("div", class_="blockItemComb")
        for block in blocks:
            items = block.find_all("div", class_="itemNewBlockComb")
            subjects = [item.get_text(strip=True) for item in items]
            # Проверяем, что все требуемые предметы в этом блоке
            if all(req in subjects for req in required_subjects):
                if self.logger:
                    self.logger.info(f"Найдена комбинация ЕГЭ: {subjects}")
                return True
        if self.logger:
            self.logger.info(f"Комбинация {required_subjects} не найдена")
        return False

    def get_direction_links(self):
        """
        Собирает ссылки на все направления (napr) на странице вуза.
        Обычный URL: https://vuzopedia.ru/vuz/{id}/napr/{dir_id}
        """
        try:
            # Ждём появления раздела направлений, уточните селектор:
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/napr/']")))
        except TimeoutException:
            if self.logger:
                self.logger.warning("Ссылки на направления не появились вовремя")
        elems = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/napr/']")
        links = set()
        for el in elems:
            href = el.get_attribute('href')
            if href and '/napr/' in href:
                links.add(href.split('?')[0])
        if self.logger:
            self.logger.info(f"Найдено направлений: {len(links)}")
        return list(links)

    def get_program_links(self):
        elems = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/programs/']")
        links = set()
        for el in elems:
            href = el.get_attribute('href')
            if not href: continue
            href_base = href.split('?')[0]
            if re.search(r"/programs/bakispec/\\d+$", href_base):
                links.add(href_base)
        if self.logger:
            self.logger.info(f"Найдено валидных программ на странице университета: {len(links)}")
        return list(links)


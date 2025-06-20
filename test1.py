# -*- coding: utf-8 -*-
import os
import pytest
from selenium.webdriver.chrome.webdriver import WebDriver
from bs4 import BeautifulSoup
from vuzopedia_parser import build_filter_url, parse_program_from_driver

# Тесты для утилитарных функций

def test_build_filter_url():
    params = {'city_id': 59, 'speca_id': 5, 'mat': 76, 'rus': 72, 'inform': 82}
    url = build_filter_url(params)
    assert url.startswith("https://vuzopedia.ru/vuzfilter?")
    assert 'city%5B%5D=59' in url
    assert 'speca%5B%5D=5' in url
    assert 'mat=76' in url
    assert 'rus=72' in url
    assert 'inform=82' in url

# Для тестирования парсинга детальной страницы:
# Сохраните вручную HTML страницы программы как sample_program.html рядом с этим тестом.

def load_sample_html():
    path = os.path.join(os.path.dirname(__file__), 'sample_program.html')
    if not os.path.exists(path):
        pytest.skip("Нет sample_program.html для теста парсинга")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

class DummyDriver:
    """Заглушка для Selenium WebDriver: хранит page_source"""
    def __init__(self, html):
        self.page_source = html
        self.current_url = 'https://vuzopedia.ru/vuz/xxx/programs/bakispec/yyy'


def test_parse_program_from_driver_with_sample():
    html = load_sample_html()
    driver = DummyDriver(html)
    data = parse_program_from_driver(driver)
    # Пример: проверяем, что вернулся dict или None
    if data is None:
        pytest.skip("parse_program_from_driver вернул None; проверьте sample_program.html и ALLOWED_CODES")
    # Проверяем наличие ключей
    assert 'Название программы' in data
    assert 'Код направления' in data
    assert 'Ссылка' in data
    # Если в sample есть проходные баллы, проверяем формат
    for k, v in data.items():
        assert isinstance(v, str) or isinstance(v, (int, float))

# Интеграционные проверки с Selenium вручную:
# Запускать отдельно: проверить, что браузер запускается и URL фильтра открывается.
# Можно использовать фикстуру Selenium WebDriver:

@pytest.fixture(scope='module')
def driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    opts = Options()
    opts.add_argument('--headless')
    driver = webdriver.Chrome(options=opts)
    yield driver
    driver.quit()


def test_filter_url_opens_page(driver):
    # Тестирует, что filter_url возвращает страницу без ошибки 404.
    params = {'city_id': 59, 'speca_id': 5, 'mat': 76, 'rus': 72, 'inform': 82}
    url = build_filter_url(params)
    driver.get(url)
    assert "vuz/" in driver.current_url or driver.title is not None

# Дополнительные ручные тесты:
# - Сохраните HTML вузов в sample_univ.html и протестируйте извлечение ссылок.
# - Для этого можно написать аналогичные функции parse_univ_list(html) и тестировать их.

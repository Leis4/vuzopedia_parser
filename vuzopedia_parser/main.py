import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from vuzopedia_parser.pages.main_page import MainPage

def click_show_specialties(driver, logger, timeout=10):
    """
    Кликает на кнопку "Показать специальности" или "Посмотреть все комбинаций".
    Скрывает/скроллит, если надо.
    """
    try:
        btn = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                "a.openSideCont, div.buttonNewComb, div.buttonNewCombActive"))
        )
        # Скрыть возможные баннеры мешающие
        try:
            banner = driver.find_element(By.CSS_SELECTOR, "#fab")
            driver.execute_script("arguments[0].style.display='none'", banner)
        except:
            pass
        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        time.sleep(0.3)
        try:
            btn.click()
        except ElementClickInterceptedException:
            logger.info("Click intercepted, пытаемся через JS")
            driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.5)
    except TimeoutException:
        logger.info("Кнопка 'Показать специальности' не найдена или не успела загрузиться")
    except Exception as e:
        logger.exception(f"Ошибка при клике 'Показать специальности': {e}")

def process_university(arg):
    """
    arg: (uni_url, cfg), cfg содержит driver, logger, valid_codes и т.п.
    Возвращает список: [(prog_url, data_dict), ...] или [].
    """
    uni_url, cfg = arg
    driver = cfg.get("driver")
    logger = cfg.get("logger")
    timeout = cfg.get("timeout", 10)
    valid_codes = cfg.get("valid_codes", [])  # список допустимых кодов программ, при необходимости
    results = []
    try:
        driver.get(uni_url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
        click_show_specialties(driver, logger, timeout)

        # Пример поиска комбинаций ЕГЭ на странице университета
        comb = None
        try:
            # скорректируйте селектор под реальный сайт
            comb_elements = driver.find_elements(By.CSS_SELECTOR, ".combination-selector")
            for el in comb_elements:
                texts = [t.strip() for t in el.text.split(',')]
                # проверить, подходит ли комбинация:
                # пример: если хотите именно конкретный набор, напишите условие:
                # if set(texts) == set(["Русский язык", "Математика", "Информатика"]):
                #     comb = texts
                #     break
                # Пока оставляем как заглушку:
                # если нашли нужную комбинацию, установите comb = texts и break
                pass
        except Exception:
            pass
        if comb is None:
            logger.info(f"Комбинация ЕГЭ не подходит: {uni_url}")
            return []

        # Найти направления (скорректировать селектор)
        try:
            directions = driver.find_elements(By.CSS_SELECTOR, "a.napravlenie-link")
        except Exception:
            directions = []
        for d in directions:
            dir_link = d.get_attribute("href")
            if not dir_link:
                continue
            driver.get(dir_link)
            try:
                WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.program-item"))
                )
            except TimeoutException:
                logger.warning(f"Не дождались списка программ на направлении: {dir_link}")
                continue
            # Собираем ссылки программ (скорректировать селектор)
            try:
                program_links = driver.find_elements(By.CSS_SELECTOR, "a.program-item-link")
            except Exception:
                program_links = []
            for p in program_links:
                prog_url = p.get_attribute("href")
                if not prog_url:
                    continue
                # Открываем страницу программы
                driver.get(prog_url)
                try:
                    WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                    )
                except TimeoutException:
                    logger.warning(f"Не дождались загрузки страницы программы: {prog_url}")
                    continue
                # Пример сбора данных из страницы программы. Скорректируйте под нужные поля:
                data = {"url": prog_url}
                # Например:
                try:
                    title_el = driver.find_element(By.CSS_SELECTOR, "h1")
                    data["title"] = title_el.text.strip()
                except:
                    pass
                # Соберите другие поля...
                # Можно проверять код программы и фильтровать по valid_codes:
                # code = data.get("code")
                # if valid_codes and code not in valid_codes:
                #     logger.info(f"Код {code} не в списке valid_codes, пропускаем: {prog_url}")
                #     continue
                results.append((prog_url, data))
        return results

    except Exception as e:
        logger.exception(f"Ошибка в process_university для {uni_url}: {e}")
        return []

def main():
    logger = logging.getLogger("main")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    # Инициализация WebDriver
    driver = webdriver.Chrome()
    base_url = "https://vuzopedia.ru"
    city_id = 59
    direction_id = 5

    main_page = MainPage(driver, timeout=10, logger=logger, base_url=base_url)
    main_page.open_with_filters(city_id, direction_id, None)
    uni_links = main_page.get_university_links()
    total_unis = len(uni_links)
    logger.info(f"Total {total_unis} вузов после фильтра")

    all_results = []
    skipped_unis = []
    for idx, uni_url in enumerate(uni_links, start=1):
        logger.info(f"Processing {idx}/{total_unis}: {uni_url}")
        try:
            cfg = {
                "driver": driver,
                "logger": logger,
                "timeout": 10,
                "valid_codes": [],  # при необходимости укажите список допустимых кодов
            }
            uni_results = process_university((uni_url, cfg))
            if not isinstance(uni_results, (list, tuple)):
                logger.warning(f"process_university вернул не-list: {type(uni_results)}")
                skipped_unis.append(uni_url)
                continue
            for item in uni_results:
                if isinstance(item, tuple) and len(item) == 2:
                    prog_url, data = item
                elif isinstance(item, dict):
                    prog_url = item.get("url")
                    data = item
                    if prog_url is None:
                        logger.warning(f"Нет 'url' в возвращённом dict: {item}")
                        continue
                else:
                    logger.warning(f"Неизвестный элемент из process_university: {item}")
                    continue
                all_results.append((prog_url, data))
        except Exception as e:
            logger.exception(f"Ошибка при обработке университета {uni_url}: {e}")
            skipped_unis.append(uni_url)
        # небольшая пауза между университетами, если нужно
        # time.sleep(1)

    logger.info(f"Всего программ собрано: {len(all_results)}; пропущено вузов: {len(skipped_unis)}")
    if skipped_unis:
        logger.info("Список пропущенных вузов:")
        for u in skipped_unis:
            logger.info(f"  {u}")

    # TODO: Дальнейшая обработка all_results

    driver.quit()

if __name__ == "__main__":
    main()

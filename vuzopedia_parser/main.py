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
    Кликает на кнопку "Показать специальности" или аналогичные элементы, раскрывает блок с комбинациями.
    """
    selectors = [
        "a.openSideCont", "div.buttonNewComb", "div.buttonNewCombActive",
        "button.show-combinations", ".show-all-combinations",
    ]
    xpath_texts = ["contains(text(), 'Все комбинации')", "contains(text(), 'Показать специальности')", "contains(text(), 'Посмотреть все')"]
    # Скрыть возможные мешающие баннеры
    try:
        banners = driver.find_elements(By.CSS_SELECTOR, "#fab, .overlay-banner, .fixed-banner")
        for banner in banners:
            driver.execute_script("arguments[0].style.display='none'", banner)
    except Exception:
        pass
    # Попробовать несколько попыток кликнуть
    for attempt in range(3):
        # Попробовать CSS селекторы
        for sel in selectors:
            try:
                btn = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.3)
                try:
                    btn.click()
                except ElementClickInterceptedException:
                    logger.info("Click intercepted, пытаемся через JS на селектор %s", sel)
                    driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
                return True
            except Exception:
                continue
        # Попробовать XPath по тексту
        for txt in xpath_texts:
            try:
                btn = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, f"//*[ {txt} ]"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.3)
                try:
                    btn.click()
                except ElementClickInterceptedException:
                    logger.info("Click intercepted via JS для текста %s", txt)
                    driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
                return True
            except Exception:
                continue
        # Если не нашли, прокрутить
        try:
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
        except Exception:
            pass
        time.sleep(1)
    logger.debug("Кнопка показа комбинаций не найдена после попыток")
    return False


def normalize_subject(subject):
    s = subject.strip().lower()
    # Упрощение названий
    s = s.replace("русский язык", "русский")
    s = s.replace("математика (профильная)", "математика")
    s = s.replace("математика профильная", "математика")
    s = s.replace("информатика и икт", "информатика")
    # Убрать скобки и лишние описания
    if '(' in s:
        s = s.split('(')[0].strip()
    return s


def find_ege_combination(driver, logger, timeout=10, target_subjects=None):
    """Пытается найти нужную комбинацию ЕГЭ на странице университета"""
    if target_subjects is None:
        target_subjects = {"русский", "математика", "информатика"}
    # Попытаться кликнуть показать все комбинации
    click_show_specialties(driver, logger, timeout)
    # Дать время на загрузку
    time.sleep(1.5)
    selectors = [
        "div.blockItemComb",
        "div.contCombsBlock",
        ".combination-selector",
        ".ege-combination",
        ".comb-list",
    ]
    elems = []
    for attempt in range(4):
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ",".join(selectors)))
            )
        except TimeoutException:
            logger.debug(f"Попытка {attempt+1}: блоки комбинаций не появились за время ожидания")
        # Собираем элементы
        elems = []
        for sel in selectors:
            try:
                found = driver.find_elements(By.CSS_SELECTOR, sel)
                if found:
                    elems.extend(found)
            except Exception:
                continue
        if elems:
            break
        # Если не нашли, прокрутить вниз и попробовать снова
        try:
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
        except Exception:
            pass
        # Повторно попытаться раскрыть комбинации
        click_show_specialties(driver, logger, timeout)
        time.sleep(1)
    if not elems:
        logger.debug("После нескольких попыток блоки комбинаций не найдены")
    # Проанализировать найденные блоки
    for el in elems:
        parts = []
        try:
            items = el.find_elements(By.CSS_SELECTOR, "div.itemNewBlockComb, .item-comb-element")
            if items:
                for item in items:
                    text = item.text.strip()
                    if text:
                        parts.append(text)
            else:
                text = el.text.strip()
                if not text:
                    continue
                if ',' in text:
                    parts = [t.strip() for t in text.split(',') if t.strip()]
                elif '\n' in text:
                    parts = [t.strip() for t in text.split('\n') if t.strip()]
                elif ';' in text:
                    parts = [t.strip() for t in text.split(';') if t.strip()]
                else:
                    child_texts = []
                    for child in el.find_elements(By.XPATH, ".//*"):
                        ct = child.text.strip()
                        if ct:
                            child_texts.append(ct)
                    parts = child_texts or [text]
        except Exception as inner_e:
            logger.debug(f"Ошибка получения частей комбинации: {inner_e}")
            continue
        normalized = {normalize_subject(p) for p in parts if p.strip()}
        logger.debug(f"Комбинация из элемента: {normalized}")
        if normalized == target_subjects:
            logger.info(f"Найдена подходящая комбинация: {normalized}")
            return True
    # Дополнительно попытаться через XPath
    try:
        xpath_expr = "//div[contains(@class,'blockItemComb')]//div[contains(@class,'itemNewBlockComb')]"
        elems_xpath = driver.find_elements(By.XPATH, xpath_expr)
        parts = [el.text.strip() for el in elems_xpath if el.text.strip()]
        normalized = {normalize_subject(p) for p in parts}
        logger.debug(f"Комбинация из XPath: {normalized}")
        if normalized == target_subjects:
            logger.info(f"Найдена подходящая комбинация через XPath: {normalized}")
            return True
    except Exception:
        pass
    logger.debug("Подходящая комбинация не найдена")
    # Для отладки можно раскомментировать:
    # logger.debug(driver.page_source)
    return False


def process_university(arg):
    uni_url, cfg = arg
    driver = cfg.get("driver")
    logger = cfg.get("logger")
    timeout = cfg.get("timeout", 10)
    valid_codes = cfg.get("valid_codes", [])
    results = []
    try:
        driver.get(uni_url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
        # Проверка комбинации ЕГЭ
        if not find_ege_combination(driver, logger, timeout):
            logger.info(f"Комбинация ЕГЭ не подходит: {uni_url}")
            return []
        # Перейти по направлениям
        try:
            directions = driver.find_elements(By.CSS_SELECTOR, "a.napravlenie-link, .direction-link")
        except Exception:
            directions = []
        for d in directions:
            dir_link = d.get_attribute("href")
            if not dir_link:
                continue
            driver.get(dir_link)
            try:
                WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.program-item, .program-list"))
                )
            except TimeoutException:
                logger.warning(f"Не дождались списка программ на направлении: {dir_link}")
                continue
            try:
                program_links = driver.find_elements(By.CSS_SELECTOR, "a.program-item-link, .program-link")
            except Exception:
                program_links = []
            for p in program_links:
                prog_url = p.get_attribute("href")
                if not prog_url:
                    continue
                driver.get(prog_url)
                try:
                    WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                    )
                except TimeoutException:
                    logger.warning(f"Не дождались загрузки страницы программы: {prog_url}")
                    continue
                data = {"url": prog_url}
                try:
                    title_el = driver.find_element(By.CSS_SELECTOR, "h1, .program-title")
                    data["title"] = title_el.text.strip()
                except Exception:
                    pass
                results.append((prog_url, data))
        return results
    except Exception as e:
        logger.exception(f"Ошибка в process_university для {uni_url}: {e}")
        return []


def main():
    logger = logging.getLogger("main")
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(ch)

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
                "valid_codes": [],
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

    logger.info(f"Всего программ собрано: {len(all_results)}; пропущено вузов: {len(skipped_unis)}")
    if skipped_unis:
        logger.info("Список пропущенных вузов:")
        for u in skipped_unis:
            logger.info(f"  {u}")

    driver.quit()

if __name__ == "__main__":
    main()

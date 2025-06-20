# # -*- coding: utf-8 -*-
# import logging
# import time
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import (
#     TimeoutException,
#     WebDriverException,
#     StaleElementReferenceException,
# )
# from vuzopedia_parser.pages.main_page import MainPage
#
# # --- Настройка логирования ---
# logging.basicConfig(
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     level=logging.INFO
# )
# logger = logging.getLogger("main")
# # Отключаем шумные логи Selenium/urllib3
# logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
# logging.getLogger("urllib3").setLevel(logging.WARNING)
#
# CITY_ID = 59
# DIRECTION_ID = 5
#
# def normalize_subject(s: str) -> str:
#     s = s.strip().lower()
#     s = s.replace("русский язык", "русский")
#     s = s.replace("математика (профильная)", "математика")
#     s = s.replace("математика профильная", "математика")
#     s = s.replace("информатика и икт", "информатика")
#     return s.split('(')[0].strip()
#
# def has_target_ege_combination(driver, timeout=5) -> bool:
#     """
#     Проверяем, есть ли на странице ссылка /poege/egemat;egerus;egeinform;.
#     Ждём элемент a.itemBlockCombLink, затем проверяем href-ы.
#     """
#     target_codes = {"egemat", "egerus", "egeinform"}
#     try:
#         WebDriverWait(driver, timeout).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "a.itemBlockCombLink"))
#         )
#     except TimeoutException:
#         return False
#     try:
#         links = driver.find_elements(By.CSS_SELECTOR, "a.itemBlockCombLink")
#     except Exception:
#         return False
#     for link in links:
#         try:
#             href = link.get_attribute("href") or ""
#         except StaleElementReferenceException:
#             continue
#         if "/poege/" not in href:
#             continue
#         segment = href.split("/poege/")[1].split("?")[0].rstrip("/")
#         codes = [c for c in segment.split(";") if c]
#         if set(codes) == target_codes:
#             return True
#     return False
#
# def process_university(driver, uni_url, timeout=10):
#     """
#     Открываем страницу университета, проверяем ЕГЭ-комбинацию, парсим направления и программы.
#     Возвращает список кортежей (prog_url, title).
#     """
#     results = []
#     logger.info(f"Открываем вуз: {uni_url}")
#     try:
#         driver.get(uni_url)
#         WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
#     except TimeoutException:
#         logger.warning(f"  Не загрузилась страница вуза: {uni_url}")
#         return results
#
#     try:
#         if not has_target_ege_combination(driver, timeout):
#             logger.info("  → комбинация ЕГЭ не подходит, пропускаем")
#             return results
#     except WebDriverException as e:
#         logger.warning(f"  Ошибка при проверке ЕГЭ-комбинации: {e}")
#         return results
#
#     # Сбор ссылок направлений
#     try:
#         elems = driver.find_elements(By.CSS_SELECTOR, "a.linknapWoutActive, a.napravlenie-link, .direction-link")
#     except Exception:
#         elems = []
#     seen_dirs = set()
#     dirs = []
#     for e in elems:
#         try:
#             href = e.get_attribute("href")
#         except StaleElementReferenceException:
#             continue
#         if href and href not in seen_dirs:
#             seen_dirs.add(href)
#             dirs.append(href)
#     logger.info(f"  Найдено направлений: {len(dirs)}")
#     for d_url in dirs:
#         logger.info(f"    Открываем направление: {d_url}")
#         try:
#             driver.get(d_url)
#             WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
#             time.sleep(0.3)
#         except TimeoutException:
#             logger.warning(f"      Не загрузилось направление: {d_url}")
#             continue
#         # Сбор ссылок программ
#         try:
#             pe = driver.find_elements(By.CSS_SELECTOR, "a.newItemSpPrTitle, a.program-item-link, .program-link")
#         except Exception:
#             pe = []
#         seen_pr = set()
#         progs = []
#         for p in pe:
#             try:
#                 href = p.get_attribute("href")
#             except StaleElementReferenceException:
#                 continue
#             if href and "/program" in href and href not in seen_pr:
#                 seen_pr.add(href)
#                 progs.append(href)
#         logger.info(f"      Найдено программ: {len(progs)}")
#         for p_url in progs:
#             logger.info(f"        Открываю программу: {p_url}")
#             try:
#                 driver.get(p_url)
#                 WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
#                 # Некоторая пауза, чтобы успела отрисоваться
#                 time.sleep(0.2)
#             except TimeoutException:
#                 logger.warning(f"          Не загрузилась страница программы: {p_url}")
#                 continue
#             title = ""
#             try:
#                 title = driver.find_element(By.CSS_SELECTOR, "h1, .program-title").text.strip()
#             except Exception:
#                 pass
#             results.append((p_url, title))
#     return results
#
# def collect_university_links(main_page: MainPage, driver, timeout=10):
#     """
#     С помощью MainPage обходим страницы фильтра, получаем упорядоченный список ссылок на вузы.
#     Постранично: пока get_university_links() возвращает новые ссылки.
#     """
#     all_links = []
#     page_index = 1
#     # Перед первым вызовом open_with_filters не забудьте очистить состояние
#     while True:
#         logger.info(f"Открываем фильтрованную страницу, page={page_index}")
#         try:
#             # Здесь MainPage.open_with_filters переходит на нужную страницу:
#             # Если в MainPage реализован метод с page-параметром — используем его. Предположим:
#             main_page.open_with_filters(CITY_ID, DIRECTION_ID, {"page": page_index})
#         except Exception as e:
#             logger.warning(f"Не удалось открыть фильтрованную страницу {page_index}: {e}")
#             break
#
#         # Предположим, get_university_links возвращает список ссылок на вузы на текущей странице
#         try:
#             links = main_page.get_university_links()
#         except Exception as e:
#             logger.warning(f"get_university_links() упал на странице {page_index}: {e}")
#             break
#         # Удаляем дубли, сохраняя порядок
#         new_count = 0
#         for link in links:
#             link = link.rstrip("/")
#             if link not in all_links:
#                 all_links.append(link)
#                 new_count += 1
#         logger.info(f"  Страница {page_index}: найдено вузов на этой странице: {len(links)}, новых: {new_count}, всего накоплено: {len(all_links)}")
#         # Если на этой странице новых не появилось, выходим
#         if new_count == 0:
#             break
#         page_index += 1
#         # Небольшая пауза перед переходом
#         time.sleep(0.5)
#     logger.info(f"Итоговый список вузов: {len(all_links)}")
#     return all_links
#
# def create_driver():
#     opts = Options()
#     # opts.add_argument("--headless=new")
#     opts.add_argument("--log-level=3")
#     driver = webdriver.Chrome(options=opts)
#     driver.set_page_load_timeout(30)
#     driver.implicitly_wait(5)
#     return driver
#
# def main():
#     base_url = "https://vuzopedia.ru"
#     global CITY_ID, DIRECTION_ID
#
#     driver = create_driver()
#     try:
#         main_page = MainPage(driver, timeout=10, logger=logger, base_url=base_url)
#         # Собираем ссылки вузов
#         uni_links = collect_university_links(main_page, driver)
#
#         if not uni_links:
#             logger.info("Список вузов пуст, выходим.")
#             return
#
#         all_programs = []
#         skipped = []
#         restart_every = 20  # перезапускать драйвер после каждых 20 вузов
#         for idx, uni_url in enumerate(uni_links, start=1):
#             # При краше вкладки — поймаем WebDriverException и перезапустим
#             try:
#                 progs = process_university(driver, uni_url)
#                 all_programs.extend(progs)
#             except WebDriverException as e:
#                 logger.error(f"WebDriverException при обработке {uni_url}: {e}. Перезапускаем драйвер и продолжаем.")
#                 skipped.append(uni_url)
#                 # перезапуск драйвера
#                 try:
#                     driver.quit()
#                 except:
#                     pass
#                 driver = create_driver()
#                 main_page = MainPage(driver, timeout=10, logger=logger, base_url=base_url)
#                 # вернуться к фильтру и текущей странице, чтобы продолжить?
#                 # Простейше: продолжаем со следующего индекса, т.к. ссылки уже в uni_links.
#                 continue
#
#             # Периодический перезапуск драйвера, чтобы избежать утечек
#             if idx % restart_every == 0 and idx < len(uni_links):
#                 logger.info(f"Перезапуск драйвера после {idx} вузов для предотвращения утечек.")
#                 try:
#                     driver.quit()
#                 except:
#                     pass
#                 driver = create_driver()
#                 main_page = MainPage(driver, timeout=10, logger=logger, base_url=base_url)
#
#             # Пауза между вузами
#             time.sleep(0.5)
#
#         logger.info(f"Готово. Всего программ собрано: {len(all_programs)}. Пропущено вузов (из-за ошибок): {len(skipped)}")
#         if skipped:
#             logger.info("Список пропущенных вузов:")
#             for u in skipped:
#                 logger.info(f"  {u}")
#         # Пример: вывести первые 5 программ
#         for url, title in all_programs[:5]:
#             logger.info(f"  Программа: {url} → {title}")
#
#     finally:
#         try:
#             driver.quit()
#         except:
#             pass
#
# if __name__ == "__main__":
#     main()


# -*- coding: utf-8 -*-
import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)
from vuzopedia_parser.pages.main_page import MainPage

# --- Настройка логирования ---
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("main")
# Отключаем шумные логи Selenium/urllib3
logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

CITY_ID = 59
DIRECTION_ID = 5

def normalize_subject(s: str) -> str:
    s = s.strip().lower()
    s = s.replace("русский язык", "русский")
    s = s.replace("математика (профильная)", "математика")
    s = s.replace("математика профильная", "математика")
    s = s.replace("информатика и икт", "информатика")
    return s.split('(')[0].strip()

def click_show_all_combinations(driver, timeout=5) -> bool:
    """
    На главной странице вуза кликает кнопку "Посмотреть все" комбинаций (buttonNewCombActive) и дожидается перехода на /kakie-ege-sdavat.
    Возвращает True если кликнули и перешли, False otherwise.
    """
    try:
        # Ждём, пока элемент появится
        el = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.buttonNewCombActive"))
        )
    except TimeoutException:
        return False
    try:
        # Прокрутка и клик
        driver.execute_script("arguments[0].scrollIntoView(true);", el)
        time.sleep(0.2)
        try:
            el.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", el)
        # Ждём перехода на URL заканчивающийся /kakie-ege-sdavat
        WebDriverWait(driver, timeout).until(EC.url_contains("/kakie-ege-sdavat"))
        return True
    except Exception:
        return False

def find_and_click_target_combination(driver, timeout=5) -> bool:
    """
    Предполагаем, что находимся на странице /kakie-ege-sdavat.
    Ищем среди комбинаций блок с Математика+Русский+Информатика, кликаем его кнопку "Посмотрите варианты" (div.buttonNewComb).
    Возвращаем True если кликнули, False otherwise.
    """
    target_subjects = {"русский", "математика", "информатика"}
    # Ждём появления элементов комбинаций
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.itemBlockCombLink"))
        )
    except TimeoutException:
        # Может быть нужный селектор другой, но попробуем всё равно искать текстовые блоки ниже
        pass

    # Перебираем все блоки комбинаций
    try:
        combo_blocks = driver.find_elements(By.CSS_SELECTOR, "a.itemBlockCombLink")
    except Exception:
        combo_blocks = []
    for link in combo_blocks:
        try:
            href = link.get_attribute("href") or ""
        except StaleElementReferenceException:
            continue
        # внутри каждого блока комбинации есть <div class="blockItemComb"> с предметами
        # соберём тексты
        try:
            # на некоторых комбинациях может быть active-класс
            items = link.find_elements(By.CSS_SELECTOR, "div.blockItemComb div.itemNewBlockComb, div.blockItemComb div.itemNewBlockCombActive")
            parts = []
            for it in items:
                t = it.text.strip()
                if t:
                    parts.append(t)
            # Если items пусто, можно попробовать разобрать текст всей ссылки
            if not parts:
                raw = link.text.strip()
                if raw:
                    # разбить по переносам или запятым или точке с запятой
                    if '\n' in raw:
                        parts = [x.strip() for x in raw.split('\n') if x.strip()]
                    elif ',' in raw:
                        parts = [x.strip() for x in raw.split(',') if x.strip()]
                    elif ';' in raw:
                        parts = [x.strip() for x in raw.split(';') if x.strip()]
                    else:
                        # собрать дочерние:
                        for c in link.find_elements(By.XPATH, ".//*"):
                            txt = c.text.strip()
                            if txt:
                                parts.append(txt)
                        if not parts:
                            parts = [raw]
            normalized = {normalize_subject(p) for p in parts if p.strip()}
            if normalized == target_subjects:
                # нашли нужную комбинацию
                # внутри link надо найти кнопку "Посмотрите варианты": div.buttonNewComb
                try:
                    btn = link.find_element(By.CSS_SELECTOR, "div.buttonNewComb")
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    time.sleep(0.1)
                    try:
                        btn.click()
                    except ElementClickInterceptedException:
                        driver.execute_script("arguments[0].click();", btn)
                    # Ждём, что URL содержит /poege/
                    try:
                        WebDriverWait(driver, timeout).until(EC.url_contains("/poege/"))
                    except TimeoutException:
                        pass
                    # После клика можно вернуться на главную страницу вуза
                    # Получаем базовый URL университета (до /poege/)
                    curr = driver.current_url
                    base = curr.split("/poege/")[0]
                    try:
                        driver.get(base)
                        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
                    except:
                        pass
                    return True
                except Exception:
                    # не удалось найти или кликнуть кнопку
                    return False
        except Exception:
            continue
    return False

def has_target_ege_combination(driver, timeout=5) -> bool:
    """
    Общая функция: на главной странице вуза кликает "Посмотреть все" комбинаций,
    ждёт /kakie-ege-sdavat, затем ищет нужную комбинацию и кликает её.
    Если нет кнопки "Посмотреть все", можно попытаться напрямую открыть /kakie-ege-sdavat.
    """
    uni_url = driver.current_url
    # 1) Попробуем кликнуть кнопку "Посмотреть все" на главной странице
    clicked = False
    try:
        clicked = click_show_all_combinations(driver, timeout)
    except WebDriverException:
        clicked = False

    if clicked:
        # уже перешли на /kakie-ege-sdavat, теперь ищем нужную комбинацию
        try:
            ok = find_and_click_target_combination(driver, timeout)
            return ok
        except WebDriverException:
            return False
    # 2) Если нет кнопки или не перешло, попробуем напрямую перейти на /kakie-ege-sdavat
    combo_url = uni_url.rstrip('/') + '/kakie-ege-sdavat'
    try:
        driver.get(combo_url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.itemBlockCombLink, div.blockItemComb"))
        )
        # Теперь на странице комбинаций, ищем нужную комбинацию:
        try:
            ok = find_and_click_target_combination(driver, timeout)
            return ok
        except WebDriverException:
            # вернуться назад
            driver.get(uni_url)
            return False
    except Exception:
        # не получилось напрямую — вернёмся на главную страницу
        try:
            driver.get(uni_url)
        except:
            pass
    # 3) Если не найдена кнопка и не удалось открыть напрямую, можно попытаться на месте парсить текстовые блоки,
    # но этот кейс уже охвачен ранее, поэтому считаем, что комбинация не найдена.
    return False

def process_university(driver, uni_url, timeout=10):
    """
    Открываем страницу университета, проверяем ЕГЭ-комбинацию, затем парсим направления и программы.
    """
    results = []
    logger.info(f"Открываем вуз: {uni_url}")
    try:
        driver.get(uni_url)
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
    except TimeoutException:
        logger.warning(f"  Не загрузилась страница вуза: {uni_url}")
        return results

    try:
        if not has_target_ege_combination(driver, timeout):
            logger.info("  → комбинация ЕГЭ не подходит, пропускаем")
            return results
    except WebDriverException as e:
        logger.warning(f"  Ошибка при проверке ЕГЭ-комбинации: {e}")
        return results

    # Сбор ссылок направлений
    try:
        elems = driver.find_elements(By.CSS_SELECTOR, "a.linknapWoutActive, a.napravlenie-link, .direction-link")
    except Exception:
        elems = []
    seen_dirs = set()
    dirs = []
    for e in elems:
        try:
            href = e.get_attribute("href")
        except StaleElementReferenceException:
            continue
        if href and href not in seen_dirs:
            seen_dirs.add(href)
            dirs.append(href)
    logger.info(f"  Найдено направлений: {len(dirs)}")
    for d_url in dirs:
        logger.info(f"    Открываем направление: {d_url}")
        try:
            driver.get(d_url)
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
            time.sleep(0.3)
        except TimeoutException:
            logger.warning(f"      Не загрузилось направление: {d_url}")
            continue
        # Сбор ссылок программ
        try:
            pe = driver.find_elements(By.CSS_SELECTOR, "a.newItemSpPrTitle, a.program-item-link, .program-link")
        except Exception:
            pe = []
        seen_pr = set()
        progs = []
        for p in pe:
            try:
                href = p.get_attribute("href")
            except StaleElementReferenceException:
                continue
            if href and "/program" in href and href not in seen_pr:
                seen_pr.add(href)
                progs.append(href)
        logger.info(f"      Найдено программ: {len(progs)}")
        for p_url in progs:
            logger.info(f"        Открываю программу: {p_url}")
            try:
                driver.get(p_url)
                WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
                time.sleep(0.2)
            except TimeoutException:
                logger.warning(f"          Не загрузилась страница программы: {p_url}")
                continue
            title = ""
            try:
                title = driver.find_element(By.CSS_SELECTOR, "h1, .program-title").text.strip()
            except Exception:
                pass
            results.append((p_url, title))
    return results

def collect_university_links(main_page: MainPage, driver, timeout=10):
    """
    Собирает все ссылки вузов из отфильтрованного списка, постранично, пока появляются новые.
    """
    all_links = []
    page_index = 1
    while True:
        logger.info(f"Открываем фильтрованную страницу, page={page_index}")
        try:
            # Если MainPage.open_with_filters поддерживает передачу page, передаём:
            main_page.open_with_filters(CITY_ID, DIRECTION_ID, {"page": page_index})
        except Exception as e:
            logger.warning(f"Не удалось открыть отфильтрованную страницу page={page_index}: {e}")
            break

        try:
            links = main_page.get_university_links()
        except Exception as e:
            logger.warning(f"get_university_links() упал на странице {page_index}: {e}")
            break
        new_count = 0
        for link in links:
            link = link.rstrip("/")
            if link not in all_links:
                all_links.append(link)
                new_count += 1
        logger.info(f"  Страница {page_index}: найдено вузов: {len(links)}, новых: {new_count}, всего накоплено: {len(all_links)}")
        if new_count == 0:
            break
        page_index += 1
        time.sleep(0.5)
    logger.info(f"Итоговый список вузов: {len(all_links)}")
    return all_links

def create_driver():
    opts = Options()
    # при необходимости headless:
    # opts.add_argument("--headless=new")
    opts.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(5)
    return driver

def main():
    base_url = "https://vuzopedia.ru"
    driver = create_driver()
    try:
        main_page = MainPage(driver, timeout=10, logger=logger, base_url=base_url)
        uni_links = collect_university_links(main_page, driver)
        if not uni_links:
            logger.info("Список вузов пуст, выходим.")
            return

        all_programs = []
        skipped = []
        restart_every = 20
        for idx, uni_url in enumerate(uni_links, start=1):
            try:
                progs = process_university(driver, uni_url)
                all_programs.extend(progs)
            except WebDriverException as e:
                logger.error(f"WebDriverException при обработке {uni_url}: {e}. Перезапуск драйвера.")
                skipped.append(uni_url)
                try:
                    driver.quit()
                except:
                    pass
                driver = create_driver()
                main_page = MainPage(driver, timeout=10, logger=logger, base_url=base_url)
                continue
            if idx % restart_every == 0 and idx < len(uni_links):
                logger.info(f"Перезапуск драйвера после {idx} вузов для сброса памяти.")
                try:
                    driver.quit()
                except:
                    pass
                driver = create_driver()
                main_page = MainPage(driver, timeout=10, logger=logger, base_url=base_url)
            time.sleep(0.5)

        logger.info(f"Готово. Всего программ собрано: {len(all_programs)}; пропущено вузов: {len(skipped)}")
        if skipped:
            logger.info("Список пропущенных вузов:")
            for u in skipped:
                logger.info(f"  {u}")
        for url, title in all_programs[:5]:
            logger.info(f"  Программа: {url} → {title}")

    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()

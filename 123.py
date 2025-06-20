from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
import time
import openpyxl

CHROMEDRIVER_PATH = r"C:\chromedriver\chromedriver.exe"
BASE_URL = "https://vuzopedia.ru"
START_URL = f"{BASE_URL}/moskva/target-company"

options = Options()
options.add_argument("--disable-gpu")

print("⏳ Запускаю Chrome...")
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

# Excel и TXT инициализация
wb = openpyxl.Workbook()
ws = wb.active
ws.append(["Название", "Тип", "Ссылка", "Специальности"])

txt_file = open("companies.txt", "w", encoding="utf-8")

def parse_companies():
    shadow_blocks = driver.find_elements(By.CLASS_NAME, "shadowForItem")
    for block in shadow_blocks:
        try:
            parent_a = block.find_element(By.XPATH, "./ancestor::a")
            link = urljoin(BASE_URL, parent_a.get_attribute("href"))
        except:
            link = "❌ ссылка не найдена"

        try:
            span = block.find_element(By.TAG_NAME, "span").text.strip()
        except:
            span = "❌ тип не найден"

        try:
            name = block.text.replace(span, "").strip()
        except:
            name = "❌ название не найдено"

        print("📌 Компания:")
        print(f"  🔗 Ссылка: {link}")
        print(f"  🏷️ Тип: {span}")
        print(f"  🏢 Название: {name}")

        specialties = []
        if link.startswith(BASE_URL):
            driver.execute_script("window.open(arguments[0]);", link)
            driver.switch_to.window(driver.window_handles[1])
            time.sleep(2)

            try:
                spec_blocks = driver.find_elements(By.CLASS_NAME, "blockNewItem")
                for sb in spec_blocks:
                    try:
                        title = sb.find_element(By.CLASS_NAME, "newItemSpPrTitle").text.strip()
                        specialties.append(title)
                    except:
                        pass
            except:
                pass

            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        ws.append([name, span, link, "\n".join(specialties)])
        txt_file.write(f"Название: {name}\nТип: {span}\nСсылка: {link}\nСпециальности:\n")
        for spec in specialties:
            txt_file.wr\\\\\\ite(f" - {spec}\n")
        txt_file.write("\n" + "-"*50 + "\n")

        print(f"  📚 Специальностей найдено: {len(specialties)}")
        print("-" * 50)

try:
    print(f"🌐 Открываю сайт: {START_URL}")
    driver.get(START_URL)
    time.sleep(2)

    while True:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "shadowForItem"))
        )

        print(f"\n🔄 Парсинг страницы: {driver.current_url}")
        parse_companies()

        try:
            next_button = driver.find_element(By.CSS_SELECTOR, 'li.page-item.last > a.page-link[rel="next"]')
            next_link = next_button.get_attribute("href")
            print("➡️ Переход на следующую страницу...")
            driver.get(next_link)
            time.sleep(2)
        except:
            print("✅ Последняя страница достигнута.")
            break

except Exception as e:
    print(f"❌ Ошибка при парсинге: {e}")

finally:
    driver.quit()
    wb.save("companies.xlsx")
    txt_file.close()
    print("💾 Сохранено в Excel и TXT")
    print("🚪 Браузер закрыт.")

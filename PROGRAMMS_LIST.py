import requests
from requests.adapters import HTTPAdapter, Retry
import pandas as pd

# 1. URL страницы
url = "https://propostuplenie.ru/article/polnyj-perechen-specialnostej-i-napravlenij-podgotovki-vysshego-obrazovaniya#+++++++++++"

# 2. Создаём сессию с ретраями
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET"]
)
session.mount("https://", HTTPAdapter(max_retries=retries))

# 3. Делаем запрос
resp = session.get(url, timeout=30, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
})
resp.raise_for_status()
html = resp.text

# 4. Читаем все таблицы из скачанного HTML
tables = pd.read_html(html, encoding="utf-8")
print(f"Найдено таблиц: {len(tables)}")
for idx, df in enumerate(tables):
    print(f"Таблица {idx}: shape={df.shape}, columns={list(df.columns)}")

# 5. Предположим, что бакалавриат — в таблице 0, специалист — в таблице 1
df_bach = tables[0].copy()
df_spec = tables[1].copy()

# 6. Добавляем столбец с уровнем подготовки
df_bach["Уровень"] = "Бакалавриат"
df_spec["Уровень"] = "Специалист"

# 7. Объединяем и сохраняем
df_full = pd.concat([df_bach, df_spec], ignore_index=True)
output_file = "Полный_список_бакалавриата_и_специалиста.xlsx"
df_full.to_excel(output_file, index=False)

print(f"Экспорт завершён: {output_file}")

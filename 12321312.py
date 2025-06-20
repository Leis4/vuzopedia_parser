import requests
import pandas as pd

# Функция загрузки JSON по ID программы
def fetch_program_json(pid):
    url = f"https://vuzopedia.ru/api/v2/programs/{pid}"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

# Парсинг одного объекта JSON в словарь
def parse_program_json(j, pid, city, university_short):
    return {
        "ID программы": pid,
        "Вуз": j.get("university", {}).get("title", university_short),
        "Город": j.get("university", {}).get("city", city),
        "Название программы": j.get("title", ""),
        "Код направления": j.get("code", ""),
        "Уровень": j.get("level", ""),
        "Количество бюджетных мест": j.get("budget_places", ""),
        "Количество платных мест": j.get("paid_places", ""),
        "Стоимость обучения": j.get("tuition", ""),
        "Проходной балл 2024": j.get("passing_score", ""),
        "Минимальный балл ЕГЭ": j.get("min_score", ""),
        "Предметы ЕГЭ": ", ".join([e.get("subject") for e in j.get("subjects", [])]),
        "Общежитие": "да" if j.get("has_hostel") else "нет",
        "Ссылка": f"https://vuzopedia.ru/vuz/{j['university']['id']}/programs/bakispec/{pid}"
    }

# Основной цикл сбора данных
results = []
for pid, university_short, city in program_data:
    try:
        js = fetch_program_json(pid)
        results.append(parse_program_json(js, pid, city, university_short))
    except Exception as e:
        results.append({
            "ID программы": pid,
            "Вуз": university_short,
            "Город": city,
            "Ошибка": str(e)
        })

# Формируем DataFrame
df = pd.DataFrame(results)
df.head()

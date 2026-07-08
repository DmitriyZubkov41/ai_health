import pandas as pd
from psycopg2 import connect
from dotenv import load_dotenv
import os

#from pprint import pprint

def get_date(val):
    if pd.isna(val):
        return pd.NA
    if hasattr(val, 'strftime'):
        return val.strftime('%d.%m.%Y')
    # Для строк
    date_part = str(val).split('\n')[0].split(' ')[0]
    if '-' in date_part:
        y, m, d = date_part.split('-')
        return f"{d}.{m}.{y}"
    return date_part


load_dotenv()
password=os.getenv("DB_PASSWORD")
user=os.getenv("DB_USER")
path_catalog=os.getenv("PATH_CATALOG")

# Подключение к БД
conn = connect(
    host="localhost",
    port=5432,
    database="db_health",
    user=user,
    password=password
)
cursor = conn.cursor()

df = pd.read_excel(f'{path_catalog}/Analiz.xlsx', sheet_name='Анализы', header=1)

# Извлекаем дату
df['Дата_чистая'] = df['Дата'].apply(get_date)
df['Дата'] = pd.to_datetime(df['Дата_чистая'], format='%d.%m.%Y').dt.date

# Извлекаем лабораторию (если есть)
df['Лаборатория'] = df['Дата'].apply(
    lambda x: str(x).split('\n')[1].strip() if len(str(x).split('\n')) > 1 else None
)
#print(df[['Дата_чистая', 'Лаборатория']].head())
df = df.drop('Дата_чистая', axis=1)

#print("\nПосле преобразований:")
#print(df.head())
# Список показателей, которые нужно перенести
data = []

for i, row in df.iterrows():
    data.append((
        row['Дата'],
        row['Лаборатория'],
        row['25 (OH) Витамин D'],
        row['B-12 витамин пг/мл'],
        row['Белок C-реактивный, мг/дл'],
        row['Ревматоидный фактор мЕ/мл'],
        row['Группа крови'],
        row['Резус принадлежность'],
        row['Аланинаминотрансфераза (АлАТ) Ед/л'],
        row['Аспартатаминотрансфераза (ФсАт)'],
        row['Фосфатаза щелочная'],
        row['Лактатдегидрогеназа (ЛДГ)'],
        row['Амилаза Ед/л или МЕ/л'],
        row['Липаза'],
        row['Гамма-глутамилтрансфераза (ГГТ)'],
        row['Альфафетопротеин (АФП)'],
        row['Простатический специфический антиген общий (ПСА общий)'],
        row['ПСА свободный'],
        row['Пролактин'],
        row['Исследование Янус-киназы Jak2'],
        row['Холестерин общий'],
        row['Гомоцистеин, мкмоль/л'],
        row['Фолиевая кислота, нг/мл'],
        row['Микроскопическое исследование кала на гельминты с применением методов обогащения (PARASEP®)'],
        row['Кальпротектин,  мг/г'],
        row['Исследование кала (копрограмма) (качественный)']
    ))
#print("\n_______________________________")
#pprint(data[:5])  # Покажем первые 5 записи

sql_query = """
    INSERT INTO lab_analiz 
    ("Дата", "Лаборатория", "Витамин D", "Витамин B-12", "Белок C-реактивный",
     "Ревматоидный фактор", "Группа крови", "Резус принадлежности", "Аланинаминотрансфераза (АлАТ)",
    "Аспартатаминотрансфераза (ФсАт)", "Фосфатаза щелочная", "Лактатдегидрогеназа (ЛДГ)",
    "Амилаза", "Липаза", "Гамма-глутамилтрансфераза (ГГТ)", "Альфафетопротеин (АФП)",
    "ПСА общий", "ПСА свободный", "Пролактин", "Исследование Янус-киназы Jak2", "Холестерин общий",
    "Гомоцистеин", "Фолиевая кислота", "Исследование кала на гельминты",
    "Кальпротектин", "Копрограмма") 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
      %s, %s, %s, %s, %s, %s)
"""
cursor.executemany(sql_query, data)

conn.commit()  
cursor.close()
conn.close()
print(f"✅ Перенесено {len(df)} записей в lab_analiz")
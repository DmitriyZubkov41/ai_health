import pandas as pd
from psycopg2 import connect
from dotenv import load_dotenv
import os

from pprint import pprint

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

# 1. Переносим данные из Показатели.xlsx
df = pd.read_excel(f'{path_catalog}/Показатели.xlsx')
df['Дата'] = pd.to_datetime(df['Дата']).dt.date
df['Дата'] = df['Дата'].ffill()
#df['Время'] = df['Время'].astype(str)
df['Время'] = df['Время'].where(pd.notna(df['Время']), None)
#print("\nПосле преобразований:")
#print(df[['Дата', 'Время']].head())
# Список показателей, которые нужно перенести
data = []
for i, row in df.iterrows():
    data.append((
        row['Дата'],
        row['Время'],
        row['Верхнее давление'],
        row['Нижнее давление'],
        row['Пульс'],
        row['Вес'],
        row['Сахар'],
        row['Температура'],
        row['Примечание']
    ))
print("\n_______________________________")
pprint(data[:5])  # Покажем первые 5 записи

sql_query = """
    INSERT INTO metrics 
    ("Дата", "Время", "Верхнее давление", "Нижнее давление", 
     "Пульс", "Вес", "Сахар", "Температура", "Примечание") 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
cursor.executemany(sql_query, data)

conn.commit()  
cursor.close()
conn.close()
print(f"✅ Перенесено {len(df)} записей в health_metrics")
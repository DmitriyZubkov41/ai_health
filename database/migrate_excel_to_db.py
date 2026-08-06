import pandas as pd
from psycopg2 import connect
from psycopg2.extras import execute_values
from datetime import datetime
from dotenv import load_dotenv
import os

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
def migrate_health_metrics():
    df = pd.read_excel(f'{path_catalog}/Показатели.xlsx')
    df['Дата'] = pd.to_datetime(df['Дата']).dt.date
    
    # Список показателей, которые нужно перенести
    metrics = ['Вес', 'Верхнее давление', 'Нижнее давление', 'Пульс', 'Сахар', 'Температура', 'Примечание']
    
    #data = []
    for _, row in df.iterrows():
        sql = f"INSERT INTO health_metrics ('Дата', 'Верхнее давление', 'Нижнее давление', 'Пульс', 'Сахар', 'Температура',\
          'Примечание') VALUES ({row})"
        cursor.exucate(sql)

    print(f"✅ Перенесено {len(data)} записей в health_metrics")

# 2. Переносим данные из Analiz.xlsx
def migrate_lab_results():
    list_sheets = ['Анализы', 'ОАК', 'Биохимич.', 'Инфекции', 'Металлы', 'Коагуляция', 'Гормоны',\
                    'Аллергия']
    
    df = pd.read_excel(f'{path_catalog}/Analiz.xlsx', sheet_name='Анализы', header=1)
    for _, row in df.iterrows():
        sql = "INSERT INTO lab_allergiya ('Дата', 'Лаборатория', "Витамин D",\
    "Витамин B-12", "Ревматоидный фактор", "Группа крови", "Резус принадлежности",\
    "Аланинаминотрансфераза (АлАТ)", "Аспартатаминотрансфераза (ФсАт)", "Фосфатаза щелочная",\
    "Лактатдегидрогеназа (ЛДГ)", "Амилаза", "Липаза", "Гамма-глутамилтрансфераза (ГГТ)",\
    "Альфафетопротеин (АФП)", "ПСА общий", "ПСА свободный", "Пролактин", "Исследование Янус-киназы Jak2",\
    "Гомоцистеин", "Фолиевая кислота", "Белок С- реактивный", "Исследование кала на гельминты",\
    "Кальпротектин", "Копрограмма") VALUES %s"
        cursor.exucate(sql)
        print(f"✅ Перенесено {len(data)} записей в health_metrics")


    for sheet in list_sheets:
        df = pd.read_excel(f'{path_catalog}/Analiz.xlsx', sheet_name=sheet)
        
        data = []
        for _, row in df.iterrows():
        if 'Показатель' in df.columns and 'Значение' in df.columns:
            param = row.get('Показатель')
            value = row.get('Значение')
            norm = row.get('Норма', '')
            unit = row.get('Единицы', '')
            
            if pd.notna(param) and pd.notna(value):
                data.append((param, float(value), str(norm), unit, datetime.now().date()))
    
    if data:
        execute_values(
            cursor,
            "INSERT INTO lab_results (parameter, value, norm_value, unit, recorded_at) VALUES %s",
            data
        )
        print(f"✅ Перенесено {len(data)} записей в lab_results")

if __name__ == "__main__":
    try:
        migrate_health_metrics()
        migrate_lab_results()
        conn.commit()
        print("🎉 Миграция завершена успешно!")
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка: {e}")
    finally:
        cursor.close()
        conn.close()
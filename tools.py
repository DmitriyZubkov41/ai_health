import pandas as pd
from datetime import date
import json
from dotenv import load_dotenv
import os
from database.db import get_db_engine


load_dotenv()
path_catalog=os.getenv("PATH_CATALOG")
password=os.getenv("DB_PASSWORD")
user=os.getenv("DB_USER")

   
def get_current_date():
    result = {
        "status": "success",
        "date": date.today().strftime("%d.%m.%Y")
    }
    return json.dumps(result, ensure_ascii=False)


def get_health_metric(metric_name: str = None):
    """
    Получает показатели здоровья из db_health таблица metrics
    """
    engine = get_db_engine() 
    try:
        query = f"SELECT Дата, {metric_name} FROM metrics"
                
        df = pd.read_sql(query, engine)
        return df
    finally:
        engine.dispose()


def get_analiz_from_excel(parameters: list) -> str:
    """
    Получает результаты анализов из Excel-файла.
    Returns:
        str: JSON-строка с результатами
    """
    try:
        # Загружаем Excel
        list_df = pd.read_excel(f"{path_catalog}/Analiz.xlsx", sheet_name=None)
        
        # Ищем колонки, соответствующие параметрам
        list_find_columns = []
        for pokazatel in parameters:
            for df in list_df:
                for df_column in df.columns:
                    if pokazatel.lower() in df_column.lower():
                        list_find_columns.append(df_column)
                        break
        
        if not list_find_columns:
            return json.dumps({
                "status": "error",
                "message": f"Ни один из показателей {parameters} не найден в Analiz.xlsx"
            }, ensure_ascii=False)
        
        df_filtr = df[["Дата"] + list_find_columns].copy()
        
        # Преобразуем даты в строки
        df_filtr["Дата"] = pd.to_datetime(df_filtr["Дата"]).dt.strftime('%d.%m.%Y')
        
        # Заменяем NaN на None (для корректной JSON-сериализации)
        df_filtr = df_filtr.where(pd.notna(df_filtr), None)
        
        # Преобразуем в список словарей
        data_records = df_filtr.to_dict(orient='records')
        
        result = {
            "status": "success",
            "data": data_records,
            "columns": df_filtr.columns.tolist(),
            "norms": {},
            "message": f"Найдены данные по {len(list_find_columns)} показателям"
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Ошибка: {str(e)}"
        }, ensure_ascii=False)




# Описание функций
giga_functions = [
    {
        "name": "get_current_date",
        "description": f"Получить текущую дату",
        "parameters": {
            "type": 'object',
            "properties": {},
            "required": []
        }
    },
    
    {
        "name": "get_analiz_from_excel",
        "description": "Получить результаты лабораторных анализов",
        "parameters": {
            "type": "object",
            "properties": {
                "parameters": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Список показателей анализа крови, например: ['Тромбоциты'] или ['Тромбоциты', 'Эритроциты', 'Гемоглобин']"
                }
            },
            "required": ["parameters"]
        }
    },
]


# Словарь функций
function_dict = {
    "get_current_date": get_current_date,
    "get_analiz_from_excel": get_analiz_from_excel
}
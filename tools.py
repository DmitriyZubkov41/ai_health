import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, date
import json
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from psycopg2 import connect
from psycopg2.extras import Json
import io
import base64


load_dotenv()
path_catalog=os.getenv("PATH_CATALOG")
password=os.getenv("DB_PASSWORD")
user=os.getenv("DB_USER")

def make_plot(metric: str) -> json:
    """Построить график показателя (вес, давление и т.д.)"""
    try:
        df = get_health_metric(metric_name=metric)
        df['Дата'] = pd.to_datetime(df['Дата'])
        df = df[['Дата', metric]]

        # Строим график
        plt.figure(figsize=(12, 6))
        plt.plot(df['Дата'], df[metric], marker='o', linewidth=2, color='#667eea', markersize=8)
        plt.title(f"Динамика показателя '{metric}'", fontsize=16, fontweight='bold')
        plt.xlabel("Дата", fontsize=12)
        plt.ylabel(metric, fontsize=12)
        plt.grid(True, alpha=0.3)
        #plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Сохраняем график в буфер (в память, а не на диск)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        # Кодируем в base64
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        result = {
            "status": "success",
            "image": f"data:image/png;base64,{img_base64}",  # ← сразу картинка для браузера
            "message": f"График показателя '{metric}' успешно построен"
        }
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Ошибка: {str(e)}"
        }, ensure_ascii=False)
    


def get_current_date():
    result = {
        "status": "success",
        "date": date.today().strftime("%d.%m.%Y")
    }
    return json.dumps(result, ensure_ascii=False)


def get_db_engine():
    """Создаём движок для работы с БД"""
    db_url = f"postgresql://{user}:{password}@localhost:5432/db_health"
    return create_engine(db_url)


def get_health_metric(metric_name: str = None):
    """
    Получает показатели здоровья из bd_health / metrics
    """
    engine = get_db_engine() 
    try:
        query = f"SELECT Дата, {metric_name} FROM metrics"
                
        df = pd.read_sql(query, engine)
        return df
    finally:
        engine.dispose()


def get_analiz_results(parameters: list) -> str:
    """Получает все анализы из таблицы lab_analiz
       parameters: Список показателей: ['Тромбоциты'] или ['Тромбоциты', 'Эритроциты']
    """
    engine = get_db_engine()
    
    try:
        if isinstance(parameters, str):
            parameters = [parameters]

        # Экранируем имена колонок двойными кавычками
        quoted_params = [f'"{p}"' for p in parameters]
        columns_str = ', '.join(quoted_params)
        print("columns_str", columns_str)
        
        query = f"SELECT Дата, {columns_str} FROM lab_analiz"
        df = pd.read_sql(query, engine)
        
        # Если данных нет, возвращаем сообщение об ошибке
        if df.empty:
            return json.dumps({
                "status": "error",
                "message": f"Показатели {', '.join(parameters)} не найдены в таблице lab_analiz"
            }, ensure_ascii=False)
        
        # Преобразуем даты в строковый формат
        if 'Дата' in df.columns:
            df['Дата'] = pd.to_datetime(df['Дата']).dt.strftime('%d.%m.%Y')

        df = df.dropna(subset=parameters, how='all')
        df = df.where(pd.notna(df), None)
        
        # Преобразуем DataFrame в список словарей (JSON-совместимый формат)
        data_records = df.to_dict(orient='records')
        
        result = {
            "status": "success",
            "data": data_records,
            "columns": df.columns.tolist(),
            "message": f"Найдены данные по {len(parameters)} показателям"
        }
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Ошибка получения данных: {str(e)}"
        }, ensure_ascii=False)
        
    finally:
        engine.dispose()


# Функции для сохранения чата
def get_db_connection():
    return connect(dbname="db_health", host="localhost", user=user, password=password, port="5432")


def save_message_to_db(session_id: str, role: str, content: str = None, 
                       function_call: dict = None, function_name: str = None):
    """Сохраняет сообщение в базу данных"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Преобразуем function_call в JSON, если он есть
        function_call_json = Json(function_call) if function_call else None
        
        cursor.execute(
            """
            INSERT INTO chat_history (session_id, role, content, function_call, function_name)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (session_id, role, content, function_call_json, function_name)
        )
        conn.commit()
        print(f"💾 Сохранено сообщение в БД: role={role}, session={session_id[:8]}...")
    except Exception as e:
        print(f"❌ Ошибка сохранения в БД: {e}")
        conn.rollback()
    finally:
        conn.close()

def load_history_from_db(session_id: str, limit: int = 50) -> list:
    """
    Загружает историю чата из базы данных
    Args:
        session_id: Идентификатор сессии
        limit: Максимальное количество сообщений для загрузки
    Returns:
        list: Список сообщений в формате для GigaChat
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT role, content, function_call, function_name
            FROM chat_history
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (session_id, limit)
        )
        rows = cursor.fetchall()
        
        # Преобразуем в список сообщений (в обратном порядке — от старых к новым)
        messages = []
        for row in reversed(rows):
            role, content, function_call, function_name = row
            
            message = {"role": role}
            if content:
                message["content"] = content
            if function_call:
                message["function_call"] = function_call
            if function_name:
                message["name"] = function_name
            
            messages.append(message)
        
        print(f"📖 Загружено {len(messages)} сообщений из БД для сессии {session_id[:8]}...")
        return messages
        
    except Exception as e:
        print(f"❌ Ошибка загрузки из БД: {e}")
        return []
    finally:
        conn.close()

def clear_history(session_id: str):
    """Очищает историю чата для указанной сессии"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM chat_history WHERE session_id = %s",
            (session_id,)
        )
        conn.commit()
        print(f"🗑️ История очищена для сессии {session_id[:8]}...")
    except Exception as e:
        print(f"❌ Ошибка очистки истории: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    
# Описание функций
giga_functions = [
    {
        "name": "make_plot",
        "description": f"Построить график по показателю здоровья (вес, сахар, давление и т.д.)",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "Название показателя для построения графика",
                    "enum": ["Вес", "Давление", "Гемоглобин", "Холестерин", "Сахар"]
                },
            },
            "required": ["metric"]
        }
    },
    {
        "name": "get_current_date",
        "description": f"Получить текущую дату",
        "parameters": {
            "type": 'oject',
            "properties": {},
            "required": []
        }
    },
    
    {
        "name": "get_analiz_results",
        "description": "Получить результаты лабораторных анализов в виде таблицы. Можно запросить один или несколько показателей одновременно.",
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
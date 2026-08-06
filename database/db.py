from psycopg2 import connect
from psycopg2.extras import Json
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv


load_dotenv()
path_catalog=os.getenv("PATH_CATALOG")
password=os.getenv("DB_PASSWORD")
user=os.getenv("DB_USER")


def get_db_engine():
    """Создаём движок для работы с БД"""
    db_url = f"postgresql://{user}:{password}@localhost:5432/db_health"
    return create_engine(db_url)


# Функции для сохранения чата
def get_db_connection():
    return connect(dbname="db_health", host="localhost", user=user, password=password, port="5432")


def save_message_to_db(chat_id: str, role: str, content: str = None, 
                       function_call: dict = None, function_name: str = None):
    """Сохраняет сообщение в базу данных"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Преобразуем function_call в JSON, если он есть
        function_call_json = Json(function_call) if function_call else None
        
        cursor.execute(
            """
            INSERT INTO chat_history (chat_id, role, content, function_call, function_name)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (chat_id, role, content, function_call_json, function_name)
        )
        conn.commit()
        print(f"💾 Сохранено сообщение в БД: role={role}, chat_id={chat_id}")
    except Exception as e:
        print(f"❌ Ошибка сохранения в БД: {e}")
        conn.rollback()
    finally:
        conn.close()

def load_history_from_db(chat_id: str, limit: int = 50) -> list:
    """
    Загружает историю чата из базы данных
    Args:
        chat_id: Идентификатор чата
        limit: Максимальное количество сообщений для загрузки
    Return:
        list: Список сообщений в формате для GigaChat
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT role, content, function_call, function_name
            FROM chat_history
            WHERE chat_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (chat_id, limit)
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
        
        print(f"📖 Загружено {len(messages)} сообщений из БД для чата {chat_id}...")
        return messages
        
    except Exception as e:
        print(f"❌ Ошибка загрузки из БД: {e}")
        return []
    finally:
        conn.close()

def clear_history(chat_id: str):
    """Очищает историю чата для указанной сессии"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM chat_history WHERE chat_id = %s",
            (chat_id,)
        )
        conn.commit()
        print(f"🗑️ История очищена для чата № {chat_id}")
    except Exception as e:
        print(f"❌ Ошибка очистки истории: {e}")
        conn.rollback()
    finally:
        conn.close()
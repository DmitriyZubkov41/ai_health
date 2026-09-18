from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from gigachat import GigaChat
from gigachat.models import Chat, Messages
import os
import json
import uuid
import requests
from dotenv import load_dotenv
from tools import *
from database.db import load_history_from_db, save_message_to_db, clear_history


# --- Загрузка переменных окружения ---
load_dotenv()
AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "ты специалист в медицине")

import certifi
CERT_PATH = certifi.where()

token = requests.post(
    "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {AUTH_KEY}",
    },
    data={"scope": "GIGACHAT_API_PERS"},
    verify=CERT_PATH,
)
access_token = token.json()["access_token"]

client = GigaChat(
                base_url="https://api.giga.chat/v1",
                credentials=AUTH_KEY,
                scope="GIGACHAT_API_PERS",
                #model="GigaChat-2",
                #model="GigaChat-2-Pro",
                model = "GigaChat-2-Max",
                verify_ssl_certs=True,
                access_token=access_token
)

router = APIRouter()

# Pydantic-модель для запроса - шаблон запроса при нажатии на кнопку Отправить
class ChatRequest(BaseModel):
    message: str
    chat_id: str


# --- Главная страница ---
@router.get("/", response_class=HTMLResponse)
def get_index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
        return HTMLResponse(content=html_content)
    

# --- Основной эндпоинт чата ---
@router.post("/chat")
def chat(user_message: ChatRequest):
    print(f"📥 Входящий запрос: message={user_message.message[:50]}..., chat_id={user_message.chat_id}")
    chat_id = user_message.chat_id
        
    # Загружаем историю из БД
    history_messages = load_history_from_db(chat_id)
    
    if not history_messages:
        history_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Добавляем сообщение пользователя
    history_messages.append({"role": "user", "content": user_message.message})
    save_message_to_db(chat_id, "user", user_message.message)
    
    # Создаём запрос к GigaChat
    query = Chat(
        messages=[Messages(**msg) for msg in history_messages],
        functions=giga_functions,
        function_call="auto"
    )
    
    response = client.chat(query)
    print("\nRESPONSE:")
    print(response)
    message = response.choices[0].message
    print("\nMESSAGE:")
    print(message)
    
    
    # Проверяем, нужно ли вызвать функцию
    if response.choices[0].finish_reason == "function_call":
        function_call_dict = message.function_call.model_dump()
        
        #  Записываем ответ в бд
        save_message_to_db(
            chat_id,
            "assistant",
            function_call=function_call_dict,
            function_name = message.function_call.name
        )
        
        history_messages.append({
            "role": "assistant",
            "function_call": function_call_dict
        })
        
        function_name = message.function_call.name
        function_args = message.function_call.arguments
        print(f"\n🔧 Вызов функции: {function_name}")
        print(f"📝 Аргументы: {function_args}")
        
        # Выполняем функцию
        func = function_dict.get(function_name)
        if func:
            result_funk = func(**function_args)
        else:
            result_funk = json.dumps({"status": "error", "message": f"Неизвестная функция: {function_name}"})
        print(f"✅ Результат функции (JSON): {result_funk[:100]}...")
        
        # Добавляем результат функции в историю
        history_messages.append({"role": "function", "content": result_funk, "name": function_name})
        save_message_to_db(chat_id, "function", result_funk, function_name=function_name)
        
        # Снова отправляем запрос с результатом функции
        final_query = Chat(
            messages=[Messages(**msg) for msg in history_messages],
            functions=giga_functions,
            function_call="auto"
        )
        final_response = client.chat(final_query)
        final_message = final_response.choices[0].message.content
        save_message_to_db(chat_id, "assistant", final_message)
        
           
        return {"response": final_message}
    
    # Если функция не вызывалась
    save_message_to_db(chat_id, "assistant", message.content)
    return {"response": message.content}


# --- Очистка истории ---
@router.post("/clear_history")
def clear_chat_history(user_message: ChatRequest):
    """Очищает историю чата для указанного chat_id"""
    chat_id = user_message.chat_id
    clear_history(chat_id)
    return {"status": "success", "message": f"История чата {chat_id[:8]}... очищена"}
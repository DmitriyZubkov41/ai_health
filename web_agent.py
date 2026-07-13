from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from gigachat import GigaChat
from gigachat.models import Chat, Messages
import os
from dotenv import load_dotenv
import uvicorn
import requests
import uuid
import json
from tools import *


METRIC_SYNONYMS = {
    "Давление": "Верхнее_давление",
    "Верхнее давление": "Верхнее_давление",
    "Нижнее давление": "Нижнее_давление",
    "Вес": "Вес",
    "Пульс": "Пульс",
    "Сахар": "Сахар",
    "Температура": "Температура",
    "Витамин D": "Витамин_D",
    "Витамин B-12": "Витамин_B-12",
    "Белок C-реактивный": "Белок_C-реактивный",
    "Белок C": "Белок_C-реактивный",
    "Ревматоидный фактор": "Ревматоидный_фактор",
    "Группа крови": "Группа_крови",
    "Резус принадлежности": "Резус_принадлежности",
    "Аланинаминотрансфераза (АлАТ)": "Аланинаминотрансфераза_(АлАТ)"
}


#Путь к сертификату
import certifi
CERT_PATH = certifi.where()

load_dotenv()
AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")
token_response = requests.post(
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
access_token = token_response.json()["access_token"]

app = FastAPI()

# Функция для получения или создания session_id
def get_session_id(request: Request) -> str:
    """Получает session_id из cookies или создаёт новый"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

# Создаем клиента GigaChat
client = GigaChat(
                credentials=AUTH_KEY,
                scope="GIGACHAT_API_PERS",
                model="GigaChat-2",
                verify_ssl_certs=True,
                access_token=access_token
)

class ChatRequest(BaseModel):
    message: str

#Декоратор для открытия index.html
@app.get("/", response_class=HTMLResponse)
def get_index():
    """Веб-страница AI-доктора"""
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Файл templates/index.html не найден</h1>", status_code=404)

@app.post("/chat")
def chat(user_message: ChatRequest, request: Request):
    """Обработка сообщений с сохранением истории в БД"""
    
    # Получаем или создаём session_id
    session_id = get_session_id(request)
    print(f"🆔 Сессия: {session_id[:8]}...")
    
    # Загружаем историю из БД
    history_messages = load_history_from_db(session_id)
    
    # Если истории нет, добавляем системный промпт
    if not history_messages:
        history_messages = [
            {"role": "system", "content": "ты специалист в медицине, твоя задача давать мне советы по моему здоровью. Если попрошу построить график по показателю, ты построишь график используя функцию make_plot()"}
        ]
    
    # Добавляем сообщение пользователя
    history_messages.append({"role": "user", "content": user_message.message})
    
    # Сохраняем сообщение пользователя в БД
    save_message_to_db(session_id, "user", user_message.message)
    
    # Создаём объект Chat для запроса
    chat_request = Chat(
        messages=[Messages(**msg) for msg in history_messages],
        functions=giga_functions,
        function_call="auto"
    )
    
    # Отправляем запрос
    response = client.chat(chat_request)
    message = response.choices[0].message
    
    # Проверяем, нужно ли вызвать функцию
    if response.choices[0].finish_reason == "function_call":
        # Сохраняем ответ модели с вызовом функции
        save_message_to_db(
            session_id, 
            "assistant", 
            function_call=message.function_call.model_dump() if hasattr(message.function_call, 'model_dump') else message.function_call
        )
    
        # Добавляем ответ модели с вызовом функции в историю
        history_messages.append({
            "role": "assistant",
            "function_call": message.function_call.model_dump() if hasattr(message.function_call, 'model_dump') else message.function_call
        })

        # Имя и аргументы функции
        function_name = message.function_call.name
        function_args = message.function_call.arguments
        print("\nfunction_args:", function_args)
        
        # Выполняем функцию по её имени
        if function_name == "make_plot":
            metric = function_args.get('metric')
            if metric in METRIC_SYNONYMS:
                function_args['metric'] = METRIC_SYNONYMS[metric]
            result_funk = make_plot(**function_args)
        elif function_name == "get_current_date":
            result_funk = get_current_date(**function_args)
        elif function_name == "get_analiz_results":
            parameter = function_args.get('parameters')
            if isinstance(parameter, list):
                for i, p in enumerate(parameter):
                    if p in METRIC_SYNONYMS:
                        parameter[i] = METRIC_SYNONYMS[p]
                function_args['parameters'] = parameter
            result_funk = get_analiz_results(**function_args)
        else:
            result_funk = json.dumps({"status": "error", "message": f"Неизвестная функция: {function_name}"})

        print(f"✅ Результат функции (JSON): {result_funk}")

        # Добавляем результат функции в историю
        history_messages.append({"role": "function", "content": result_funk, "name": function_name})
    
        # Сохраняем результат функции в БД
        save_message_to_db(session_id, "function", result_funk, function_name=function_name)

        # Получаем финальный ответ с учетом результата функции
        final_request = Chat(
            messages=[Messages(**msg) for msg in history_messages],
            functions=giga_functions,
            function_call="auto"
        )
        final_response = client.chat(final_request)
        final_message = final_response.choices[0].message.content

        # Сохраняем финальный ответ в БД
        save_message_to_db(session_id, "assistant", final_message)
        
        # Парсим результат result_funk
        try:
            result_data = json.loads(result_funk)
            image_data = result_data.get("image")
            plot_path = result_data.get("plot_path")
            table_data = result_data.get("data") if result_data.get("status") == "success" else None
            columns = result_data.get("columns", [])
            norms = result_data.get("norms", {})
        except:
            image_data = None
            plot_path = None
            table_data = None
            columns = []
            norms = {}

        # Формируем списки для ответа
        plots = []
        tables = []

        if plot_path:
            plots = [f"/{plot_path}"]

        if table_data:
            tables = [{
                "data": table_data,
                "columns": columns,
                "norms": norms
            }]

        # Возвращаем ответ с графиком и/или таблицей
        if image_data:
            return {
                "response": final_message,
                "image": image_data,
                "plots": plots,      # ← если есть путь к файлу
                "tables": tables     # ← если есть таблица
            }
        else:
            return {
                "response": final_message,
                "plots": plots,
                "tables": tables
            }
    
    # Если функция не вызывалась, возвращаем обычный ответ
    else:
        # Обычный ответ (без вызова функции)
        save_message_to_db(session_id, "assistant", message.content)
        
        return {
            "response": message.content,
            "plots": [],
            "tables": []
        }

# Добавьте эндпоинт для очистки истории
@app.post("/clear_history")
def clear_chat_history(request: Request):
    """Очищает историю чата для текущей сессии"""
    session_id = get_session_id(request)
    clear_history(session_id)
    return {"status": "success", "message": "История очищена"}

# В ответе на запрос отправляем session_id в cookie
@app.get("/", response_class=HTMLResponse)
def get_index(request: Request):
    """Веб-страница AI-доктора"""
    session_id = get_session_id(request)
    
    # Создаём ответ с HTML и устанавливаем cookie
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        
        response = HTMLResponse(content=html_content)
        response.set_cookie(key="session_id", value=session_id, max_age=31536000)  # 1 год
        return response
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Файл templates/index.html не найден</h1>", status_code=404)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
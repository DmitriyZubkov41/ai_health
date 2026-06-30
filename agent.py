import os
import requests
import uuid

# из файла .env получаем gigachat key
from dotenv import load_dotenv
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
    #verify="/path/to/russian_trusted_root_ca.pem",
    verify=False
)

access_token = token_response.json()["access_token"]

# 2. Отправляем запрос к модели
chat_response = requests.post(
    "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
    },
    json={
        "model": "GigaChat",
        "messages": [{"role": "user", "content": "Привет! Расскажи о себе в двух предложениях."}],
        "temperature": 0.7,
    },
    verify="/path/to/russian_trusted_root_ca.pem",
)
print(chat_response.json()["choices"][0]["message"]["content"])
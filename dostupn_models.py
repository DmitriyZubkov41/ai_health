import requests
from dotenv import load_dotenv
import os
import uuid
import certifi

load_dotenv()
AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")
CERT_PATH = certifi.where()

# 1. ПОЛУЧАЕМ ACCESS_TOKEN
token_response = requests.post(
    "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {AUTH_KEY}",  # Здесь используем AUTH_KEY
    },
    data={"scope": "GIGACHAT_API_PERS"},
    verify=CERT_PATH,
)

if token_response.status_code == 200:
    access_token = token_response.json()["access_token"]
    print(f"✅ Токен получен: {access_token[:50]}...")
else:
    print(f"❌ Ошибка получения токена: {token_response.status_code}")
    print(token_response.text)
    exit()


url = "https://gigachat.devices.sberbank.ru/api/v1/models"

payload={}
headers = {
  'Accept': 'application/json',
  'Authorization': f'Bearer {access_token}'
}

response = requests.request("GET", url, headers=headers, data=payload, verify=CERT_PATH)

print(response.text)
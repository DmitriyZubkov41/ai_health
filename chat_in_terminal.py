from gigachat import GigaChat
import os
from dotenv import load_dotenv

load_dotenv()
AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY")

with GigaChat(credentials=AUTH_KEY) as client:
    print("Чат с GigaChat. Введите 'выход' или 'exit' для завершения.\n")
    
    while True:
        # Ввод пользователя
        user_input = input("Вы: ")
        
        # Проверка на выход
        if user_input.lower() in ['выход', 'exit', 'quit']:
            print("До свидания!")
            break
        
        # Отправка запроса
        response = client.chat(user_input)
        print(f"GigaChat: {response.choices[0].message.content}\n")
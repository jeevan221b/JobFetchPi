# telegram_bot.py
# Sends messages using Telegram Bot API

import requests

TOKEN = '7798463460:AAFWLWu5gVCo6bU80l_na5L4l_POWnrpLCQ'
CHAT_ID = '1255819939'

def send_message(text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': text}
    response = requests.post(url, data=data)
    if not response.ok:
        print("Failed to send message:", response.text)

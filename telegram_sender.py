# telegram_sender.py
import requests
import time
from telegram import Bot
import asyncio

BOT_TOKEN = "7798463460:AAFWLWu5gVCo6bU80l_na5L4l_POWnrpLCQ"
USER_ID = 1255819939  # your Telegram user ID

bot = Bot(token=BOT_TOKEN)

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": USER_ID,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"❌ Failed to send: {response.text}")
        else:
            print("📨 Message sent!")
    except Exception as e:
        print(f"❌ Error sending message: {e}")

async def send_jobs(jobs, query_label="Job Alert"):
    if not jobs:
        message = f"No jobs found for \"{query_label}\""
        # print(f"> Job Scraper:\n{message}")
        await bot.send_message(chat_id=USER_ID, text=message)
        return

    header = f"{query_label}\n"
    message = header + "\n" + "\n\n".join(jobs)

    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
    for chunk in chunks:
        await bot.send_message(chat_id=USER_ID, text=chunk)
        await asyncio.sleep(1)  # prevent Telegram flood

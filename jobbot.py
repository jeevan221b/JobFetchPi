import json
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Replace with your actual bot token and user ID
TOKEN = "7798463460:AAFWLWu5gVCo6bU80l_na5L4l_POWnrpLCQ"
ALLOWED_USER_ID = 1255819939

# State management
state = {}
alerts_file = "job_alerts.json"
WAITING_TITLE = "waiting_title"
WAITING_LOCATION = "waiting_location"

# Enable logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def load_alerts():
    try:
        with open(alerts_file, 'r') as f:
            return json.load(f)
    except:
        return []


def save_alerts(alerts):
    with open(alerts_file, 'w') as f:
        json.dump(alerts, f, indent=2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("🚫 You don't have access to this bot.")
        return

    logger.info("User started bot.")
    await update.message.reply_text("👋 Welcome! Send 'New Job' to add a job alert. Use /list to view saved jobs.")


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message.text.strip()

    if user_id != ALLOWED_USER_ID:
        logger.warning(f"Unauthorized user tried to access: {user_id}")
        await update.message.reply_text("🚫 You don't have access to this bot.")
        return

    logger.info(f"Received message: {msg}")

    if msg.lower() in ["hi", "hello", "hey"]:
        await update.message.reply_text("👋 Hello! You can send 'New Job' to start adding an alert.")
        return

    if msg.lower() == "new job":
        state[user_id] = {"step": WAITING_TITLE}
        await update.message.reply_text("✏️ Enter the Job Title:")
        return

    if state.get(user_id, {}).get("step") == WAITING_TITLE:
        state[user_id]["title"] = msg
        state[user_id]["step"] = WAITING_LOCATION
        await update.message.reply_text("🗺️ Enter the Location:")
        return

    if state.get(user_id, {}).get("step") == WAITING_LOCATION:
        title = state[user_id]["title"]
        location = msg

        alerts = load_alerts()
        alerts.append({"title": title, "location": location})
        save_alerts(alerts)

        await update.message.reply_text(f"✅ Job alert added:\n🔹 {title}\n📍 {location}")
        logger.info(f"Added job alert: {title} @ {location}")
        state.pop(user_id)
        return

    await update.message.reply_text("💡 Send 'New Job' to begin.")


async def list_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("🚫 You don't have access to this bot.")
        return

    alerts = load_alerts()
    if not alerts:
        await update.message.reply_text("🗂️ No job alerts saved.")
        return

    msg = "📋 Your Job Alerts:\n"
    for i, alert in enumerate(alerts, 1):
        msg += f"{i}. {alert['title']} @ {alert['location']}\n"
    await update.message.reply_text(msg)


def main():
    logger.info("🔁 Starting jobbot.py...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_alerts))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    logger.info("✅ Bot is now polling for messages.")
    app.run_polling()


if __name__ == "__main__":
    main()

import json
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta


# Bot config
TOKEN = "7798463460:AAFWLWu5gVCo6bU80l_na5L4l_POWnrpLCQ"
ALLOWED_USER_ID = 1255819939

# File to store alerts
alerts_file = "job_alerts.json"

# States
WAITING_TITLE = "waiting_title"
WAITING_LOCATION = "waiting_location"
WAITING_DELETE_NUMBER = "waiting_delete_number"
WAITING_CONFIRM_REMOVE_ALL = "waiting_remove_all"

state = {}

# Setup logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# JSON handlers
def load_alerts():
    try:
        with open(alerts_file, 'r') as f:
            return json.load(f)
    except:
        return []

def save_alerts(alerts):
    with open(alerts_file, 'w') as f:
        json.dump(alerts, f, indent=2)


# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return await update.message.reply_text("🚫 You don't have access.")
    await update.message.reply_text("👋 Welcome!\nSend 'New Job' to add a job alert.\nUse /list to view alerts.\n/delete to remove one.\n/remove_all to clear all.\n/cancel to cancel.")


# Command: /list
async def list_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return await update.message.reply_text("🚫 You don't have access.")
    alerts = load_alerts()
    if not alerts:
        return await update.message.reply_text("📭 No job alerts saved.")
    msg = "📋 Your Job Alerts:\n"
    for i, alert in enumerate(alerts, 1):
        msg += f"{i}. {alert['title']} @ {alert['location']}\n"
    await update.message.reply_text(msg)


# Command: /delete
async def delete_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return await update.message.reply_text("🚫 You don't have access.")
    alerts = load_alerts()
    if not alerts:
        return await update.message.reply_text("📭 No alerts to delete.")
    msg = "🗑️ Which alert to delete?\n"
    for i, alert in enumerate(alerts, 1):
        msg += f"{i}. {alert['title']} @ {alert['location']}\n"
    state[ALLOWED_USER_ID] = {"step": WAITING_DELETE_NUMBER}
    await update.message.reply_text(msg + "\n✏️ Send the number of the alert to delete.")


# Command: /remove_all
async def remove_all_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return await update.message.reply_text("🚫 You don't have access.")
    state[ALLOWED_USER_ID] = {"step": WAITING_CONFIRM_REMOVE_ALL}
    await update.message.reply_text("⚠️ Are you sure you want to delete all job alerts?\nType 'yes' to confirm or /cancel.")


# Command: /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return await update.message.reply_text("🚫 You don't have access.")
    if ALLOWED_USER_ID in state:
        state.pop(ALLOWED_USER_ID)
        await update.message.reply_text("❌ Operation cancelled.")
    else:
        await update.message.reply_text("ℹ️ No ongoing operation to cancel.")


# Main message handler
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message.text.strip()

    if user_id != ALLOWED_USER_ID:
        return await update.message.reply_text("🚫 Unauthorized.")

    user_state = state.get(user_id)

    if msg.lower() == "new job":
        state[user_id] = {"step": WAITING_TITLE}
        return await update.message.reply_text("✏️ Enter the Job Title:")
    
    if msg.lower() in ["next scrape", "when next", "next"]:
        await next_scrape(update, context)
        return

    if user_state:
        step = user_state.get("step")

        if step == WAITING_TITLE:
            state[user_id]["title"] = msg
            state[user_id]["step"] = WAITING_LOCATION
            return await update.message.reply_text("🗺️ Enter the Location:")

        elif step == WAITING_LOCATION:
            title = user_state["title"]
            location = msg
            alerts = load_alerts()
            alerts.append({"title": title, "location": location})
            save_alerts(alerts)
            state.pop(user_id)
            return await update.message.reply_text(f"✅ Job alert added:\n🔹 {title}\n📍 {location}")

        elif step == WAITING_DELETE_NUMBER:
            try:
                idx = int(msg) - 1
                alerts = load_alerts()
                if 0 <= idx < len(alerts):
                    removed = alerts.pop(idx)
                    save_alerts(alerts)
                    state.pop(user_id)
                    return await update.message.reply_text(f"🗑️ Deleted: {removed['title']} @ {removed['location']}")
                else:
                    return await update.message.reply_text("❌ Invalid number. Use /delete again.")
            except ValueError:
                return await update.message.reply_text("❌ Please enter a valid number.")

        elif step == WAITING_CONFIRM_REMOVE_ALL:
            if msg.lower() == "yes":
                save_alerts([])
                state.pop(user_id)
                return await update.message.reply_text("🧹 All job alerts removed.")
            else:
                state.pop(user_id)
                return await update.message.reply_text("❌ Cancelled removing all alerts.")

    await update.message.reply_text("💡 Send 'New Job' to begin or /list to view saved alerts.")

async def next_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("🚫 You don't have access to this bot.")
        return

    try:
        with open("next_scrape.txt", "r") as f:
            time_str = f.read().strip()
            next_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            formatted = next_time.strftime("%I:%M %p on %A, %d %B")
            await update.message.reply_text(f"🕒 Next scrape will run at: {formatted}")
    except FileNotFoundError:
        await update.message.reply_text("⏱️ Next scrape time is not set.")


# Init bot
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_alerts))
    app.add_handler(CommandHandler("delete", delete_alert))
    app.add_handler(CommandHandler("remove_all", remove_all_alerts))
    app.add_handler(CommandHandler("next", next_scrape))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    logger.info("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()

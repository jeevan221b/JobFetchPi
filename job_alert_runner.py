import json
import asyncio
from linkedin_scraper import get_jobs_for
from telegram_sender import send_jobs
from datetime import datetime, timedelta


def update_next_scrape_time():
    next_time = datetime.now() + timedelta(hours=1)
    with open("next_scrape.txt", "w") as f:
        f.write(next_time.strftime("%Y-%m-%d %H:%M:%S"))

def load_alerts(path="job_alerts.json"):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ No saved alerts found.")
        return []


async def run_all_alerts_async():
    alerts = load_alerts()
    if not alerts:
        print("🚫 No alerts to run.")
        return

    print(f"🔁 Running {len(alerts)} job alerts...")

    all_messages = []

    for alert in alerts:
        title = alert.get("title")
        location = alert.get("location")

        if not title or not location:
            print("⚠️ Skipping invalid alert:", alert)
            continue

        print(f"\n🔎 Fetching jobs for: {title} – {location}")
        label, jobs = await get_jobs_for(title, location)

        if jobs:
            message = f"{len(jobs)} jobs found for \"{label}\"\n\n" + "\n\n".join(jobs)
            all_messages.append(message)

    # Send all collected messages in one go
    for message in all_messages:
        await send_jobs([message])  # send_jobs expects a list of job messages


def run_all_alerts():
    asyncio.run(run_all_alerts_async())


if __name__ == "__main__":
    run_all_alerts()
    update_next_scrape_time()

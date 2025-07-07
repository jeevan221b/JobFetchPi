import json
from linkedin_scraper import get_jobs_for

def load_alerts(path="job_alerts.json"):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ No saved alerts found.")
        return []

def run_all_alerts():
    alerts = load_alerts()
    if not alerts:
        print("🚫 No alerts to run.")
        return

    print(f"🔁 Running {len(alerts)} job alerts...")

    for alert in alerts:
        title = alert.get("title")
        location = alert.get("location")

        if not title or not location:
            print("⚠️ Skipping invalid alert:", alert)
            continue

        print(f"\n🔎 Fetching jobs for: {title} – {location}")
        # send_to_telegram=True will trigger send_jobs() from within get_jobs_for
        get_jobs_for(title, location, send_to_telegram=True)

if __name__ == "__main__":
    run_all_alerts()

from playwright.sync_api import sync_playwright
import json
import re
import time
from telegram_sender import send_jobs
import asyncio

def load_cookies(path="cookies.json"):
    with open(path, "r") as f:
        return json.load(f)

def get_jobs_for(title, location, send_to_telegram=False):
    url = f"https://www.linkedin.com/jobs/search/?keywords={title.replace(' ', '%20')}&location={location.replace(' ', '%20')}&f_TPR=r86400"
    jobs = []

    print(f"\n🌐 Opening LinkedIn job search: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context()
        context.add_cookies(load_cookies())

        page = context.new_page()
        page.goto(url, timeout=60000)
        time.sleep(10)  # Let the page load

        try:
            # cards = page.query_selector_all("li.scaffold-layout__list-item")
            cards = page.query_selector_all("li.scaffold-layout__list-item")[:5]

            print(f"🔍 Found {len(cards)} job cards")

            for i, card in enumerate(cards):
                try:
                    card.scroll_into_view_if_needed()
                    card.click()
                    time.sleep(3)  # Wait for right pane to load

                    # LEFT PANE scraping (title, company, link)
                    title_el = card.query_selector("a.job-card-list__title--link")
                    company_el = card.query_selector("div.artdeco-entity-lockup__subtitle span")
                    href = title_el.get_attribute("href") if title_el else None
                    job_link = "https://www.linkedin.com" + href if href and href.startswith("/") else href or page.url

                    title_text = title_el.inner_text().strip() if title_el else "Unknown Title"
                    company_text = company_el.inner_text().strip() if company_el else "Unknown Company"

                    # RIGHT PANE scraping (time + apply count)
                    tertiary_info = page.query_selector("div.job-details-jobs-unified-top-card__tertiary-description-container")
                    if not tertiary_info:
                        print(f"⚠️ Skipping job {i} - no right-pane info found")
                        continue

                    info_lines = tertiary_info.inner_text().split("\n")
                    time_text = next((line for line in info_lines if "ago" in line.lower() or "just now" in line.lower()), "Time not found").strip()

                    job_data = (
                        f"💼 {title_text} at {company_text}\n\n"
                        f"🔗 {job_link}\n\n"
                        f"🕒 {time_text}\n\n"
                    )

                    jobs.append(job_data)
                    print(f"✅ Added job {i+1}: {title_text} at {company_text}")

                except Exception as e:
                    print(f"❌ Error parsing job {i+1}: {e}")
                    continue

        except Exception as e:
            print("❌ Scrape failed:", e)

        browser.close()

    print(f"\n✅ Total jobs collected: {len(jobs)}")

    if send_to_telegram:
        label = f'{len(jobs)} jobs found for "{title} {location}"'
        asyncio.run(send_jobs(jobs, query_label=label))

    return jobs

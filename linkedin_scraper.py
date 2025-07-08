import json
import re
import asyncio
from playwright.async_api import async_playwright

def is_recent_posted(time_text):
    time_text = time_text.lower()
    if "just now" in time_text or "few seconds" in time_text:
        return True
    if "minute" in time_text:
        return True
    if "hour" in time_text:
        try:
            hours = int(re.findall(r'\d+', time_text)[0])
            return hours <= 2
        except:
            return False
    if re.search(r"\b\d+\s*m\b", time_text):  # e.g., 45m
        return True
    if re.search(r"\b\d+\s*h\b", time_text):  # e.g., 1h
        return int(re.findall(r"\d+", time_text)[0]) <= 2
    if "recently" in time_text:
        return True
    return False

def load_cookies(path="cookies.json"):
    with open(path, "r") as f:
        return json.load(f)

async def get_jobs_for(title, location):
    url = f"https://www.linkedin.com/jobs/search/?keywords={title.replace(' ', '%20')}&location={location.replace(' ', '%20')}&f_TPR=r86400"
    jobs = []

    print(f"\n🌐 Opening LinkedIn job search: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_cookies(load_cookies())

        page = await context.new_page()
        await page.goto(url, timeout=180000)
        await asyncio.sleep(10)

        try:
            cards = await page.query_selector_all("li.scaffold-layout__list-item")
            print(f"🔍 Found {len(cards)} job cards")

            for i, card in enumerate(cards):  # Limit to first 5 for testing
                try:
                    await card.scroll_into_view_if_needed()
                    await card.click()
                    await asyncio.sleep(3)

                    # LEFT PANE scraping
                    title_el = await card.query_selector("a.job-card-list__title--link")
                    company_el = await card.query_selector("div.artdeco-entity-lockup__subtitle span")
                    href = await title_el.get_attribute("href") if title_el else None
                    job_link = "https://www.linkedin.com" + href if href and href.startswith("/") else href

                    title_text = await title_el.inner_text() if title_el else "Unknown Title"
                    company_text = await company_el.inner_text() if company_el else "Unknown Company"

                    # RIGHT PANE scraping
                    tertiary_info = await page.query_selector("div.job-details-jobs-unified-top-card__tertiary-description-container")
                    if not tertiary_info:
                        print(f"⚠️ Skipping job {i} - no right-pane info found")
                        continue

                    info_lines = (await tertiary_info.inner_text()).split("\n")
                    time_text = next((line for line in info_lines if "ago" in line.lower() or "just now" in line.lower()), "Time not found").strip()

                    if not is_recent_posted(time_text):
                        print(f"⏩ Skipped (old): {title_text} – {time_text}")
                        continue

                    job_data = (
                        f"💼 {title_text} at {company_text}\n"
                        f"🔗 {job_link}\n"
                        f"🕒 {time_text}"
                    )
                    jobs.append(job_data)
                    print(f"✅ Added job {i+1}: {title_text} at {company_text}")

                except Exception as e:
                    print(f"❌ Error parsing job {i+1}: {e}")
                    continue

        except Exception as e:
            print("❌ Scrape failed:", e)

        await browser.close()

    label = f"{title} {location}"
    print(f"\n✅ Total jobs collected: {len(jobs)}")
    return label, jobs

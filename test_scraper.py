from linkedin_scraper import get_jobs_for

jobs = get_jobs_for("React Developer", "Bangalore")

print(f"Found {len(jobs)} jobs.")
for job in jobs:
    print(job)
    print("---")

import re
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

SEARCH_TERMS = [
    "SOC Analyst",
    "Cybersecurity Analyst",
    "Security Analyst",
    "Information Security",
    "IT Support",
    "Network Engineer",
    "Cloud Engineer",
    "DevSecOps",
    "Penetration Tester",
    "Technical Support",
    "Software Developer",
    "Data Analyst",
]

LOCATIONS = [
    "Kenya",
    "Uganda",
    "Rwanda",
    "Ghana",
    "Nigeria",
    "South Africa",
    "Egypt",
    "Remote Africa",
]


def make_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def search_web(term: str, location: str) -> list[dict]:
    query = quote(f"{term} jobs {location}")
    url = f"https://www.google.com/search?q={query}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 Chrome/147 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    jobs = []

    for result in soup.select("div.MjjYud"):
        link = result.select_one("a[href]")
        title = result.select_one("h3")

        if not link or not title:
            continue

        href = link.get("href", "")
        text = result.get_text(" ", strip=True)

        if not href.startswith("http"):
            continue

        jobs.append({
            "id": make_id(href),
            "title": title.get_text(" ", strip=True),
            "url": href,
            "location": location,
            "search_term": term,
            "snippet": re.sub(r"\s+", " ", text),
            "source": "web_search",
        })

    return jobs


def discover_jobs():
    discovered = {}

    for location in LOCATIONS:
        for term in SEARCH_TERMS:
            try:
                results = search_web(term, location)

                for job in results:
                    discovered[job["id"]] = job

            except Exception as exc:
                print(f"[search error] {term} / {location}: {exc}")

    return list(discovered.values())


if __name__ == "__main__":
    jobs = discover_jobs()

    print(f"\nDiscovered {len(jobs)} unique jobs\n")

    for job in jobs[:30]:
        print(f"{job['title']}")
        print(f"{job['location']} | {job['url']}")
        print()

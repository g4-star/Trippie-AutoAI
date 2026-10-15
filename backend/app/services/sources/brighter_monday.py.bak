import json
import re
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.brightermonday.co.ke"
JOBS_URL = f"{BASE_URL}/jobs"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    )
}


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        return None

    value = value.strip()

    if not value:
        return None

    # Handle ISO-8601 values such as:
    # 2026-09-22T00:00:00.000000Z
    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).replace(tzinfo=None)
    except ValueError:
        pass

    # Fallback for date-only values.
    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        )
    except ValueError:
        return None


def clean_text(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, (list, tuple)):
        parts = [
            clean_text(item)
            for item in value
        ]
        text = " ".join(
            part
            for part in parts
            if part
        )
        return text.strip() or None

    if isinstance(value, dict):
        parts = [
            clean_text(item)
            for item in value.values()
        ]
        text = " ".join(
            part
            for part in parts
            if part
        )
        return text.strip() or None

    if not isinstance(value, str):
        value = str(value)

    value = value.strip()

    if not value:
        return None

    # Avoid passing plain URLs to BeautifulSoup. BeautifulSoup warns
    # when a string looks like a URL rather than HTML/XML.
    lowered = value.lower()

    if lowered.startswith(("http://", "https://", "www.")):
        return value

    soup = BeautifulSoup(
        value,
        "html.parser",
    )

    text = " ".join(
        soup.stripped_strings
    )

    return text.strip() or None


def absolute_url(url: str | None) -> str | None:
    if not url:
        return None

    if url.startswith("http://") or url.startswith("https://"):
        return url

    return f"{BASE_URL}/{url.lstrip('/')}"


def extract_jobposting(soup: BeautifulSoup) -> dict[str, Any] | None:
    """
    Extract the Schema.org JobPosting object from a BrighterMonday page.
    """

    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue

        items = []

        if isinstance(data, dict) and "@graph" in data:
            items = data["@graph"]
        elif isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = [data]

        for item in items:
            if not isinstance(item, dict):
                continue

            job_type = item.get("@type")

            if job_type == "JobPosting":
                return item

    return None


def extract_company(soup: BeautifulSoup, job: dict[str, Any]) -> str | None:
    """
    Try structured data first, then fall back to the visible company heading.
    """

    organization = job.get("hiringOrganization")

    if isinstance(organization, dict):
        name = organization.get("name")
        if name:
            return str(name).strip()

    # BrighterMonday's visible company heading normally appears
    # immediately after the job title.
    headings = soup.find_all(["h1", "h2", "h3"])

    for heading in headings:
        text = " ".join(heading.stripped_strings).strip()

        if text and "TRINOVA" in text.upper():
            return text

    # Generic fallback: inspect text around the main job title.
    title = clean_text(job.get("title"))

    if title:
        for heading in headings:
            text = " ".join(heading.stripped_strings).strip()

            if text and text != title:
                return text

    return None


def extract_location(job: dict[str, Any]) -> str | None:
    location = job.get("jobLocation")

    if isinstance(location, list):
        location = location[0] if location else None

    if not isinstance(location, dict):
        return None

    address = location.get("address")

    if not isinstance(address, dict):
        return None

    locality = address.get("addressLocality")
    region = address.get("addressRegion")
    country = address.get("addressCountry")

    # Prefer the actual city/locality when available.
    if locality:
        parts = [str(locality).strip()]

        if region and str(region).strip().lower() != str(locality).strip().lower():
            parts.append(str(region).strip())

        return ", ".join(parts)

    # If only a region is supplied, use it.
    if region:
        return str(region).strip()

    # Convert country codes into readable names.
    country_map = {
        "KE": "Kenya",
        "UG": "Uganda",
        "TZ": "Tanzania",
        "RW": "Rwanda",
        "US": "United States",
        "GB": "United Kingdom",
    }

    if country:
        country = str(country).strip()
        return country_map.get(country.upper(), country)

    return None


def extract_salary(job: dict[str, Any]) -> str | None:
    salary = job.get("baseSalary")

    if not isinstance(salary, dict):
        return None

    currency = salary.get("currency")

    value = salary.get("value")

    if not isinstance(value, dict):
        return None

    minimum = value.get("minValue")
    maximum = value.get("maxValue")

    if minimum is not None and maximum is not None:
        return f"{currency} {minimum} - {maximum}"

    if minimum is not None:
        return f"{currency} {minimum}"

    if maximum is not None:
        return f"{currency} {maximum}"

    return None


def build_external_id(url: str) -> str:
    """
    Use the BrighterMonday listing slug as the stable external ID.
    """

    match = re.search(r"/listings/([^/?#]+)", url)

    if match:
        return f"brightermonday:{match.group(1)}"

    return f"brightermonday:{url}"


def parse_job_page(url: str) -> dict[str, Any] | None:
    """
    Fetch and normalize one BrighterMonday vacancy.
    """

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    job = extract_jobposting(soup)

    if not job:
        return None

    title = clean_text(job.get("title"))

    if not title:
        return None

    return {
        "external_id": build_external_id(url),
        "title": title,
        "company": extract_company(soup, job),
        "location": extract_location(job),
        "description": clean_text(job.get("description")),
        "requirements": clean_text(
            job.get("qualifications")
        ),
        "experience_requirements": clean_text(
            job.get("experienceRequirements")
        ),
        "education_requirements": clean_text(
            job.get("educationRequirements")
        ),
        "date_posted": parse_datetime(
            job.get("datePosted")
        ),
        "valid_through": parse_datetime(
            job.get("validThrough")
        ),
        "job_url": url,
        "source": "BrighterMonday",
        "employment_type": job.get("employmentType"),
        "salary": extract_salary(job),
    }


def discover_job_urls(
    limit: int = 20,
    query: str | None = None,
    page: int = 1,
) -> list[str]:
    """
    Discover actual BrighterMonday vacancy URLs.

    When ``query`` is provided, use BrighterMonday's public
    search parameter instead of scanning the generic jobs page.
    """

    params = {}

    if query:
        params["q"] = query

    # BrighterMonday currently returns 404 when a filtered
    # search uses both ``q`` and ``page``. Keep pagination
    # available for the generic jobs page only.
    if page > 1 and not query:
        params["page"] = page

    response = requests.get(
        JOBS_URL,
        params=params,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    urls = []
    seen = set()

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")

        if "/listings/" not in href:
            continue

        url = absolute_url(href)

        if not url or url in seen:
            continue

        seen.add(url)
        urls.append(url)

        if len(urls) >= limit:
            break

    return urls


def discover_jobs(limit: int = 20) -> list[dict[str, Any]]:
    """
    Discover and parse BrighterMonday vacancies.
    """

    jobs = []

    for url in discover_job_urls(limit=limit):
        try:
            job = parse_job_page(url)

            if job:
                jobs.append(job)

        except requests.RequestException:
            continue

    return jobs

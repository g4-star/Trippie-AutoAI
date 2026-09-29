from __future__ import annotations

import hashlib
from datetime import datetime
from urllib.parse import parse_qs, quote_plus, unquote, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    )
}

TIMEOUT = 20


def clean_url(url: str) -> str:
    parsed = urlparse(url)

    query = parse_qs(parsed.query)

    query = {
        key: value
        for key, value in query.items()
        if not key.lower().startswith(
            ("utm_", "fbclid", "gclid", "msclkid")
        )
    }

    from urllib.parse import urlencode

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            parsed.params,
            urlencode(query, doseq=True),
            "",
        )
    )


def external_id(url: str) -> str:
    digest = hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()[:32]

    return f"web:{digest}"


def extract_result_url(anchor) -> str | None:
    href = anchor.get("href")

    if not href:
        return None

    if "uddg=" in href:
        parsed = urlparse(href)

        target = parse_qs(
            parsed.query
        ).get("uddg")

        if target:
            return unquote(target[0])

    if href.startswith("//"):
        return "https:" + href

    if href.startswith("/"):
        return (
            "https://html.duckduckgo.com"
            + href
        )

    return href


def search_web(
    query: str,
    limit: int = 10,
) -> list[dict]:

    url = (
        "https://html.duckduckgo.com/html/"
        f"?q={quote_plus(query)}"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    results = []
    seen = set()

    for anchor in soup.select("a.result__a"):

        target = extract_result_url(anchor)

        if not target:
            continue

        target = clean_url(target)

        parsed = urlparse(target)

        if parsed.scheme not in (
            "http",
            "https",
        ):
            continue

        if not parsed.netloc:
            continue

        if target in seen:
            continue

        title = anchor.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue

        seen.add(target)

        results.append(
            {
                "external_id": external_id(
                    target
                ),
                "title": title[:255],
                "job_url": target,
                "source": "web_search",
                "discovered_at": datetime.utcnow(),
            }
        )

        if len(results) >= limit:
            break

    return results


def discover_web_jobs(
    query: str,
    limit: int = 10,
) -> list[dict]:
    """
    Temporary implementation.

    Search discovery is intentionally separated from page extraction.
    We will add validated job-page extraction after confirming the
    search layer is stable.
    """

    results = search_web(
        query=query,
        limit=limit,
    )

    jobs = []

    for result in results:
        jobs.append(
            {
                **result,
                "company": "Unknown",
                "location": None,
                "description": None,
                "requirements": None,
                "employment_type": None,
                "salary": None,
                "date_posted": None,
                "valid_through": None,
            }
        )

    return jobs

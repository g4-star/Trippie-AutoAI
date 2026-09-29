from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from .base import DiscoveryProvider


logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    )
}

TIMEOUT = 20


class PublicPageProvider(DiscoveryProvider):
    """
    Extract candidate job links from publicly accessible pages.

    This provider does not bypass authentication, CAPTCHA, OTP,
    robots restrictions, or other access controls.
    """

    name = "public_pages"

    def __init__(self, pages: list[dict] | None = None):
        self.pages = pages or []

    @staticmethod
    def _clean_url(url: str) -> str:
        parsed = urlparse(url)

        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc.lower(),
                parsed.path.rstrip("/"),
                parsed.params,
                "",
                "",
            )
        )

    @staticmethod
    def _external_id(url: str) -> str:
        digest = hashlib.sha256(
            url.encode("utf-8")
        ).hexdigest()[:32]

        return f"web:{digest}"

    @staticmethod
    def _looks_like_job_link(
        href: str,
        title: str,
    ) -> bool:
        text = f"{href} {title}".lower()

        keywords = (
            "job",
            "jobs",
            "career",
            "careers",
            "vacancy",
            "vacancies",
            "position",
            "opportunity",
            "employment",
            "internship",
            "intern",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        if limit <= 0:
            return []

        results: list[dict] = []
        seen: set[str] = set()

        query_terms = {
            term.strip().lower()
            for term in query.split()
            if len(term.strip()) >= 3
        }

        for page in self.pages:
            page_url = str(
                page.get("url") or ""
            ).strip()

            if not page_url:
                continue

            try:
                response = requests.get(
                    page_url,
                    headers=HEADERS,
                    timeout=TIMEOUT,
                )

                if response.status_code in {
                    401,
                    403,
                    429,
                }:
                    logger.info(
                        "Skipping inaccessible page %s: HTTP %s",
                        page_url,
                        response.status_code,
                    )
                    continue

                response.raise_for_status()

            except requests.RequestException as exc:
                logger.warning(
                    "Could not fetch %s: %s",
                    page_url,
                    exc,
                )
                continue

            soup = BeautifulSoup(
                response.text,
                "html.parser",
            )

            source = (
                page.get("source")
                or urlparse(page_url).netloc
            )

            for anchor in soup.select("a[href]"):
                href = anchor.get("href")

                if not href:
                    continue

                title = anchor.get_text(
                    " ",
                    strip=True,
                )

                if not title:
                    continue

                if not self._looks_like_job_link(
                    href,
                    title,
                ):
                    continue

                target = self._clean_url(
                    urljoin(page_url, href)
                )

                parsed = urlparse(target)

                if parsed.scheme not in {
                    "http",
                    "https",
                }:
                    continue

                if not parsed.netloc:
                    continue

                if target == self._clean_url(page_url):
                    continue

                if target in seen:
                    continue

                # Keep query matching loose. If the page itself is a
                # search/category page, job links often won't contain
                # every query word.
                combined = (
                    f"{title} {target}"
                ).lower()

                relevance = sum(
                    1
                    for term in query_terms
                    if term in combined
                )

                if query_terms and relevance == 0:
                    continue

                seen.add(target)

                results.append(
                    {
                        "external_id": self._external_id(
                            target
                        ),
                        "title": title[:255],
                        "job_url": target,
                        "source": source,
                        "discovered_at": datetime.utcnow(),
                    }
                )

                if len(results) >= limit:
                    return results

        return results

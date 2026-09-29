from __future__ import annotations

import logging
from typing import Any

import requests

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


class GreenhouseProvider(DiscoveryProvider):
    name = "Greenhouse"

    def __init__(
        self,
        boards: list[str] | None = None,
    ) -> None:
        self.boards = boards or []

    @staticmethod
    def _board_token(board: str) -> str | None:
        value = str(board or "").strip().rstrip("/")

        if not value:
            return None

        if "/" not in value:
            return value

        token = value.split("/")[-1].strip()

        return token or None

    @staticmethod
    def _job_matches(
        job: dict[str, Any],
        query: str,
    ) -> bool:
        query_terms = {
            term.strip().lower()
            for term in query.split()
            if len(term.strip()) >= 3
        }

        if not query_terms:
            return True

        title = str(job.get("title") or "").lower()
        content = str(job.get("content") or "").lower()

        departments = " ".join(
            str(item.get("name") or "")
            for item in job.get("departments", [])
            if isinstance(item, dict)
        ).lower()

        offices = " ".join(
            str(item.get("name") or "")
            for item in job.get("offices", [])
            if isinstance(item, dict)
        ).lower()

        searchable = " ".join(
            [title, content, departments, offices]
        )

        return any(
            term in searchable
            for term in query_terms
        )

    @staticmethod
    def _location(job: dict[str, Any]) -> str:
        locations = [
            str(item.get("name") or "").strip()
            for item in job.get("offices", [])
            if isinstance(item, dict)
        ]

        return ", ".join(
            value for value in locations if value
        )

    def _fetch_job_page(self, job_url: str, fallback_company: str) -> tuple[str, str]:
        try:
            response = requests.get(
                job_url,
                headers=HEADERS,
                timeout=TIMEOUT,
            )
            if response.status_code != 200:
                return "", fallback_company

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            page_text = soup.get_text(" ", strip=True)

            company = fallback_company
            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            marker = " at "

            if marker in title:
                extracted = title.rsplit(marker, 1)[-1].strip()
                if extracted:
                    company = extracted[:255]

            return page_text, company

        except requests.RequestException:
            return "", fallback_company

    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:

        if limit <= 0:
            return []

        results = []
        seen = set()

        for board in self.boards:
            token = self._board_token(board)

            if not token:
                continue

            endpoint = (
                "https://boards-api.greenhouse.io/v1/boards/"
                f"{token}/jobs"
            )

            try:
                response = requests.get(
                    endpoint,
                    headers=HEADERS,
                    timeout=TIMEOUT,
                )

                if response.status_code in {
                    401, 403, 429
                }:
                    logger.info(
                        "Skipping Greenhouse board %s: HTTP %s",
                        token,
                        response.status_code,
                    )
                    continue

                response.raise_for_status()
                payload = response.json()

            except (
                requests.RequestException,
                ValueError,
            ) as exc:
                logger.warning(
                    "Could not fetch Greenhouse board %s: %s",
                    token,
                    exc,
                )
                continue

            jobs = payload.get("jobs", [])

            if not isinstance(jobs, list):
                continue

            for job in jobs:
                if not isinstance(job, dict):
                    continue

                if not self._job_matches(job, query):
                    continue

                job_url = str(
                    job.get("absolute_url") or ""
                ).strip()

                if not job_url or job_url in seen:
                    continue

                title = str(
                    job.get("title") or ""
                ).strip()

                if not title:
                    continue

                seen.add(job_url)

                page_text, company = self._fetch_job_page(
                    job_url,
                    token,
                )

                results.append({
                    "external_id": (
                        f"greenhouse:{token}:"
                        f"{job.get('id')}"
                    ),
                    "title": title[:255],
                    "company": company,
                    "location": self._location(job),
                    "description": page_text,
                    "requirements": "",
                    "experience_requirements": "",
                    "education_requirements": "",
                    "job_url": job_url,
                    "source": self.name,
                    "employment_type": "",
                    "salary": "",
                    "date_posted": None,
                    "valid_through": None,
                })

                if len(results) >= limit:
                    return results

        return results

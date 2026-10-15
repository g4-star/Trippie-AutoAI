from __future__ import annotations

import logging
import re

from app.services.sources.brighter_monday import (
    discover_job_urls,
    parse_job_page,
)

from .base import DiscoveryProvider


logger = logging.getLogger(__name__)


class BrighterMondayProvider(DiscoveryProvider):
    """
    BrighterMonday public-job provider.

    Discovery relevance is intentionally stricter than candidate
    matching. The purpose here is to determine whether a vacancy
    belongs to the requested search topic.

    Final candidate/job fit is handled by job_matcher.py.
    """

    name = "BrighterMonday"

    ROLE_GROUPS = {
        "cybersecurity": {
            "cybersecurity",
            "cyber security",
            "information security",
            "security analyst",
            "security engineer",
            "security operations",
            "soc analyst",
            "soc",
            "infosec",
            "penetration tester",
            "penetration testing",
            "ethical hacker",
            "ethical hacking",
            "network security",
            "incident response",
            "threat intelligence",
            "vulnerability",
        },
        "soc": {
            "soc",
            "soc analyst",
            "security operations",
            "security analyst",
            "cybersecurity",
            "cyber security",
            "incident response",
            "threat detection",
        },
        "security": {
            "security analyst",
            "security engineer",
            "information security",
            "cybersecurity",
            "cyber security",
            "network security",
            "application security",
            "security operations",
            "soc",
            "penetration testing",
            "ethical hacking",
        },
        "software developer": {
            "software developer",
            "software engineer",
            "software development",
            "developer",
            "programmer",
            "application developer",
            "full stack developer",
            "frontend developer",
            "backend developer",
            "web developer",
            "mobile developer",
        },
        "python developer": {
            "python developer",
            "python engineer",
            "python",
            "django",
            "flask",
            "fastapi",
        },
        "flutter developer": {
            "flutter developer",
            "flutter",
            "dart developer",
            "dart",
            "mobile developer",
            "mobile application developer",
        },
        "react developer": {
            "react developer",
            "react.js developer",
            "frontend developer",
            "frontend engineer",
            "javascript developer",
            "typescript developer",
        },
        "it support": {
            "it support",
            "technical support",
            "help desk",
            "service desk",
            "desktop support",
            "it technician",
            "technical support specialist",
            "it support specialist",
        },
        "technical support": {
            "technical support",
            "technical support specialist",
            "it support",
            "help desk",
            "service desk",
            "desktop support",
        },
        "data analyst": {
            "data analyst",
            "data analysis",
            "data analytics",
            "business intelligence analyst",
            "bi analyst",
            "reporting analyst",
            "analytics analyst",
        },
        "business analyst": {
            "business analyst",
            "business analysis",
            "business intelligence analyst",
            "requirements analyst",
        },
        "operations analyst": {
            "operations analyst",
            "operations analysis",
            "business operations analyst",
            "process analyst",
        },
        "supply chain": {
            "supply chain",
            "supply chain analyst",
            "supply chain officer",
            "supply chain management",
            "procurement",
            "logistics",
            "inventory",
        },
    }

    def _normalize(self, value: str) -> str:
        value = value.lower()
        value = re.sub(r"[^a-z0-9+#.\-/ ]+", " ", value)
        return " ".join(value.split())

    def _query_key(self, query: str) -> str:
        normalized = self._normalize(query)

        # Check longer/specific phrases first.
        candidates = sorted(
            self.ROLE_GROUPS,
            key=len,
            reverse=True,
        )

        for candidate in candidates:
            if candidate in normalized:
                return candidate

        return normalized

    def _term_matches(self, text: str, term: str) -> bool:
        """
        Match a discovery term as a complete word or phrase.

        This prevents short terms such as "soc" from matching
        unrelated words such as "social".
        """
        normalized_text = self._normalize(text)
        normalized_term = self._normalize(term)

        if not normalized_text or not normalized_term:
            return False

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(normalized_term)
            + r"(?![a-z0-9])"
        )

        return re.search(pattern, normalized_text) is not None

    def _score_job(
        self,
        job: dict,
        query: str,
    ) -> tuple[int, list[str]]:
        title = self._normalize(
            str(job.get("title") or "")
        )

        company = self._normalize(
            str(job.get("company") or "")
        )

        body = self._normalize(
            " ".join(
                str(job.get(field) or "")
                for field in (
                    "description",
                    "requirements",
                    "responsibilities",
                    "experience_requirements",
                )
            )
        )

        normalized_query = self._normalize(query)
        query_key = self._query_key(query)

        # Direct phrase is the strongest signal.
        if self._term_matches(title, normalized_query):
            return 100, [normalized_query]

        if self._term_matches(body, normalized_query):
            return 50, [normalized_query]

        terms = self.ROLE_GROUPS.get(
            query_key,
            set(),
        )

        if not terms:
            # For unknown searches, require the complete query phrase.
            return 0, []

        title_matches = [
            term
            for term in terms
            if self._term_matches(title, term)
        ]

        body_matches = [
            term
            for term in terms
            if self._term_matches(body, term)
            and term not in title_matches
        ]

        # A related role in the TITLE is a strong signal.
        if title_matches:
            score = 70 + min(
                len(title_matches) * 5,
                25,
            )

            return score, title_matches

        # Body-only matches are weaker. Require at least two
        # independent meaningful terms before considering the job
        # relevant.
        if len(body_matches) >= 2:
            score = min(
                30 + len(body_matches) * 5,
                60,
            )

            return score, body_matches

        return 0, []

    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:

        if limit <= 0:
            return []

        try:
            urls = discover_job_urls(
                limit=max(limit * 8, 40),
                query=query,
            )
        except Exception as exc:
            logger.warning(
                "BrighterMonday URL discovery failed: %s",
                exc,
            )
            return []

        results: list[dict] = []
        seen: set[str] = set()

        for url in urls:
            if not url or url in seen:
                continue

            seen.add(url)

            try:
                job = parse_job_page(url)
            except Exception as exc:
                logger.debug(
                    "Could not parse BrighterMonday job %s: %s",
                    url,
                    exc,
                )
                continue

            if not job:
                continue

            relevance, matched_terms = self._score_job(
                job,
                query,
            )

            if relevance <= 0:
                continue

            job["discovery_relevance"] = relevance
            job["discovery_query"] = query
            job["discovery_matched_terms"] = matched_terms
            job["source"] = self.name

            results.append(job)

        results.sort(
            key=lambda item: (
                item.get("discovery_relevance", 0),
                item.get("date_posted") or "",
            ),
            reverse=True,
        )

        return results[:limit]

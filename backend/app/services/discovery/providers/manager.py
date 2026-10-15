from __future__ import annotations

import logging

from .base import DiscoveryProvider

logger = logging.getLogger(__name__)


class DiscoveryProviderManager:
    """Query providers fairly while isolating failures and deduplicating URLs."""

    def __init__(
        self,
        providers: list[DiscoveryProvider] | None = None,
    ) -> None:
        self.providers = providers or []

    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        if limit <= 0 or not self.providers:
            return []

        results: list[dict] = []
        seen_urls: set[str] = set()

        # Give every provider an initial opportunity before filling spare slots.
        per_provider = max(1, (limit + len(self.providers) - 1) // len(self.providers))

        for provider in self.providers:
            if len(results) >= limit:
                break

            try:
                provider_results = provider.search(
                    query=query,
                    limit=per_provider,
                )
            except Exception as exc:
                logger.warning(
                    "Discovery provider %s failed for %r: %s",
                    getattr(provider, "name", "unknown"),
                    query,
                    exc,
                )
                continue

            for item in provider_results:
                if not isinstance(item, dict):
                    continue

                job_url = str(item.get("job_url") or "").strip()
                if not job_url or job_url in seen_urls:
                    continue

                seen_urls.add(job_url)
                results.append(item)

                if len(results) >= limit:
                    break

        return results

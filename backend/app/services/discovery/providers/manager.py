from __future__ import annotations

import logging

from .base import DiscoveryProvider


logger = logging.getLogger(__name__)


class DiscoveryProviderManager:
    """
    Runs multiple public discovery providers.

    Providers are isolated from one another: if one provider fails,
    the remaining providers can continue.
    """

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
        results: list[dict] = []
        seen_urls: set[str] = set()

        if limit <= 0:
            return results

        for provider in self.providers:
            remaining = limit - len(results)

            if remaining <= 0:
                break

            try:
                provider_results = provider.search(
                    query=query,
                    limit=remaining,
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
                job_url = str(
                    item.get("job_url") or ""
                ).strip()

                if not job_url:
                    continue

                if job_url in seen_urls:
                    continue

                seen_urls.add(job_url)
                results.append(item)

                if len(results) >= limit:
                    break

        return results

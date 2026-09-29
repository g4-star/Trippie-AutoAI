from __future__ import annotations

from abc import ABC, abstractmethod


class DiscoveryProvider(ABC):
    """
    Common interface for every public job-discovery provider.

    A provider may be a search engine, job board, ATS directory,
    company career source, or another public source.
    """

    name: str = "unknown"

    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Return candidate URLs.

        Providers should return lightweight records containing
        at least:

            title
            job_url
            source
        """
        raise NotImplementedError

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.database import Base, engine
from app.models.discovery_state import DiscoveryState
from app.services.discovery.providers import (
    BrighterMondayProvider,
    DiscoveryProviderManager,
    DuckDuckGoProvider,
    GreenhouseProvider,
    PublicPageProvider,
)
from app.services.discovery.search_planner import build_search_queries
from app.services.job_discovery import save_discovered_job


logger = logging.getLogger(__name__)


# Public ATS/company sources that can be queried without login.
GREENHOUSE_BOARDS = [
    "https://boards.greenhouse.io/andela",
    "https://boards.greenhouse.io/flutterwave",
    "https://boards.greenhouse.io/moniepoint",
    "https://boards.greenhouse.io/wise",
    "https://boards.greenhouse.io/stripe",
]


PUBLIC_CAREER_PAGES = [
    {
        "url": "https://www.safaricom.co.ke/careers",
        "source": "Safaricom",
    },
    {
        "url": "https://www.kcbgroup.com/careers/",
        "source": "KCB",
    },
    {
        "url": "https://www.equitygroupholdings.com/careers/",
        "source": "Equity Bank",
    },
]


def build_provider_manager() -> DiscoveryProviderManager:
    """
    Build all enabled public job-discovery providers.

    Providers are isolated. If one source is blocked, unavailable,
    or temporarily fails, discovery continues with the others.
    """

    providers = [
        BrighterMondayProvider(),
        DuckDuckGoProvider(),

        # Public ATS source.
        GreenhouseProvider(
            boards=GREENHOUSE_BOARDS,
        ),

        # Public company career pages.
        PublicPageProvider(
            pages=PUBLIC_CAREER_PAGES,
        ),
    ]

    return DiscoveryProviderManager(
        providers=providers,
    )


def ensure_discovery_state_table() -> None:
    inspector = inspect(engine)

    if "discovery_states" not in inspector.get_table_names():
        Base.metadata.create_all(
            bind=engine,
            tables=[DiscoveryState.__table__],
        )


def get_discovery_state(
    db: Session,
    user_id: int,
) -> DiscoveryState:

    state = (
        db.query(DiscoveryState)
        .filter(DiscoveryState.user_id == user_id)
        .first()
    )

    if state is None:
        state = DiscoveryState(
            user_id=user_id,
            query_offset=0,
            total_cycles=0,
        )

        db.add(state)
        db.commit()
        db.refresh(state)

    return state


def select_rotating_queries(
    queries: list[str],
    offset: int,
    count: int,
) -> tuple[list[str], int]:

    if not queries or count <= 0:
        return [], 0

    total = len(queries)
    start = offset % total

    selected = [
        queries[(start + index) % total]
        for index in range(min(count, total))
    ]

    next_offset = (
        start + len(selected)
    ) % total

    return selected, next_offset


def discover_internet_jobs(
    *,
    db: Session,
    user_id: int,
    queries_per_cycle: int = 8,
    results_per_query: int = 10,
) -> dict:

    ensure_discovery_state_table()

    all_queries = build_search_queries(
        db,
        user_id,
    )

    state = get_discovery_state(
        db,
        user_id,
    )

    selected_queries, next_offset = (
        select_rotating_queries(
            all_queries,
            state.query_offset,
            queries_per_cycle,
        )
    )

    logger.info(
        "Discovery cycle %s: %s queries",
        state.total_cycles + 1,
        len(selected_queries),
    )

    manager = build_provider_manager()

    discovered = 0
    created = 0
    updated = 0
    failed = 0

    searched = []
    provider_results: dict[str, int] = {}

    for query in selected_queries:

        searched.append(query)

        try:
            jobs = manager.search(
                query=query,
                limit=results_per_query,
            )

        except Exception as exc:
            logger.warning(
                "Discovery failed for %r: %s",
                query,
                exc,
            )

            failed += 1
            continue

        discovered += len(jobs)

        for job_data in jobs:

            source = str(
                job_data.get("source")
                or "unknown"
            )

            provider_results[source] = (
                provider_results.get(source, 0) + 1
            )

            try:

                _, was_created = (
                    save_discovered_job(
                        db,
                        job_data,
                    )
                )

                if was_created:
                    created += 1
                else:
                    updated += 1

            except Exception as exc:

                db.rollback()

                logger.warning(
                    "Could not save discovered job: %s",
                    exc,
                )

                failed += 1

    previous_offset = state.query_offset

    state.query_offset = next_offset
    state.total_cycles += 1
    state.last_run_at = datetime.utcnow()
    state.updated_at = datetime.utcnow()

    db.commit()

    return {
        "cycle": state.total_cycles,
        "queries_run": len(searched),
        "total_queries_available": len(all_queries),
        "previous_offset": previous_offset,
        "next_offset": next_offset,
        "discovered": discovered,
        "created": created,
        "updated": updated,
        "failed": failed,
        "provider_results": provider_results,
        "queries": searched,
    }

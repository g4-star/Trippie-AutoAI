from __future__ import annotations

import threading

from app.database import SessionLocal
from app.models.settings import Settings
from app.services.agent_runner import run_agent


USER_ID = 1
CYCLE_INTERVAL_SECONDS = 60

_worker_thread: threading.Thread | None = None
_worker_stop_event = threading.Event()


def _worker_loop() -> None:
    while not _worker_stop_event.is_set():
        db = SessionLocal()

        try:
            settings = db.query(Settings).filter(
                Settings.user_id == USER_ID
            ).first()

            if settings and settings.agent_enabled:
                try:
                    result = run_agent(
                        db=db,
                        user_id=USER_ID,
                    )

                    print(
                        "[AI AGENT] cycle:",
                        result,
                        flush=True,
                    )

                except Exception as error:
                    print(
                        f"[AI AGENT] cycle failed: {error}",
                        flush=True,
                    )

        finally:
            db.close()

        _worker_stop_event.wait(
            CYCLE_INTERVAL_SECONDS
        )


def start_agent_worker() -> None:
    global _worker_thread

    if (
        _worker_thread is not None
        and _worker_thread.is_alive()
    ):
        return

    _worker_stop_event.clear()

    _worker_thread = threading.Thread(
        target=_worker_loop,
        name="trippie-ai-agent",
        daemon=True,
    )

    _worker_thread.start()

    print(
        "[AI AGENT] background worker started.",
        flush=True,
    )


def stop_agent_worker() -> None:
    global _worker_thread

    _worker_stop_event.set()

    if (
        _worker_thread is not None
        and _worker_thread.is_alive()
    ):
        _worker_thread.join(
            timeout=5
        )

    _worker_thread = None

    print(
        "[AI AGENT] background worker stopped.",
        flush=True,
    )

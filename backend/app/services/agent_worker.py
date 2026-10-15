from __future__ import annotations

import logging
import os
import threading

from app.database import SessionLocal
from app.models.settings import Settings
from app.services.agent_runner import run_agent

logger = logging.getLogger(__name__)

USER_ID = int(os.getenv("AUTOAI_USER_ID", "1"))
CYCLE_INTERVAL_SECONDS = max(
    60,
    int(os.getenv("AGENT_CYCLE_INTERVAL_SECONDS", "300")),
)

_worker_thread: threading.Thread | None = None
_worker_stop_event = threading.Event()
_worker_lock = threading.Lock()


def _worker_loop() -> None:
    logger.info("AI agent worker loop started for user %s", USER_ID)

    while not _worker_stop_event.is_set():
        try:
            db = SessionLocal()
            try:
                settings = (
                    db.query(Settings)
                    .filter(Settings.user_id == USER_ID)
                    .first()
                )
                enabled = bool(settings and settings.agent_enabled)
            finally:
                db.close()

            if _worker_stop_event.is_set():
                break

            if not enabled:
                # Poll periodically so API Start can enable the worker
                # without requiring a server restart.
                _worker_stop_event.wait(min(15, CYCLE_INTERVAL_SECONDS))
                continue

            db = SessionLocal()
            try:
                result = run_agent(db=db, user_id=USER_ID)
                logger.info("AI agent cycle finished: %s", result)
            finally:
                db.close()

        except Exception:
            logger.exception("AI agent worker cycle failed")

        # Wait interruptibly so Stop and server shutdown take effect promptly.
        _worker_stop_event.wait(CYCLE_INTERVAL_SECONDS)

    logger.info("AI agent worker loop exited for user %s", USER_ID)


def start_agent_worker() -> bool:
    """Start one worker thread. Return False if one is already active."""
    global _worker_thread

    with _worker_lock:
        if _worker_thread is not None and _worker_thread.is_alive():
            return False

        _worker_stop_event.clear()
        _worker_thread = threading.Thread(
            target=_worker_loop,
            name=f"trippie-ai-agent-{USER_ID}",
            daemon=True,
        )
        _worker_thread.start()

    logger.info(
        "AI agent worker started; user=%s interval=%ss",
        USER_ID,
        CYCLE_INTERVAL_SECONDS,
    )
    return True


def stop_agent_worker(timeout: float = 10) -> bool:
    """Signal the worker to stop and wait briefly for the current cycle."""
    global _worker_thread

    with _worker_lock:
        thread = _worker_thread
        if thread is None:
            return True
        _worker_stop_event.set()

    if thread.is_alive() and thread is not threading.current_thread():
        thread.join(timeout=max(0, timeout))

    stopped = not thread.is_alive()

    with _worker_lock:
        if stopped and _worker_thread is thread:
            _worker_thread = None

    if not stopped:
        logger.warning(
            "AI agent worker is still finishing its current cycle; "
            "it will exit after that cycle."
        )

    return stopped


def is_agent_worker_alive() -> bool:
    thread = _worker_thread
    return bool(thread and thread.is_alive())

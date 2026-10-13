from __future__ import annotations

import logging
import os

import requests

logger = logging.getLogger(__name__)


def notify_job_draft_ready(
    *, job_title: str, company: str, match_score: int, gmail_draft_url: str
) -> tuple[bool, str | None]:
    """Send a concise SMS via ClickSend when credentials and a recipient are configured."""
    username = os.getenv("CLICKSEND_USERNAME", "").strip()
    api_key = os.getenv("CLICKSEND_API_KEY", "").strip()
    recipient = os.getenv("AUTOAI_NOTIFY_PHONE", "").strip()
    if not (username and api_key and recipient):
        return False, "SMS not configured (set CLICKSEND_USERNAME, CLICKSEND_API_KEY, AUTOAI_NOTIFY_PHONE)."

    if not recipient.startswith("+") or not recipient[1:].isdigit():
        return False, "AUTOAI_NOTIFY_PHONE must be in international format, e.g. +2547XXXXXXXX."

    title = " ".join((job_title or "Job opportunity").split())[:42]
    employer = " ".join((company or "employer not listed").split())[:28]
    body = f"Trippie AutoAI: {title} at {employer} ({match_score}% match) is ready. Review/send: {gmail_draft_url}"
    try:
        response = requests.post(
            "https://rest.clicksend.com/v3/sms/send",
            auth=(username, api_key),
            json={"messages": [{"to": recipient, "body": body, "source": "trippie-autoai"}]},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") or {}
        messages = data.get("messages") or []
        if not messages or str(messages[0].get("status", "")).lower() not in {
            "queued", "sent", "scheduled", "success"
        }:
            reason = str(messages[0].get("status") if messages else payload.get("response_code", "no message status"))
            logger.warning("ClickSend did not queue job-draft SMS: %s", reason)
            return False, f"ClickSend did not confirm the SMS was queued: {reason}"
        return True, None
    except Exception as error:
        logger.exception("Unable to send job-draft SMS notification")
        return False, str(error)[:500]

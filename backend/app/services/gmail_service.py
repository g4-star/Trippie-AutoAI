from __future__ import annotations

import base64
import re
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.email import Email
from app.services.email_agent import (
    classify_by_gmail_labels,
    classify_email,
    detect_job_alert,
)


BASE_DIR = Path(__file__).resolve().parents[2]

CREDENTIALS_FILE = BASE_DIR / "secrets" / "credentials.json"
TOKEN_FILE = BASE_DIR / "secrets" / "gmail_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

# Temporary in-memory storage for local development.
# The same Flow object must survive from /connect to /callback
# because it contains the PKCE code verifier.
_pending_flow: Flow | None = None
_pending_state: str | None = None


def create_gmail_flow(
    redirect_uri: str,
    state: str | None = None,
) -> Flow:
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Gmail credentials not found: {CREDENTIALS_FILE}"
        )

    return Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        state=state,
    )


def get_authorization_url(redirect_uri: str) -> str:
    global _pending_flow
    global _pending_state

    flow = create_gmail_flow(redirect_uri)

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    _pending_flow = flow
    _pending_state = state

    return authorization_url


def complete_authorization(
    redirect_uri: str,
    authorization_response: str,
) -> None:
    global _pending_flow
    global _pending_state

    if _pending_flow is None:
        raise RuntimeError(
            "No pending Gmail authorization was found. "
            "Start the connection again."
        )

    if not _pending_state:
        raise RuntimeError(
            "No pending Gmail authorization state was found."
        )

    flow = _pending_flow

    flow.fetch_token(
        authorization_response=authorization_response,
    )

    credentials = flow.credentials

    TOKEN_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with TOKEN_FILE.open("w") as token_file:
        token_file.write(credentials.to_json())

    TOKEN_FILE.chmod(0o600)

    _pending_flow = None
    _pending_state = None


def _get_gmail_credentials() -> Credentials:
    if not TOKEN_FILE.exists():
        raise FileNotFoundError(
            "Gmail is not connected. Connect a Gmail account first."
        )

    credentials = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        SCOPES,
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )
        TOKEN_FILE.chmod(0o600)

    if not credentials.valid:
        raise RuntimeError(
            "Gmail credentials are invalid or expired. "
            "Reconnect the Gmail account."
        )

    return credentials


def _decode_base64url(data: str) -> str:
    if not data:
        return ""

    try:
        padding = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(
            data + padding
        ).decode(
            "utf-8",
            errors="replace",
        )
    except Exception:
        return ""


def _html_to_text(html: str) -> str:
    text = re.sub(
        r"<(script|style).*?>.*?</\1>",
        " ",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    text = re.sub(
        r"<br\s*/?>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"</(p|div|li|tr)>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n\s*\n+",
        "\n\n",
        text,
    )

    return text.strip()


def _extract_headers(payload: dict[str, Any]) -> dict[str, str]:
    headers = {}

    for header in payload.get("headers", []):
        name = header.get("name", "").lower()
        value = header.get("value", "")

        if name:
            headers[name] = value

    return headers


def _extract_body(payload: dict[str, Any]) -> str:
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    if body_data:
        decoded = _decode_base64url(body_data)

        if mime_type == "text/html":
            return _html_to_text(decoded)

        return decoded.strip()

    parts = payload.get("parts", [])

    plain_text = ""
    html_text = ""

    for part in parts:
        part_type = part.get("mimeType", "")

        if part_type == "text/plain":
            data = part.get("body", {}).get("data")

            if data:
                plain_text += _decode_base64url(data)

        elif part_type == "text/html":
            data = part.get("body", {}).get("data")

            if data:
                html_text += _decode_base64url(data)

        elif part.get("parts"):
            nested = _extract_body(part)

            if nested:
                plain_text += nested

    if plain_text.strip():
        return plain_text.strip()

    if html_text.strip():
        return _html_to_text(html_text)

    return ""


def _parse_received_at(internal_date: str | None) -> datetime | None:
    if not internal_date:
        return None

    try:
        timestamp = int(internal_date) / 1000

        return datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        ).replace(tzinfo=None)
    except (TypeError, ValueError, OSError):
        return None


def _get_message(
    gmail: Any,
    message_id: str,
) -> dict[str, Any]:
    return (
        gmail.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="full",
        )
        .execute()
    )



def send_gmail_reply(
    *,
    to: str,
    subject: str,
    body: str,
    original_message_id: str,
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Send a reply to an existing Gmail message."""

    if not to:
        raise ValueError("Reply recipient is required.")

    if not body.strip():
        raise ValueError("Reply body cannot be empty.")

    if not original_message_id:
        raise ValueError("Original Gmail message ID is required.")

    credentials = _get_gmail_credentials()

    gmail = build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )

    # Fetch the original Gmail message so we can use its real
    # RFC Message-ID header and Gmail thread ID.
    original_message = _get_message(
        gmail,
        original_message_id,
    )

    original_headers = _extract_headers(
        original_message.get("payload", {})
    )

    original_rfc_message_id = original_headers.get("message-id")

    if not original_rfc_message_id:
        raise ValueError(
            "The original Gmail message does not contain a Message-ID header."
        )

    actual_thread_id = (
        thread_id
        or original_message.get("threadId")
    )

    reply_subject = subject.strip()

    if reply_subject and not reply_subject.lower().startswith("re:"):
        reply_subject = f"Re: {reply_subject}"

    message = MIMEText(
        body.strip(),
        "plain",
        "utf-8",
    )

    message["To"] = to
    message["Subject"] = reply_subject or "Re:"
    message["In-Reply-To"] = original_rfc_message_id
    message["References"] = original_rfc_message_id

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode("utf-8")

    request_body: dict[str, Any] = {
        "raw": raw_message,
    }

    if actual_thread_id:
        request_body["threadId"] = actual_thread_id

    result = (
        gmail.users()
        .messages()
        .send(
            userId="me",
            body=request_body,
        )
        .execute()
    )

    return {
        "status": "sent",
        "message_id": result.get("id"),
        "thread_id": result.get("threadId"),
        "to": to,
        "subject": reply_subject or "Re:",
    }


def sync_gmail(
    db: Session,
    user_id: int,
    max_messages: int = 50,
) -> dict[str, Any]:
    credentials = _get_gmail_credentials()

    gmail = build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )

    result = (
        gmail.users()
        .messages()
        .list(
            userId="me",
            includeSpamTrash=True,
            maxResults=max_messages,
        )
        .execute()
    )

    message_refs = result.get("messages", [])

    created = 0
    updated = 0
    skipped = 0
    classified = 0
    fast_classified = 0

    for message_ref in message_refs:
        gmail_message_id = message_ref.get("id")

        if not gmail_message_id:
            skipped += 1
            continue

        existing = db.scalar(
            select(Email).where(
                Email.user_id == user_id,
                Email.message_id == gmail_message_id,
            )
        )

        # Already-synced messages do not need to be downloaded and
        # rewritten on every agent cycle. New messages are processed
        # fully below.
        if existing:
            skipped += 1
            continue

        message = _get_message(
            gmail,
            gmail_message_id,
        )

        payload = message.get("payload", {})
        headers = _extract_headers(payload)

        sender = headers.get("from", "Unknown sender")
        recipient = headers.get("to")
        subject = headers.get(
            "subject",
            "(No subject)",
        )

        body = _extract_body(payload)

        received_at = _parse_received_at(
            message.get("internalDate")
        )

        label_ids = set(
            message.get("labelIds", [])
        )

        is_read = "UNREAD" not in label_ids
        is_starred = "STARRED" in label_ids

        gmail_labels = ",".join(
            sorted(label_ids)
        )

        email = Email(
            user_id=user_id,
            message_id=gmail_message_id,
            sender=sender,
            recipient=recipient,
            subject=subject,
            body=body,
            received_at=received_at,
            is_read=is_read,
            is_starred=is_starred,
            gmail_labels=gmail_labels,
        )

        fast_result = classify_by_gmail_labels(
            gmail_labels=gmail_labels,
            sender=sender,
            subject=subject,
        )

        if fast_result:
            email.ai_category = fast_result["category"]
            email.ai_summary = fast_result["summary"]
            fast_classified += 1

        else:
            job_result = detect_job_alert(
                sender=sender,
                subject=subject,
            )

            if job_result:
                email.ai_category = job_result["category"]
                email.ai_summary = job_result["summary"]
                fast_classified += 1

            else:
                try:
                    ai_result = classify_email(
                        sender=sender,
                        subject=subject,
                        body=body,
                    )

                    email.ai_category = ai_result["category"]
                    email.ai_summary = ai_result["summary"]
                    classified += 1

                except Exception:
                    # Do not fail Gmail sync because of AI processing.
                    pass

        db.add(email)
        created += 1

    db.commit()

    return {
        "status": "synced",
        "user_id": user_id,
        "requested": max_messages,
        "messages_found": len(message_refs),
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "classified": classified,
        "fast_classified": fast_classified,
    }


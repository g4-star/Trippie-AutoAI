from __future__ import annotations

import base64
import hashlib
import json
import os
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.gmail_draft_authorization import GmailDraftAuthorization


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CREDENTIALS_FILE = BASE_DIR / "secrets" / "credentials.json"
CREDENTIALS_FILE = Path(os.getenv("GMAIL_CREDENTIALS_PATH", str(DEFAULT_CREDENTIALS_FILE)))
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

_pending_flow: Flow | None = None
_pending_state: str | None = None


def _client_config() -> dict[str, Any]:
    raw = os.getenv("GMAIL_CLIENT_CONFIG_JSON")
    if raw:
        try:
            config = json.loads(raw)
        except json.JSONDecodeError as error:
            raise RuntimeError("GMAIL_CLIENT_CONFIG_JSON is not valid JSON.") from error
        if not isinstance(config, dict) or not (config.get("web") or config.get("installed")):
            raise RuntimeError("GMAIL_CLIENT_CONFIG_JSON must contain Google OAuth 'web' or 'installed' client configuration.")
        return config
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            "Gmail OAuth client config is missing. Set GMAIL_CLIENT_CONFIG_JSON "
            "or provide GMAIL_CREDENTIALS_PATH."
        )
    return json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode("utf-8")).digest())
    return Fernet(key)


def _encrypt_credentials(credentials_json: str) -> str:
    return _fernet().encrypt(credentials_json.encode("utf-8")).decode("ascii")


def _decrypt_credentials(encrypted: str) -> str:
    try:
        return _fernet().decrypt(encrypted.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as error:
        raise RuntimeError(
            "Saved Gmail draft authorization could not be decrypted. If SECRET_KEY changed, reconnect Gmail."
        ) from error


def get_draft_authorization_url(redirect_uri: str) -> str:
    global _pending_flow, _pending_state
    _pending_flow = Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    url, _pending_state = _pending_flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return url


def complete_draft_authorization(
    *,
    authorization_response: str,
    db: Session,
    user_id: int,
) -> None:
    global _pending_flow, _pending_state
    if _pending_flow is None or not _pending_state:
        raise RuntimeError("No pending job-draft Gmail authorization. Start the connection again.")
    flow = _pending_flow
    flow.fetch_token(authorization_response=authorization_response)
    serialized = flow.credentials.to_json()
    record = db.scalar(
        select(GmailDraftAuthorization).where(
            GmailDraftAuthorization.user_id == user_id
        )
    )
    if record is None:
        record = GmailDraftAuthorization(
            user_id=user_id,
            credentials_encrypted=_encrypt_credentials(serialized),
        )
        db.add(record)
    else:
        record.credentials_encrypted = _encrypt_credentials(serialized)
        record.updated_at = __import__("datetime").datetime.utcnow()
    db.commit()
    _pending_flow = None
    _pending_state = None


def _get_draft_credentials(*, db: Session, user_id: int) -> Credentials:
    record = db.scalar(
        select(GmailDraftAuthorization).where(
            GmailDraftAuthorization.user_id == user_id
        )
    )
    if not record:
        raise RuntimeError(
            "Job-application Gmail drafts are not connected. Open "
            "/api/job-drafts/gmail/connect to authorize draft creation."
        )
    credentials = Credentials.from_authorized_user_info(
        json.loads(_decrypt_credentials(record.credentials_encrypted)),
        scopes=SCOPES,
    )
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        record.credentials_encrypted = _encrypt_credentials(credentials.to_json())
        record.updated_at = __import__("datetime").datetime.utcnow()
        db.commit()
    if not credentials.valid:
        raise RuntimeError("Gmail draft authorization is expired or invalid; reconnect Gmail.")
    return credentials


def create_gmail_draft(
    *,
    db: Session,
    user_id: int,
    to: str,
    subject: str,
    body: str,
) -> dict[str, str]:
    if not to or "@" not in to:
        raise ValueError("A verified recipient email is required.")
    if not subject.strip() or not body.strip():
        raise ValueError("Draft subject and body are required.")

    message = MIMEText(body.strip(), "plain", "utf-8")
    message["To"] = to
    message["Subject"] = subject.strip()
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    gmail = build(
        "gmail", "v1",
        credentials=_get_draft_credentials(db=db, user_id=user_id),
        cache_discovery=False,
    )
    result = gmail.users().drafts().create(
        userId="me", body={"message": {"raw": raw}}
    ).execute()
    draft_id = str(result.get("id") or "")
    if not draft_id:
        raise RuntimeError("Gmail did not return a draft ID.")
    return {
        "draft_id": draft_id,
        "message_id": str((result.get("message") or {}).get("id") or ""),
        "url": f"https://mail.google.com/mail/u/0/#drafts/{draft_id}",
    }

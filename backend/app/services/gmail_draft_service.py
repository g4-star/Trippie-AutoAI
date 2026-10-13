from __future__ import annotations

import base64
import hashlib
import json
import os
from email.message import EmailMessage
from datetime import datetime, timedelta
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
from app.models.gmail_oauth_transaction import GmailOAuthTransaction


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CREDENTIALS_FILE = BASE_DIR / "secrets" / "credentials.json"
CREDENTIALS_FILE = Path(os.getenv("GMAIL_CREDENTIALS_PATH", str(DEFAULT_CREDENTIALS_FILE)))
# Only compose access is requested. The user reviews and sends directly in Gmail.
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]



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


def get_draft_authorization_url(*, redirect_uri: str, db: Session) -> str:
    flow = Flow.from_client_config(
        _client_config(), scopes=SCOPES, redirect_uri=redirect_uri
    )
    url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )

    # Remove expired transactions and persist this transaction before redirecting.
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    db.query(GmailOAuthTransaction).filter(
        GmailOAuthTransaction.created_at < cutoff
    ).delete(synchronize_session=False)

    db.add(GmailOAuthTransaction(state=state, redirect_uri=redirect_uri))
    db.commit()
    return url


def complete_draft_authorization(
    *,
    authorization_response: str,
    state: str,
    redirect_uri: str,
    db: Session,
    user_id: int,
) -> None:
    if not state:
        raise RuntimeError("OAuth state is missing. Start Gmail connection again.")

    transaction = db.get(GmailOAuthTransaction, state)
    if transaction is None:
        raise RuntimeError(
            "Gmail authorization state is invalid, expired, or already used. "
            "Start the connection again."
        )

    if transaction.redirect_uri != redirect_uri:
        raise RuntimeError(
            "Gmail callback URL differs from the original authorization URL. "
            "Check the production domain and Google OAuth redirect URI."
        )

    if datetime.utcnow() - transaction.created_at > timedelta(minutes=10):
        db.delete(transaction)
        db.commit()
        raise RuntimeError("Gmail authorization expired. Start the connection again.")

    # Rebuild the flow in this request and require Google's returned state to match.
    flow = Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        state=state,
        redirect_uri=redirect_uri,
    )
    flow.fetch_token(authorization_response=authorization_response)

    serialized = flow.credentials.to_json()
    record = db.scalar(
        select(GmailDraftAuthorization).where(
            GmailDraftAuthorization.user_id == user_id
        )
    )
    encrypted = _encrypt_credentials(serialized)

    if record is None:
        record = GmailDraftAuthorization(
            user_id=user_id, credentials_encrypted=encrypted
        )
        db.add(record)
    else:
        record.credentials_encrypted = encrypted
        record.updated_at = datetime.utcnow()

    # Consume the state and save the encrypted credentials in one transaction.
    db.delete(transaction)
    db.commit()


def _get_draft_credentials(*, db: Session, user_id: int) -> Credentials:
    record = db.scalar(
        select(GmailDraftAuthorization).where(GmailDraftAuthorization.user_id == user_id)
    )
    if not record:
        raise RuntimeError(
            "Job-application Gmail drafts are not connected. Open "
            "/api/job-drafts/gmail/connect to authorize draft creation."
        )
    credentials = Credentials.from_authorized_user_info(
        json.loads(_decrypt_credentials(record.credentials_encrypted)), scopes=SCOPES
    )
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        record.credentials_encrypted = _encrypt_credentials(credentials.to_json())
        from datetime import datetime
        record.updated_at = datetime.utcnow()
        db.commit()
    if not credentials.valid:
        raise RuntimeError("Gmail draft authorization is expired or invalid; reconnect Gmail.")
    return credentials


def create_gmail_draft(
    *, db: Session, user_id: int, to: str, subject: str, body: str, body_html: str | None = None
) -> dict[str, str]:
    if not to or "@" not in to:
        raise ValueError("A verified recipient email is required.")
    if not subject.strip() or not body.strip():
        raise ValueError("Draft subject and body are required.")

    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject.strip()
    message.set_content(body.strip())
    if body_html:
        message.add_alternative(body_html, subtype="html")
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    gmail = build(
        "gmail", "v1", credentials=_get_draft_credentials(db=db, user_id=user_id),
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

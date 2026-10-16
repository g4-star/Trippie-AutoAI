import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.refresh_session import RefreshSession

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

ALGORITHM = "HS256"
PBKDF2_ITERATIONS = 600_000


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=256)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=512)


class LogoutRequest(BaseModel):
    refresh_token: str | None = Field(default=None, min_length=20, max_length=512)


class LegacyBootstrapRequest(BaseModel):
    setup_code: str = Field(min_length=32, max_length=512)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(derived).decode("ascii"),
    )


def _verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        algorithm, rounds, salt_text, expected_text = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(expected_text.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(rounds)
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _make_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user.id),
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        },
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def _public_user(user: User) -> dict:
    return {"id": user.id, "full_name": user.full_name, "email": user.email}


def _create_refresh_token(db: Session, user: User) -> str:
    raw_token = secrets.token_urlsafe(48)
    db.add(
        RefreshSession(
            user_id=user.id,
            token_hash=hashlib.sha256(raw_token.encode("utf-8")).hexdigest(),
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
    )
    return raw_token


def _token_response(db: Session, user: User) -> dict:
    refresh_token = _create_refresh_token(db, user)
    db.commit()
    return {
        "user": _public_user(user),
        "access_token": _make_token(user),
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[ALGORITHM]
        )
        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise unauthorized
        user_id = int(subject)
    except (JWTError, ValueError, TypeError):
        raise unauthorized

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise unauthorized
    return user


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    email = _normalize_email(data.email)
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")

    # Do not let an unauthenticated request claim an existing profile.
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "An account with this email already exists. "
                "Account recovery or verified account linking is required."
            ),
        )

    user = User(
        full_name=data.full_name.strip(),
        email=email,
        password_hash=_hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _token_response(db, user)


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    email = _normalize_email(data.email)
    user = db.query(User).filter(User.email == email).first()

    if not user or not _verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is disabled.")

    return _token_response(db, user)


@router.post("/legacy-bootstrap")
def legacy_bootstrap(data: LegacyBootstrapRequest, db: Session = Depends(get_db)):
    """Claim the pre-auth account once, only with an explicitly configured secret."""
    configured_key = os.getenv("LEGACY_ACCOUNT_BOOTSTRAP_KEY", "").strip()
    if len(configured_key) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="One-time account setup is not enabled on this server.",
        )
    if not hmac.compare_digest(data.setup_code, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The one-time setup code is invalid.",
        )

    # Never create a replacement profile: the existing account and its data must remain intact.
    user = db.query(User).filter(User.id == 1).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The existing account is unavailable; setup was not completed.",
        )

    # Use the already-existing refresh_sessions table so this feature does not
    # require a schema migration or create a new table on preview startup.
    claim_marker = hashlib.sha256(
        b"trippie-autoai-legacy-account-bootstrap-claimed-v1"
    ).hexdigest()
    if db.query(RefreshSession).filter(RefreshSession.token_hash == claim_marker).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One-time account setup has already been used.",
        )

    now = datetime.utcnow()
    db.add(
        RefreshSession(
            user_id=user.id,
            token_hash=claim_marker,
            expires_at=now + timedelta(days=36500),
            created_at=now,
            revoked_at=now,
        )
    )
    refresh_token = _create_refresh_token(db, user)
    try:
        # The fixed primary key makes simultaneous claims race safely: only one can commit.
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One-time account setup has already been used.",
        )
    return {
        "user": _public_user(user),
        "access_token": _make_token(user),
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(data.refresh_token.encode("utf-8")).hexdigest()
    session = (
        db.query(RefreshSession)
        .filter(RefreshSession.token_hash == token_hash)
        .first()
    )
    now = datetime.utcnow()
    if (
        session is None
        or session.revoked_at is not None
        or session.expires_at <= now
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh session is invalid or expired.",
        )

    user = db.query(User).filter(User.id == session.user_id).first()
    if user is None or not user.is_active:
        session.revoked_at = now
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account unavailable.")

    # Rotate refresh tokens so a previously used token cannot be replayed.
    session.revoked_at = now
    new_refresh_token = _create_refresh_token(db, user)
    db.commit()
    return {
        "user": _public_user(user),
        "access_token": _make_token(user),
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(data: LogoutRequest, db: Session = Depends(get_db)):
    if data.refresh_token:
        token_hash = hashlib.sha256(data.refresh_token.encode("utf-8")).hexdigest()
        session = (
            db.query(RefreshSession)
            .filter(RefreshSession.token_hash == token_hash)
            .first()
        )
        if session is not None and session.revoked_at is None:
            session.revoked_at = datetime.utcnow()
            db.commit()
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _public_user(user)

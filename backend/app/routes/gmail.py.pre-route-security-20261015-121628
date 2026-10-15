from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.email import Email
from app.models.email_reply import EmailReply
from app.models.settings import Settings
from app.services.reply_decision import decide_reply
from app.services.gmail_service import (
    complete_authorization,
    get_authorization_url,
    send_gmail_reply,
    sync_gmail,
)
from app.services.reply_workflow import generate_pending_reply


class GmailReplyRequest(BaseModel):
    body: str


router = APIRouter(
    prefix="/api/gmail",
    tags=["Gmail"],
)


@router.get("/connect")
def connect_gmail(request: Request):
    redirect_uri = str(request.url_for("gmail_callback"))

    try:
        authorization_url = get_authorization_url(redirect_uri)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to start Gmail connection: {error}",
        ) from error

    return RedirectResponse(url=authorization_url)


@router.get("/callback", name="gmail_callback")
def gmail_callback(request: Request):
    error = request.query_params.get("error")

    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Gmail authorization failed: {error}",
        )

    code = request.query_params.get("code")

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Gmail authorization code was not provided.",
        )

    redirect_uri = str(request.url_for("gmail_callback"))

    try:
        complete_authorization(
            redirect_uri=redirect_uri,
            authorization_response=str(request.url),
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to complete Gmail authorization: {error}",
        ) from error

    return {
        "status": "connected",
        "message": "Gmail account connected successfully.",
    }


@router.post("/reply/generate/{user_id}/{email_id}")
def generate_ai_reply(
    user_id: int,
    email_id: int,
    db: Session = Depends(get_db),
):
    try:
        return generate_pending_reply(
            user_id=user_id,
            email_id=email_id,
            db=db,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to generate AI reply: {error}",
        ) from error


@router.get("/replies/{user_id}")
def list_pending_replies(
    user_id: int,
    db: Session = Depends(get_db),
):
    replies = db.scalars(
        select(EmailReply)
        .where(
            EmailReply.user_id == user_id,
            EmailReply.status == "pending_approval",
        )
        .order_by(
            EmailReply.generated_at.desc()
        )
    ).all()

    results = []

    for reply in replies:
        email = db.scalar(
            select(Email).where(
                Email.id == reply.email_id,
                Email.user_id == user_id,
            )
        )

        results.append({
            "reply_id": reply.id,
            "email_id": reply.email_id,
            "sender": email.sender if email else None,
            "subject": email.subject if email else None,
            "original_body": email.body if email else None,
            "reply": reply.reply_body,
            "confidence": reply.confidence,
            "reason": reply.reason,
            "status": reply.status,
            "generated_at": reply.generated_at,
        })

    return {
        "count": len(results),
        "replies": results,
    }


@router.patch("/reply/{user_id}/{reply_id}")
def update_reply_draft(
    user_id: int,
    reply_id: int,
    payload: GmailReplyRequest,
    db: Session = Depends(get_db),
):
    reply = db.scalar(
        select(EmailReply).where(
            EmailReply.id == reply_id,
            EmailReply.user_id == user_id,
        )
    )

    if not reply:
        raise HTTPException(
            status_code=404,
            detail="Reply draft not found.",
        )

    if reply.status != "pending_approval":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Reply cannot be edited because its "
                f"current status is '{reply.status}'."
            ),
        )

    body = payload.body.strip()

    if not body:
        raise HTTPException(
            status_code=400,
            detail="Reply body cannot be empty.",
        )

    reply.reply_body = body
    db.commit()
    db.refresh(reply)

    return {
        "status": "updated",
        "reply_id": reply.id,
        "email_id": reply.email_id,
        "reply": reply.reply_body,
        "confidence": reply.confidence,
    }


@router.post("/reply/approve/{user_id}/{reply_id}")
def approve_and_send_reply(
    user_id: int,
    reply_id: int,
    db: Session = Depends(get_db),
):
    reply = db.scalar(
        select(EmailReply).where(
            EmailReply.id == reply_id,
            EmailReply.user_id == user_id,
        )
    )

    if not reply:
        raise HTTPException(
            status_code=404,
            detail="Reply draft not found.",
        )

    if reply.status != "pending_approval":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Reply cannot be approved because its "
                f"current status is '{reply.status}'."
            ),
        )

    email = db.scalar(
        select(Email).where(
            Email.id == reply.email_id,
            Email.user_id == user_id,
        )
    )

    if not email:
        reply.status = "failed"
        reply.error = "Original email no longer exists."
        db.commit()

        raise HTTPException(
            status_code=404,
            detail="Original email not found.",
        )

    if not email.message_id:
        reply.status = "failed"
        reply.error = "Original Gmail message ID is missing."
        db.commit()

        raise HTTPException(
            status_code=409,
            detail="Original Gmail message ID is missing.",
        )

    labels = {
        label.strip().upper()
        for label in (email.gmail_labels or "").split(",")
        if label.strip()
    }

    if {"SENT", "SPAM", "TRASH"} & labels:
        reply.status = "failed"
        reply.error = (
            "Replies cannot be sent for sent, spam, or trash emails."
        )
        db.commit()

        raise HTTPException(
            status_code=409,
            detail=reply.error,
        )

    settings = db.scalar(
        select(Settings).where(
            Settings.user_id == user_id
        )
    )

    if not settings:
        settings = Settings(
            user_id=user_id,
            agent_enabled=True,
            automatic_job_discovery=True,
            minimum_match_score=70,
            automatic_application=False,
            daily_application_limit=10,
            email_monitoring=True,
            auto_reply=False,
            require_approval=True,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    category = (
        email.ai_category or "other"
    ).strip().lower()

    decision = decide_reply(
        settings=settings,
        category=category,
        should_reply=True,
        model_requires_approval=False,
    )

    if not decision.allowed:
        reply.status = "failed"
        reply.error = decision.reason
        db.commit()

        raise HTTPException(
            status_code=409,
            detail=decision.reason,
        )

    try:
        result = send_gmail_reply(
            to=email.sender,
            subject=email.subject or "(No subject)",
            body=reply.reply_body,
            original_message_id=email.message_id,
        )

        reply.status = "sent"
        reply.gmail_message_id = result.get("message_id")
        reply.sent_at = datetime.utcnow()
        reply.error = None

        db.commit()
        db.refresh(reply)

        return {
            "status": "sent",
            "reply_id": reply.id,
            "email_id": email.id,
            "gmail_message_id": reply.gmail_message_id,
            "thread_id": result.get("thread_id"),
            "to": result.get("to"),
            "subject": result.get("subject"),
            "sent_at": reply.sent_at,
        }

    except Exception as error:
        reply.status = "failed"
        reply.error = str(error)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to send approved Gmail reply: {error}",
        ) from error


@router.post("/reply/reject/{user_id}/{reply_id}")
def reject_reply(
    user_id: int,
    reply_id: int,
    db: Session = Depends(get_db),
):
    reply = db.scalar(
        select(EmailReply).where(
            EmailReply.id == reply_id,
            EmailReply.user_id == user_id,
        )
    )

    if not reply:
        raise HTTPException(
            status_code=404,
            detail="Reply draft not found.",
        )

    if reply.status != "pending_approval":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Reply cannot be rejected because its "
                f"current status is '{reply.status}'."
            ),
        )

    reply.status = "rejected"
    db.commit()
    db.refresh(reply)

    return {
        "status": "rejected",
        "reply_id": reply.id,
        "email_id": reply.email_id,
    }


@router.post("/reply/{user_id}/{email_id}")
def send_reply(
    user_id: int,
    email_id: int,
    payload: GmailReplyRequest,
    db: Session = Depends(get_db),
):
    raise HTTPException(
        status_code=410,
        detail=(
            "Direct Gmail replies are disabled. "
            "Generate a reply and approve it through "
            "the pending-reply workflow."
        ),
    )


@router.post("/sync/{user_id}")
def sync_gmail_messages(
    user_id: int,
    db: Session = Depends(get_db),
):
    try:
        return sync_gmail(
            db=db,
            user_id=user_id,
            max_messages=50,
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=401,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to sync Gmail: {error}",
        ) from error

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.email import Email


router = APIRouter(
    prefix="/api/emails",
    tags=["Emails"],
)


def email_response(email: Email) -> dict:
    return {
        "id": email.id,
        "user_id": email.user_id,
        "message_id": email.message_id,
        "sender": email.sender,
        "recipient": email.recipient,
        "subject": email.subject,
        "body": email.body,
        "received_at": email.received_at,
        "is_read": email.is_read,
        "is_starred": email.is_starred,
        "gmail_labels": email.gmail_labels,
        "ai_category": email.ai_category,
        "ai_summary": email.ai_summary,
        "application_id": email.application_id,
        "created_at": email.created_at,
    }


@router.get("/{user_id}")
def get_emails(
    user_id: int,
    db: Session = Depends(get_db),
):
    emails = db.scalars(
        select(Email)
        .where(Email.user_id == user_id)
        .order_by(
            Email.received_at.desc(),
            Email.created_at.desc(),
        )
    ).all()

    return {
        "count": len(emails),
        "emails": [
            email_response(email)
            for email in emails
        ],
    }


@router.get("/{user_id}/{email_id}")
def get_email(
    user_id: int,
    email_id: int,
    db: Session = Depends(get_db),
):
    email = db.scalar(
        select(Email).where(
            Email.id == email_id,
            Email.user_id == user_id,
        )
    )

    if not email:
        raise HTTPException(
            status_code=404,
            detail="Email not found.",
        )

    return email_response(email)

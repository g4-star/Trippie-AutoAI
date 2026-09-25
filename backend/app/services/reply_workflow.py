from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.email import Email
from app.models.email_reply import EmailReply
from app.models.settings import Settings
from app.services.reply_agent import generate_reply
from app.services.gmail_service import send_gmail_reply
from app.services.reply_decision import decide_reply
from app.services.email_agent import (
    classify_by_gmail_labels,
    classify_email,
    detect_job_alert,
)


def _get_or_create_settings(
    *,
    user_id: int,
    db: Session,
) -> Settings:
    settings = db.scalar(
        select(Settings).where(
            Settings.user_id == user_id
        )
    )

    if settings:
        return settings

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

    return settings


def _existing_pending_reply(
    *,
    email_id: int,
    db: Session,
) -> EmailReply | None:
    return db.scalar(
        select(EmailReply)
        .where(
            EmailReply.email_id == email_id,
            EmailReply.status.in_(
                [
                    "generated",
                    "pending_approval",
                ]
            ),
        )
        .order_by(
            EmailReply.generated_at.desc()
        )
    )


def generate_pending_reply(
    *,
    user_id: int,
    email_id: int,
    db: Session,
) -> dict[str, Any]:
    """
    Generate an AI reply for one stored Gmail email.

    This function never sends email.

    It creates a pending EmailReply record when the email
    is eligible for a reply.
    """

    email = db.scalar(
        select(Email).where(
            Email.id == email_id,
            Email.user_id == user_id,
        )
    )

    if not email:
        raise ValueError("Email not found.")

    settings = _get_or_create_settings(
        user_id=user_id,
        db=db,
    )

    category = (
        email.ai_category
        or ""
    ).strip().lower()

    classifier_should_reply = (
        email.ai_should_reply
        if email.ai_should_reply is not None
        else False
    )

    classifier_requires_approval = (
        email.ai_requires_approval
        if email.ai_requires_approval is not None
        else True
    )

    # Never treat an unclassified email as a normal email.
    # Classify it first. If classification fails, stop safely.
    if not category:
        labels = (
            email.gmail_labels or ""
        ).split(",")

        fast_category = classify_by_gmail_labels(
            gmail_labels=email.gmail_labels or "",
            sender=email.sender,
            subject=email.subject or "",
        )

        if fast_category:
            category = str(
                fast_category.get("category", "")
            ).strip().lower()

            email.ai_category = category
            email.ai_summary = fast_category.get(
                "summary"
            )
            classifier_should_reply = bool(
                fast_category.get(
                    "should_reply",
                    False,
                )
            )
            classifier_requires_approval = bool(
                fast_category.get(
                    "requires_approval",
                    True,
                )
            )
            email.ai_should_reply = (
                classifier_should_reply
            )
            email.ai_requires_approval = (
                classifier_requires_approval
            )
        else:
            job_category = detect_job_alert(
                sender=email.sender,
                subject=email.subject or "",
            )

            if job_category:
                category = str(
                    job_category.get("category", "")
                ).strip().lower()

                email.ai_category = category
                email.ai_summary = job_category.get(
                    "summary"
                )
                classifier_should_reply = bool(
                    job_category.get(
                        "should_reply",
                        False,
                    )
                )
                classifier_requires_approval = bool(
                    job_category.get(
                        "requires_approval",
                        True,
                    )
                )
                email.ai_should_reply = (
                    classifier_should_reply
                )
                email.ai_requires_approval = (
                    classifier_requires_approval
                )
            else:
                classification = classify_email(
                    sender=email.sender,
                    subject=email.subject or "",
                    body=email.body or "",
                )

                category = str(
                    classification.get("category", "")
                ).strip().lower()

                if not category:
                    return {
                        "status": "skipped",
                        "email_id": email.id,
                        "category": "unclassified",
                        "requires_approval": True,
                        "reason": (
                            "Email classification did not "
                            "produce a category."
                        ),
                    }

                email.ai_category = category
                email.ai_summary = classification.get(
                    "summary"
                )

                classifier_should_reply = bool(
                    classification.get(
                        "should_reply",
                        False,
                    )
                )

                classifier_requires_approval = bool(
                    classification.get(
                        "requires_approval",
                        True,
                    )
                )

                email.ai_should_reply = (
                    classifier_should_reply
                )

                email.ai_requires_approval = (
                    classifier_requires_approval
                )

        db.commit()
        db.refresh(email)

    # The classifier decides whether the email actually needs
    # a reply. Deterministic protections remain enforced by
    # decide_reply().
    if email.ai_category:
        # Existing stored classifications do not contain the
        # original model decision, so protected categories must
        # remain non-replyable until reclassified.
        if category in {
            "security_alert",
            "newsletter",
            "promotion",
            "spam",
            "trash",
        }:
            classifier_should_reply = False
            classifier_requires_approval = True
        elif category == "job_opportunity":
            classifier_should_reply = False
            classifier_requires_approval = True

    decision = decide_reply(
        settings=settings,
        category=category,
        should_reply=classifier_should_reply,
        model_requires_approval=classifier_requires_approval,
    )

    if not decision.allowed:
        return {
            "status": "skipped",
            "email_id": email.id,
            "category": category,
            "requires_approval": decision.requires_approval,
            "reason": decision.reason,
        }

    existing = _existing_pending_reply(
        email_id=email.id,
        db=db,
    )

    if existing:
        return {
            "status": "already_pending",
            "reply_id": existing.id,
            "email_id": email.id,
            "category": category,
            "reply": existing.reply_body,
            "confidence": existing.confidence,
            "reason": existing.reason,
            "decision_reason": decision.reason,
            "classifier_requires_approval": classifier_requires_approval,
            "requires_approval": decision.requires_approval,
        }

    # Never send another automatic reply to an email that has
    # already been successfully sent.
    existing_sent = db.scalar(
        select(EmailReply)
        .where(
            EmailReply.email_id == email.id,
            EmailReply.status == "sent",
        )
        .order_by(
            EmailReply.sent_at.desc()
        )
    )

    if existing_sent:
        return {
            "status": "already_sent",
            "reply_id": existing_sent.id,
            "email_id": email.id,
            "category": category,
            "reply": existing_sent.reply_body,
            "confidence": existing_sent.confidence,
            "reason": existing_sent.reason,
        }

    result = generate_reply(
        sender=email.sender,
        subject=email.subject or "",
        body=email.body or "",
    )

    reply = EmailReply(
        user_id=user_id,
        email_id=email.id,
        reply_body=result["reply"],
        status="pending_approval",
        confidence=result["confidence"],
        reason=result["reason"],
    )

    db.add(reply)
    db.commit()
    db.refresh(reply)

    # Important categories remain pending approval even when
    # automatic replies are enabled. Only the deterministic
    # reply decision may authorize automatic sending.
    if not decision.requires_approval:
        if not email.message_id:
            reply.status = "failed"
            reply.error = (
                "Original Gmail message ID is missing."
            )
            db.commit()
            db.refresh(reply)

            return {
                "status": "failed",
                "reply_id": reply.id,
                "email_id": email.id,
                "category": category,
                "reply": reply.reply_body,
                "confidence": reply.confidence,
                "reason": reply.reason,
                "decision_reason": decision.reason,
            }

        labels = {
            label.strip().upper()
            for label in (
                email.gmail_labels or ""
            ).split(",")
            if label.strip()
        }

        if {"SENT", "SPAM", "TRASH"} & labels:
            reply.status = "failed"
            reply.error = (
                "Replies cannot be automatically sent for "
                "sent, spam, or trash emails."
            )
            db.commit()
            db.refresh(reply)

            return {
                "status": "failed",
                "reply_id": reply.id,
                "email_id": email.id,
                "category": category,
                "reply": reply.reply_body,
                "confidence": reply.confidence,
                "reason": reply.reason,
                "decision_reason": decision.reason,
            }

        try:
            send_result = send_gmail_reply(
                to=email.sender,
                subject=email.subject or "(No subject)",
                body=reply.reply_body,
                original_message_id=email.message_id,
            )

            reply.status = "sent"
            reply.gmail_message_id = (
                send_result.get("message_id")
            )
            reply.sent_at = datetime.utcnow()
            reply.error = None

            db.commit()
            db.refresh(reply)

            return {
                "status": "sent",
                "reply_id": reply.id,
                "email_id": email.id,
                "category": category,
                "reply": reply.reply_body,
                "confidence": reply.confidence,
                "reason": reply.reason,
                "decision_reason": decision.reason,
                "gmail_message_id": reply.gmail_message_id,
            }

        except Exception as error:
            reply.status = "failed"
            reply.error = str(error)

            db.commit()
            db.refresh(reply)

            return {
                "status": "failed",
                "reply_id": reply.id,
                "email_id": email.id,
                "category": category,
                "reply": reply.reply_body,
                "confidence": reply.confidence,
                "reason": reply.reason,
                "decision_reason": decision.reason,
                "error": str(error),
            }

    return {
        "status": "pending_approval",
        "reply_id": reply.id,
        "email_id": email.id,
        "category": category,
        "reply": reply.reply_body,
        "confidence": reply.confidence,
        "reason": reply.reason,
        "decision_reason": decision.reason,
        "classifier_requires_approval": classifier_requires_approval,
        "requires_approval": decision.requires_approval,
    }

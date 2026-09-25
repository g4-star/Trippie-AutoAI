from __future__ import annotations

from typing import Any

from app.services.ollama_service import generate_json


ALLOWED_CATEGORIES = {
    "personal",
    "work",
    "client",
    "recruiter",
    "interview",
    "assessment",
    "offer",
    "application_update",
    "rejection",
    "follow_up",
    "job_opportunity",
    "security_alert",
    "newsletter",
    "promotion",
    "notification",
    "support",
    "other",
}

PROTECTED_CATEGORIES = {
    "security_alert",
    "newsletter",
    "promotion",
}

APPROVAL_CATEGORIES = {
    "interview",
    "assessment",
    "offer",
    "rejection",
}


def _clean_body(body: str) -> str:
    """Remove invisible formatting and limit model input size."""

    cleaned = (
        body
        .replace("\u200b", " ")
        .replace("\u200c", " ")
        .replace("\u200d", " ")
        .replace("\ufeff", " ")
    )

    cleaned = " ".join(cleaned.split())

    return cleaned[:3000]


def classify_email(
    *,
    sender: str,
    subject: str,
    body: str,
) -> dict[str, Any]:
    """
    Understand any legitimate email in the user's inbox.

    Job-related classification is an additional signal and does
    not prevent the agent from handling ordinary emails.
    """

    cleaned_body = _clean_body(body)

    system_prompt = """
You are the email intelligence agent for a personal AI assistant.

Your job is to understand ANY legitimate incoming email, not only job emails.

Classify the email into exactly one category:

personal
work
client
recruiter
interview
assessment
offer
application_update
rejection
follow_up
job_opportunity
security_alert
newsletter
promotion
notification
support
other

Important rules:

1. Never invent facts.
2. Determine whether the email is job-related based only on evidence.
3. A normal personal, work, client, recruiter, or support email may require a reply.
4. Decide whether the sender appears to expect a response.
5. Do not reply to newsletters, promotions, spam-like messages, or security alerts.
6. Job-alert emails usually do not need a reply simply because they contain jobs.
7. Interview, assessment, offer, and rejection messages are important and require user approval.
8. If the email is ambiguous, require approval.
9. Never claim the user has qualifications, experience, relationships, or information that are not present.
10. Return JSON only.

Return exactly:

{
  "category": "one allowed category",
  "summary": "short factual summary",
  "is_job_related": false,
  "should_reply": false,
  "requires_approval": true,
  "reason": "short factual explanation"
}
"""

    user_prompt = f"""
Email sender:
{sender}

Email subject:
{subject}

Email body:
{cleaned_body}
"""

    result = generate_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    category = str(
        result.get("category", "other")
    ).strip().lower()

    if category not in ALLOWED_CATEGORIES:
        category = "other"

    summary = str(
        result.get("summary", "")
    ).strip()

    is_job_related = bool(
        result.get("is_job_related", False)
    )

    model_should_reply = bool(
        result.get("should_reply", False)
    )

    model_requires_approval = bool(
        result.get("requires_approval", True)
    )

    reason = str(
        result.get("reason", "")
    ).strip()

    # Application-level safety rules.
    #
    # The model can recommend an action, but it cannot override
    # deterministic protections enforced by the application.

    if category in PROTECTED_CATEGORIES:
        should_reply = False
        requires_approval = True

        reason = (
            f"{category.replace('_', ' ').title()} emails "
            "are not eligible for automatic replies."
        )

    elif category in APPROVAL_CATEGORIES:
        should_reply = model_should_reply
        requires_approval = True

        reason = (
            f"{category.replace('_', ' ').title()} emails "
            "always require user approval before replying."
        )

    elif category == "job_opportunity":
        # A job opportunity can still be processed by the general
        # email agent. This only controls the likely reply behavior
        # for the job-alert message itself.
        should_reply = model_should_reply
        requires_approval = True

        reason = (
            "Job-related email detected. Any reply requires "
            "user approval."
        )

    elif category in {
        "personal",
        "work",
        "client",
        "recruiter",
        "follow_up",
        "support",
        "notification",
        "other",
    }:
        should_reply = model_should_reply
        requires_approval = model_requires_approval

        if not should_reply:
            reason = (
                reason
                or "The email does not appear to require a reply."
            )

    else:
        should_reply = False
        requires_approval = True

        reason = (
            "Email classification is ambiguous and requires "
            "user approval."
        )

    return {
        "category": category,
        "summary": summary,
        "is_job_related": is_job_related,
        "requires_approval": requires_approval,
        "should_reply": should_reply,
        "reason": reason,
    }


def classify_by_gmail_labels(
    *,
    gmail_labels: str,
    sender: str,
    subject: str,
) -> dict[str, Any] | None:
    """
    Classify obvious Gmail categories without using Ollama.

    This is an optimization and safety layer. Returning None means
    the email should continue to the AI classifier.
    """

    labels = {
        label.strip().upper()
        for label in gmail_labels.split(",")
        if label.strip()
    }

    sender_lower = sender.lower()
    subject_lower = subject.lower()

    if "SPAM" in labels:
        return {
            "category": "spam",
            "summary": "Email is marked as spam by Gmail.",
            "is_job_related": False,
            "requires_approval": True,
            "should_reply": False,
            "reason": (
                "Spam emails are never eligible for "
                "automatic replies."
            ),
        }

    if "TRASH" in labels:
        return {
            "category": "trash",
            "summary": "Email is in the Gmail trash.",
            "is_job_related": False,
            "requires_approval": True,
            "should_reply": False,
            "reason": (
                "Trash emails are never eligible for "
                "automatic replies."
            ),
        }

    if "CATEGORY_PROMOTIONS" in labels:
        return {
            "category": "promotion",
            "summary": "Gmail classified this email as a promotion.",
            "is_job_related": False,
            "requires_approval": True,
            "should_reply": False,
            "reason": (
                "Promotional emails are never eligible for "
                "automatic replies."
            ),
        }

    if "CATEGORY_SOCIAL" in labels:
        return {
            "category": "personal",
            "summary": "Gmail classified this email as social.",
            "is_job_related": False,
            "requires_approval": True,
            "should_reply": False,
            "reason": (
                "Social emails are not automatically replied to "
                "without AI analysis and user approval."
            ),
        }

    security_terms = (
        "security alert",
        "suspicious sign-in",
        "new sign-in",
        "password changed",
        "password reset",
        "verify your account",
        "security notification",
    )

    if any(
        term in subject_lower
        for term in security_terms
    ):
        return {
            "category": "security_alert",
            "summary": (
                "Email appears to be a security notification."
            ),
            "is_job_related": False,
            "requires_approval": True,
            "should_reply": False,
            "reason": (
                "Security emails are never eligible for "
                "automatic replies."
            ),
        }

    return None


def detect_job_alert(
    *,
    sender: str,
    subject: str,
) -> dict[str, Any] | None:
    """
    Detect common job-alert emails without using the AI model.

    This is an additional signal. It does not replace general
    email classification.
    """

    sender_lower = sender.lower()
    subject_lower = subject.lower()

    job_alert_senders = (
        "linkedin.com",
        "indeed.com",
        "brightermonday.co.ke",
        "jobgether.com",
        "glassdoor.com",
        "ziprecruiter.com",
    )

    job_alert_phrases = (
        "job alert",
        "jobs match",
        "new jobs",
        "jobs for you",
        "job recommendations",
        "new job",
        "job opportunity",
    )

    sender_is_job_source = any(
        domain in sender_lower
        for domain in job_alert_senders
    )

    subject_is_job_alert = any(
        phrase in subject_lower
        for phrase in job_alert_phrases
    )

    if not sender_is_job_source and not subject_is_job_alert:
        return None

    return {
        "category": "job_opportunity",
        "summary": (
            "Job opportunity or job-alert email detected."
        ),
        "is_job_related": True,
        "requires_approval": True,
        "should_reply": False,
        "reason": (
            "Job-alert email detected. The alert itself does not "
            "automatically receive a reply."
        ),
    }

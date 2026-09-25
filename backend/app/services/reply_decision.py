from __future__ import annotations

from dataclasses import dataclass

from app.models.settings import Settings


# These categories must never be automatically sent.
NEVER_AUTO_REPLY = {
    "security_alert",
    "newsletter",
    "promotion",
    "spam",
    "trash",
    "job_opportunity",
}


# These categories always require the user's approval.
ALWAYS_REQUIRE_APPROVAL = {
    "interview",
    "assessment",
    "offer",
    "rejection",
}


@dataclass
class ReplyDecision:
    allowed: bool
    requires_approval: bool
    reason: str


def decide_reply(
    *,
    settings: Settings,
    category: str,
    should_reply: bool = True,
    model_requires_approval: bool = False,
) -> ReplyDecision:
    """
    Decide whether TrippieAutoAI may generate/send a reply.

    This is intentionally deterministic. The AI model does not
    get to override these safety and account settings.
    """

    normalized_category = (
        category or "other"
    ).strip().lower()

    # Global agent switch.
    if not settings.agent_enabled:
        return ReplyDecision(
            allowed=False,
            requires_approval=True,
            reason="AI agent is disabled.",
        )

    # Email monitoring switch.
    if not settings.email_monitoring:
        return ReplyDecision(
            allowed=False,
            requires_approval=True,
            reason="Email monitoring is disabled.",
        )

    # The classifier says no reply is appropriate.
    if not should_reply:
        return ReplyDecision(
            allowed=False,
            requires_approval=False,
            reason="The email was classified as not requiring a reply.",
        )

    # Protected categories can never be auto-sent.
    if normalized_category in NEVER_AUTO_REPLY:
        return ReplyDecision(
            allowed=False,
            requires_approval=True,
            reason=(
                f"Automatic replies are disabled for "
                f"'{normalized_category}' emails."
            ),
        )

    # Important categories always require approval.
    if normalized_category in ALWAYS_REQUIRE_APPROVAL:
        return ReplyDecision(
            allowed=True,
            requires_approval=True,
            reason=(
                f"'{normalized_category}' emails always require "
                "user approval before sending."
            ),
        )

    # The model can request approval, but never remove a
    # deterministic approval requirement.
    if model_requires_approval:
        return ReplyDecision(
            allowed=True,
            requires_approval=True,
            reason="The AI classifier requested user approval.",
        )

    # Automatic sending is a separate explicit setting.
    if not settings.auto_reply:
        return ReplyDecision(
            allowed=True,
            requires_approval=True,
            reason=(
                "Automatic replies are disabled. "
                "The reply can be prepared for approval."
            ),
        )

    # Account-level approval setting.
    if settings.require_approval:
        return ReplyDecision(
            allowed=True,
            requires_approval=True,
            reason=(
                "Account settings require approval before "
                "sending replies."
            ),
        )

    # Only now may the caller automatically send.
    return ReplyDecision(
        allowed=True,
        requires_approval=False,
        reason="Reply is permitted by the current settings.",
    )

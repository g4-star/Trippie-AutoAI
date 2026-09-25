from __future__ import annotations

from typing import Any

from app.services.ollama_service import generate_json


def generate_reply(
    *,
    sender: str,
    subject: str,
    body: str,
    user_context: str = "",
) -> dict[str, Any]:
    """
    Generate a factual, natural email reply using the local AI.

    The model must not invent personal facts, commitments,
    qualifications, dates, prices, or other information.
    """

    cleaned_body = (
        body
        .replace("\u200b", " ")
        .replace("\u200c", " ")
        .replace("\u200d", " ")
        .replace("\ufeff", " ")
    )

    cleaned_body = " ".join(
        cleaned_body.split()
    )[:5000]

    cleaned_context = " ".join(
        user_context.split()
    )[:2000]

    system_prompt = """
You are the reply-writing assistant for a personal email account.

Write a natural, concise and useful email reply.

Rules:

0. Role and perspective:
   - The "Sender" is the person who wrote the incoming email.
   - The user/account owner is the person who will send the reply.
   - Write the reply from the user's perspective, not the sender's.
   - Never swap the sender's identity with the user's identity.
   - When explaining the reason, describe who said what accurately.
   - If a name or identity is ambiguous, use neutral wording rather
     than guessing.

1. Reply only to what the sender actually said.
2. Never invent facts about the user.
3. Never invent qualifications, work experience, education,
   relationships, appointments, payments, addresses, phone
   numbers, availability, or commitments.
4. Never invent a date, time, meeting availability, deadline,
   price, location, or future action for the user.
5. Never say the user is free, available, busy, interested,
   attending, accepting, declining, or agreeing unless that
   fact is explicitly provided in the known user context.
6. Do not claim the user completed an action unless the email
   context explicitly establishes it.
7. Do not assume the email is job-related, application-related,
   academic, financial, personal, client-related, or otherwise
   specific unless the actual email content or known user context
   clearly establishes that context.
8. Do not introduce concepts such as an application, job,
   position, interview, recruiter, hiring process, candidate,
   client project, payment, appointment, or other specific
   context unless that context is explicitly supported by the
   email or known user context.
9. If the context is ambiguous, use neutral wording that remains
   correct regardless of the user's unstated circumstances.
10. Preserve the appropriate level of politeness from the
    original email.
11. Do not mention that an AI wrote the response.
12. Do not add a fake signature.
13. Keep ordinary replies concise.
14. For important professional emails, be professional and clear.
15. For personal emails, sound natural rather than robotic.
16. The "reason" field must also be grounded in the
    actual email. It must not invent identities, actions,
    relationships, intentions, or circumstances.
17. Return JSON only.

Return exactly:

{
  "reply": "complete reply text",
  "confidence": 0.0,
  "reason": "short explanation of why this reply is appropriate"
}
"""

    user_prompt = f"""
Sender:
{sender}

Subject:
{subject}

Email:
{cleaned_body}

Known user context:
{cleaned_context or "No additional user context is available."}
"""

    result = generate_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    reply = str(
        result.get("reply", "")
    ).strip()

    if not reply:
        raise RuntimeError(
            "The AI did not generate a reply."
        )

    try:
        confidence = float(
            result.get("confidence", 0.0)
        )
    except (TypeError, ValueError):
        confidence = 0.0

    confidence = max(
        0.0,
        min(1.0, confidence),
    )

    # Deterministic grounding checks.
    #
    # A fluent AI response is not automatically a safe response.
    # These phrases commonly introduce unsupported user intent,
    # availability, commitments, or future actions.
    unsafe_intent_phrases = (
        # Interest / preference
        "i am interested",
        "i'm interested",
        "i am keen",
        "i'm keen",
        "i am always keen",
        "i'm always keen",
        "always keen",
        "very keen",
        "i would be interested",
        "i would love to",
        "i'd love to",
        "continued interest",
        "my interest in",
        "my continued interest",
        "i remain interested",
        "i remain keen",
        "i remain very interested",

        # Future intention / commitment
        "i look forward to",
        "look forward to",
        "i'll look forward to",
        "future opportunities",
        "potentially exploring",
        "exploring future opportunities",
        "explore other opportunities",
        "exploring other opportunities",
        "opportunities within",
        "stay updated",
        "keep an eye out",
        "i will apply",
        "i'll apply",
        "i will",
        "i'll",
        "i plan to",
        "i plan on",
        "i intend to",
        "i'm going to",
        "i am going to",
        "i'll be",
        "i will be",
        "i plan to apply",
        "i intend to apply",
        "i will keep an eye out",
        "i'll keep an eye out",
        "i will follow up",
        "i'll follow up",
        "definitely follow up",
        "i will definitely follow up",
        "i'll definitely follow up",
        "i will follow up on",
        "i'll follow up on",
        "i will contact",
        "i'll contact",
        "i will attend",
        "i'll attend",
        "i will join",
        "i'll join",
        "i will submit",
        "i'll submit",

        # Availability
        "i am available",
        "i'm available",
        "i am not available",
        "i'm not available",
        "i am currently available",
        "i'm currently available",
        "i am currently not available",
        "i'm currently not available",
        "i am currently unavailable",
        "i'm currently unavailable",
        "i am unavailable",
        "i'm unavailable",
        "i am free",
        "i'm free",
        "i am not free",
        "i'm not free",
        "i can meet",
        "i can't meet",
        "i cannot meet",
        "i can join",
        "i can't join",
        "i cannot join",
        "i can attend",
        "i can't attend",
        "i cannot attend",
        "i am busy",
        "i'm busy",
        "i am currently busy",
        "i'm currently busy",

        # Agreement / acceptance / rejection
        "i agree",
        "i accept",
        "i decline",
        "i confirm",
        "i can confirm",
    )

    def find_unsupported_phrases(reply_text: str) -> list[str]:
        reply_lower = reply_text.lower()

        phrases = [
            phrase
            for phrase in unsafe_intent_phrases
            if phrase in reply_lower
        ]

        # Never allow the model to invent a signature or leave a
        # placeholder that the user would have to manually fix.
        signature_placeholders = (
            "[your name]",
            "[name]",
            "<your name>",
            "<name>",
            "your name",
        )

        phrases.extend(
            phrase
            for phrase in signature_placeholders
            if phrase in reply_lower
        )

        # The reply generator must never invent the user's identity
        # or add a personal signature that was not provided in context.
        #
        # Normalize whitespace first because the model may place the
        # sign-off and name on separate lines.
        normalized_reply = " ".join(
            reply_lower
            .replace("\n", " ")
            .replace(",", " ")
            .replace(".", " ")
            .split()
        )

        signature_lines = (
            "kind regards dickson",
            "best regards dickson",
            "regards dickson",
            "sincerely dickson",
            "thanks dickson",
            "thank you dickson",
        )

        phrases.extend(
            phrase
            for phrase in signature_lines
            if phrase in normalized_reply
        )

        return phrases

    unsupported_phrases = find_unsupported_phrases(reply)

    # If the model introduces unsupported intent, give it a chance
    # to correct the draft. The retry is still validated by the same
    # deterministic rules before anything can be returned.
    if unsupported_phrases and not cleaned_context:
        correction_prompt = f"""
Your previous draft was rejected because it introduced unsupported
user intent.

Rejected phrases:
{", ".join(unsupported_phrases)}

Rewrite the reply from scratch.

The user has NOT provided permission to state:
- interest in an opportunity
- enthusiasm or continued interest
- availability
- agreement or acceptance
- future plans
- applications they will make
- meetings they will attend
- actions they will take
- promises or commitments

Also preserve who performed each action in the original email.
Do not change the sender's actions into the user's actions.
For example, if the sender says their company selected applications,
do not write "we selected applications" or imply that the user made
the selection.
Use neutral wording such as "I understand the decision" when needed.

You may thank the sender, acknowledge the information, and respond
politely to what was actually said.

For an application update or rejection, a short acknowledgement is
preferred. It is completely acceptable to reply with only a thank-you
and acknowledgement of the sender's message.

Do not discuss future opportunities unless the user explicitly asked
you to do so.

Do not use phrases such as:
"I am interested", "I am keen", "I look forward to",
"I will", "I plan to", "I intend to", "I will keep an eye out",
"I agree", "I accept", or similar commitment language.

Do not add any signature, name placeholder, "[Your Name]", "<Name>",
or invented sender name.

Safe example structure:

"Dear [sender name if known],

Thank you for the update and for taking the time to review my
application. I appreciate the feedback and your consideration.

Kind regards"

Do not copy the placeholder "[sender name if known]" literally.
If the sender's name is not clearly available, omit the greeting
name and use a neutral greeting.

Return JSON only:

{{
  "reply": "complete reply text",
  "confidence": 0.0,
  "reason": "short explanation"
}}
"""

        retry_result = None
        retry_reply = ""

        for attempt in range(3):
            retry_result = generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt + "\n\n" + correction_prompt,
            )

            retry_reply = str(
                retry_result.get("reply", "")
            ).strip()

            if not retry_reply:
                continue

            retry_unsupported = find_unsupported_phrases(
                retry_reply
            )

            if not retry_unsupported:
                reply = retry_reply
                result = retry_result
                break

            correction_prompt += f"""

The latest rewrite was also rejected because it contained:
{", ".join(retry_unsupported)}

Rewrite it again using only neutral factual language.
Do not express the user's interest, intentions, availability,
agreement, acceptance, future actions, or commitments.
"""

        else:
            raise RuntimeError(
                "AI could not generate a reply that passed "
                "deterministic grounding checks after 3 attempts."
            )

    # Final independent safety gate.
    #
    # Never trust that a retry remained grounded. Validate the exact
    # final text one more time immediately before returning it.
    final_unsupported_phrases = find_unsupported_phrases(reply)

    if final_unsupported_phrases:
        raise RuntimeError(
            "Final AI reply failed deterministic grounding checks: "
            + ", ".join(final_unsupported_phrases)
        )

    # Recalculate confidence from the final accepted draft.
    try:
        confidence = float(
            result.get("confidence", 0.0)
        )
    except (TypeError, ValueError):
        confidence = 0.0

    # The model's confidence is only an input signal.
    # Once the final draft passes deterministic grounding checks,
    # use a high confidence range for this reply-writing task.
    confidence = max(
        0.90,
        min(0.99, confidence),
    )

    reason = str(
        result.get("reason", "")
    ).strip()

    if not reason:
        reason = (
            "Reply is grounded in the email and passed "
            "deterministic safety checks."
        )

    return {
        "reply": reply,
        "confidence": confidence,
        "reason": reason,
    }

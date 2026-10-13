# Automatic job-application Gmail drafts and SMS alerts

Trippie AutoAI discovers jobs, matches them to the configured profile, creates Gmail **drafts only**, and sends an SMS notification with a direct Gmail draft link when SMS is configured.

## Runtime

Deploy the backend as a persistent service using the repository-root `render.yaml` blueprint (or another always-on Python host). A Vercel serverless function cannot reliably keep a background thread alive. The worker checks the existing `agent_enabled` setting and runs every 15 minutes by default.

## Required setup

1. Configure `DATABASE_URL` and a stable, strong `SECRET_KEY`.
2. In Google Cloud, configure an OAuth web client and add `https://YOUR-BACKEND-HOST/api/job-drafts/gmail/callback` as an authorized redirect URI.
3. Set `GMAIL_CLIENT_CONFIG_JSON` to the complete Google OAuth client JSON. Treat it as a secret; do not commit it.
4. Deploy the backend and open `https://YOUR-BACKEND-HOST/api/job-drafts/gmail/connect`. Authorize the Gmail account that should hold the drafts. This is separate from the Gmail connection in ChatGPT.
5. Configure ClickSend on the backend with `CLICKSEND_USERNAME`, `CLICKSEND_API_KEY`, and `AUTOAI_NOTIFY_PHONE` in E.164 international format (for Kenya, e.g. `+2547XXXXXXXX`). These are hosting environment secrets/settings, not values to commit to GitHub.
6. Enable the agent and automatic job discovery in Trippie AutoAI. Ensure `AUTOAI_USER_ID` identifies your profile.

## Behavior

- Matches jobs using the existing configured score threshold (70 by default).
- Creates one Gmail draft per eligible job only when a contact email is explicitly present in the job listing.
- Email is multipart plain text + HTML. Portfolio, GitHub, and LinkedIn are clickable links in the HTML version.
- After the draft is saved, sends an SMS with the role, employer, match score, and direct Gmail draft URL.
- SMS failure does not delete the draft; notification errors are tracked and retried on a later worker cycle.
- Deduplicates drafts and caps successful drafts per day.
- No application email is sent by the backend. Open the notification link, inspect the recipient and draft, then tap Send yourself in Gmail. No CV attachment or external application form is submitted automatically.

## OAuth scope

Only `https://www.googleapis.com/auth/gmail.compose` is requested. No Gmail send scope is needed because sending remains a manual action in Gmail.

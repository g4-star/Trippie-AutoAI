# Automatic job-application Gmail drafts

Trippie AutoAI discovers jobs, matches them to the configured profile, and creates Gmail **drafts only**. This feature never calls Gmail's message-send API. The existing separate email-reply workflow is unchanged.

## Runtime

The Vercel Python function deployment is serverless and cannot reliably keep a background thread alive. Deploy the backend as a persistent service using the repository-root `render.yaml` blueprint (or another always-on Python host). The blueprint runs the FastAPI backend and enables the worker. Keep the mobile/web frontend pointed at the backend's public URL.

The worker checks the existing `agent_enabled` setting and runs every 15 minutes by default. It uses the existing match threshold (70 by default) and daily application limit (10 by default), overridable through host environment settings.

## Required setup

1. Configure `DATABASE_URL` and a strong, stable `SECRET_KEY`. Do not rotate this secret after Gmail is connected unless you plan to reconnect.
2. In Google Cloud, configure an OAuth web client and add the backend callback URL `https://YOUR-BACKEND-HOST/api/job-drafts/gmail/callback` as an authorized redirect URI.
3. Set `GMAIL_CLIENT_CONFIG_JSON` to the complete Google OAuth client JSON. Treat it as a secret; do not commit it.
4. Deploy the backend, then open `https://YOUR-BACKEND-HOST/api/job-drafts/gmail/connect` and authorize the Gmail account that should hold the drafts. This is a separate authorization for the deployed backend; connecting Gmail to ChatGPT does not authorize the server.
5. In Trippie AutoAI, enable the agent and automatic job discovery. Ensure the profile for `AUTOAI_USER_ID` exists and has accurate skills and preferences.

## What it does

- Searches public job sources already configured in the project and saves listings.
- Matches jobs using the existing skills-first engine and configured threshold.
- Creates one tracked Gmail draft per job only when the posting itself contains a contact email.
- Includes the role, employer, matched skills where available, and portfolio/GitHub/LinkedIn links.
- Stores the Gmail draft ID and URL in an encrypted-token-backed database workflow; list drafts via `GET /api/job-drafts/{user_id}`.
- Skips duplicates, ignores common placeholder/no-reply addresses, and caps successful drafts per day.
- Does not send applications, fill external forms, attach the CV, or invent contact emails. Listings without an email contact are counted as skipped.

## Gmail security

The draft workflow requests the `gmail.compose` OAuth scope and calls Gmail's `drafts.create` endpoint only. OAuth credentials are encrypted before storage in the database using a key derived from `SECRET_KEY`. A persistent database is required. If Google reports insufficient permissions, reconnect through the endpoint above.

## Notes

- This first implementation uses one configured user ID, matching the current worker architecture.
- An always-on host is needed for the background loop; a sleeping/serverless-only deployment will not continuously run it.
- Review each draft, attach CV/certificates when a vacancy requires them, and send manually.

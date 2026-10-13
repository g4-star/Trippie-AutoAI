# Automatic job-application Gmail drafts

Trippie AutoAI can discover jobs, match them to the configured profile, and create Gmail **drafts only**. This feature never calls Gmail's message-send API. The existing separate email-reply workflow is unchanged.

## Runtime

The Vercel Python function deployment is serverless and cannot reliably keep a background thread alive. Deploy the backend as a persistent service using the repository-root `render.yaml` blueprint (or another always-on Python host). The blueprint runs the FastAPI backend and enables the worker. Keep the mobile/web frontend pointed at the backend's public URL.

The worker checks the agent's existing `agent_enabled` setting and runs every 15 minutes by default. It uses the existing match threshold (70 by default) and daily application limit (10 by default). Change `AGENT_CYCLE_INTERVAL_SECONDS` or `JOB_EMAIL_DRAFT_DAILY_LIMIT` through host environment settings if needed.

## Required setup

1. Configure `DATABASE_URL` and a strong `SECRET_KEY`.
2. In Google Cloud, configure an OAuth web client and add the backend callback URL `https://YOUR-BACKEND-HOST/api/job-drafts/gmail/callback` as an authorized redirect URI.
3. Set `GMAIL_CLIENT_CONFIG_JSON` to the complete Google OAuth client JSON. Treat it as a secret; do not commit it.
4. Keep `GMAIL_DRAFT_TOKEN_PATH` on persistent storage. The included Render blueprint mounts `/var/data` for this purpose.
5. Deploy the backend, then open `https://YOUR-BACKEND-HOST/api/job-drafts/gmail/connect` and authorize the Gmail account that should hold the drafts. This is a separate authorization for the deployed backend; connecting Gmail to ChatGPT does not authorize the server.
6. In Trippie AutoAI, enable the agent and automatic job discovery. Ensure the profile for `AUTOAI_USER_ID` exists and has accurate skills and preferences.

## What it does

- Searches public job sources already configured in the project and saves listings.
- Matches jobs using the existing skills-based matching engine and configured threshold.
- Creates one tracked Gmail draft per job only when a contact email is explicitly present in the listing.
- Includes the job title, employer, matched skills where available, and portfolio/GitHub/LinkedIn links.
- Stores the Gmail draft ID and URL at `GET /api/job-drafts/{user_id}` for dashboard integration.
- Skips duplicate drafts, ignores common placeholder/no-reply addresses, and caps successful drafts per day.
- Does not send applications, fill external forms, attach the CV, or invent contact emails. Listings without an email contact are counted as skipped.

## Notes

- Gmail draft authorization uses the `gmail.compose` OAuth scope. If Google reports insufficient permissions, reconnect through the endpoint above and accept the requested scope.
- This first implementation uses a single configured user ID, matching the current worker architecture.
- Review every draft, attach the CV/certificates when a vacancy requires them, and send manually.

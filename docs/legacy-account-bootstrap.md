# One-time legacy account setup

The mobile client can connect to the existing backend profile (user ID `1`) with a one-time setup code. This flow is disabled unless the backend environment explicitly configures `LEGACY_ACCOUNT_BOOTSTRAP_KEY` to a randomly generated secret of at least 32 characters. Do not commit the secret to Git or place it in the Flutter app.

## Before enabling it

1. Confirm the configured database contains the intended legacy user ID `1` and its existing records. This endpoint never creates or replaces that user.
2. Configure a unique secret in the **preview environment only** first, and verify the preview uses an isolated non-production database. Do not reuse a production database for preview tests.
3. Set `LEGACY_ACCOUNT_BOOTSTRAP_KEY` in the backend deployment environment using the provider's secret/environment-variable UI. Keep the value private and share it only with the intended device owner through a trusted channel.
4. Deploy/test the feature branch preview only after verifying the database target. The first successful redemption is globally single-use for that database; subsequent attempts are rejected.
5. Remove the environment variable after the intended device has redeemed it. The database marker still prevents reuse.

The client saves the returned access and refresh tokens using Flutter Secure Storage. Normal launches restore the session and proceed to the dashboard. If app data is erased or the refresh session is lost, this single-use setup code cannot be reused; a separate authenticated recovery process would be required.

## Safety properties

- No code is enabled by default.
- The code is compared with a constant-time comparison.
- The endpoint only connects to the existing active user ID `1`; it does not create a new account or accept a caller-selected user ID.
- A reserved, revoked marker is written to the existing `refresh_sessions` table in the same transaction as the first refresh session, avoiding a new database table. Concurrent redemption attempts cannot both commit the unique marker.
- This change does not deploy to production or configure the environment variable.

# One workspace on free Render

This release connects BRICS + Geo news, HS-code research, selected-story AI analysis,
live AIS context and shared stream controls. It keeps credentials on the server.

## 1. Render

Deploy this release with one worker using the existing start command. Keep your valid
MongoDB connection string and add/update these variables:

| Key | Value |
|---|---|
| TRIGGER_SECRET | Your existing strong workspace secret |
| ALLOW_INSECURE_LOCAL | false |
| STORAGE_BACKEND | mongodb |
| DEPLOY_MODE | cloud |
| MONGODB_URI | Complete Atlas connection string |
| MONGODB_DB | newsbot |
| MONGODB_DB_NAME | geo_intel |
| RUN_SCHEDULER | false |
| ENABLE_EMAIL | false |
| ENABLE_CRITICAL_ALERTS | false |
| GEO_ENABLE_CRITICAL_ALERTS | false |
| GEO_ENABLE_WEEKLY_REPORT | false |
| GEO_ENABLE_METADATA_CLEANUP | false |
| PUBLIC_URL | Your Render homepage URL |

Leave MongoDB Atlas access configured for Render's outbound addresses. Use separate
BRICS and Geo databases, as above. Enable all three apps (their default).

For AI, add one or more GEMINI_KEYS, GROQ_KEYS, MISTRAL_KEYS, NVIDIA_KEYS. These work in
both the HSN finder and workspace. Optional GEMINI_MODEL, GROQ_MODEL, MISTRAL_MODEL,
NVIDIA_MODEL overrides select a model available to your provider account. Provider
keys being configured does not guarantee quota or model access. No AI key goes in
Apps Script, HTML, or GitHub. AISSTREAM_KEY enables live port positions.

## 2. Sign in once

Open your homepage, enter TRIGGER_SECRET in the Workspace secret field, and click
Open workspace. The server sets an HttpOnly, SameSite=Strict cookie lasting eight
hours; cloud deployment uses a Secure cookie. The secret is not placed in page URLs
or browser storage. Signing out removes the cookie. Do not share this administrator
session. This is a single-owner workspace, not multi-user account management.

The same session opens the Geo dashboard and authorizes BRICS stream add/remove.
A separate BRICS_DASHBOARD_KEY remains available for standalone stream control, but
is not needed after workspace sign-in. Watching streams is public. Stream changes
are persisted in MongoDB's settings collection when STORAGE_BACKEND=mongodb. Local
SQLite mode stores them under DATA_DIR/brics-streams.yaml; configure a persistent
disk for that file on ephemeral hosts. Bundled streams seed defaults until the first
saved edit; editing the bundled YAML after that does not overwrite saved streams.

## 3. Use the integrated features

- Collect both feeds, then refresh. Partial source failures are shown separately.
- Filter by feed, country, text or candidate HS heading. Save up to eight views in
  this browser (saved views are not email alerts and do not sync across devices).
- Follow an HS chip into the existing HSN code page, with duties and related news.
- Select one to six stories and generate a cited AI brief. It distinguishes reported
  facts from possible trade impacts and questions to verify. Download the text brief.
- Load live AIS positions for context. AIS does not prove cargo or a story-vessel link.
- Manage live streams from BRICS without re-entering the master secret.

The workspace reads the latest 150 records per source. AI receives only the selected
saved titles, summaries and candidate HS headings, not a full independent web search.

## 4. Upgrade Google Apps Script

In your existing Apps Script project, replace Code.gs with
[geonews/apps_script/Code.gs](../geonews/apps_script/Code.gs) from this release.
Keep these Script Properties:

- RENDER_BASE_URL: your homepage URL, without /geo or any query string.
- TRIGGER_SECRET: exactly the Render secret, without quotes.
- EMAIL_TO: recipient email address (or comma-separated addresses).

Optional: DIGEST_TIMES=10:00,22:00; TIME_ZONE=Asia/Kolkata;
KEEPALIVE_MINUTES=10 (set 0 to disable pings); COLLECT_MINUTES=30.

Run sendTestEmail, runCollect, then checkCollection a few minutes later. Run sendDigest
when articles exist. Run setupTriggers once to replace the old app schedules. It
removes only this app's current/legacy triggers. Do not run both old and new script
projects with active email triggers. No Web App deployment or Gmail App Password is
needed. Gmail sends as the account that authorizes Apps Script.

This version calls /api/trigger/collect for BOTH feeds, /api/status for progress,
/api/intel/digest for combined HTML, and /api/intel/mark-emailed after Gmail succeeds.
It includes up to 60 unemailed stories per run with candidate HS headings, and retries
pending acknowledgements before sending another digest. Mongo acknowledgement is
idempotent. Exactly-once email delivery is not guaranteed if execution terminates
between Gmail sending and saving the acknowledgement state. Separate SMTP/messaging
jobs can share emailed flags; leave SMTP scheduling disabled for this Gmail workflow.

The Gmail brief does not automatically call AI, produce a separate weekly trend email,
or send WhatsApp/Telegram digests. Telegram article backup can remain enabled if
configured; it runs during Geo collection. The existing events list needs real event
data; this release does not invent events or add event discovery.

## 5. Limits and troubleshooting

Free Render can sleep/restart; Apps Script wake requests cannot guarantee uptime or
bypass plan limits. AIS needs an active process to receive positions and may need time
to warm up. Google trigger times are approximate and Gmail/Apps Script quotas apply.

401: match the secret and redeploy Render. 503 for Geo: inspect Atlas credentials and
network access. No AI providers: add server keys and redeploy. AI failure: inspect
provider quota/model access. No new email: check source status and unemailed articles.
Live integration tests require your own credentials; do not paste them into chat.

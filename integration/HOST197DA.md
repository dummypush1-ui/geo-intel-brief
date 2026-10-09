# 197d-a read-only host probe

Default OFF. Owner-authenticated GET /api/collector-host-probe only when
COLLECTOR_HOST_PROBE_ENABLED=true and dedicated backend
COLLECTOR_HOST_PROBE_SECRET is configured. No browser Origin, no query string,
no user-supplied command/path/env. Owner enables/deploys this diagnostic only;
this does NOT enable collection or establish activation authority.

Closed facts: point-in-time cgroup allowance minus current use bounded by host
MemAvailable; /usr/bin/bwrap presence, actual PID namespace and nested bwrap
fixed /usr/bin/true probes (3 seconds each, kill/reap); kernel release; current
Gunicorn worker config timeout and count only if observable, otherwise null.
No env values, process command lines, tokens, DB facts, raw failures or files
are returned. Fixed closed response schema blocks arbitrary injected outputs.
No persistent writes, clients, indexes, provider, or collector activation.
One-at-a-time process-local probe gate; owner asks for one measurement, not
ongoing polling. Public health/home/read routes remain unchanged.

Probe's memory observation is not reserved capacity or free monthly quota.
A missing/unavailable fact is a blocker, not a successful readiness proof.
The conservative collector contract remains 1536 MiB available memory and
WSGI worker timeout >120s; actual host provider is still a separate 197d unit.
No live host query or deployment happened while preparing this source.

Render documents a 100-minute HTTP response/request ceiling, so the 90-second
collector contract is below that documented proxy ceiling. Actual Gunicorn
worker timeout and requester timeout remain separate checks. The 75-second
edge number in the runtime-errors tutorial describes keep-alive reuse, not
an established maximum response duration. No slow remote test was run.

Sources, read at preparation:
https://render.com/docs/render-vs-heroku-comparison
https://render.com/articles/deploy-streamlit-gradio-localhost-to-live
https://render.com/tutorials/when-deploys-go-wrong/runtime-errors
https://render.com/docs/free
https://render.com/docs/web-services

Free plan documentation states 0.1 CPU/512 MB RAM, single instance and no shell.
Do not assume this exact service's current plan from generic documentation;
probe actual allocation. Do not quietly lower worker/parser caps when too small.

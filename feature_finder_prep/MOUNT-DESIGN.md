# Finder mount decision preparation

Copyright (c) 2026 Push. All rights reserved.

Source-only policy evaluator, not a proxy, provider connector, mounted Finder,
or authorization grant. Existing shell/source/index unchanged. public107 still
serves offline Finder. No requests, keys, environment or runtime changes here.

mount_policy.prepare accepts explicit reviewed-input records for Groq, Gemini,
Mistral only, exact official HTTPS endpoint, bounded model name, caller review
within24h, disclosure/free-only assertions, report/day/request/token/time/bytes
caps. These assertions are unverified caller data: output says account/owner
permission unverified, mountedFalse, transportFalse. It rejects shared legacy
proxy, arbitrary host/path/query/userinfo, unsupported saved-provider widening,
paid fallback and budgets multiplied beyond aggregate12requests/24000tokens.
Caps are design guardrails, not provider quota availability or execution proof.
Per-report wall <=120seconds and per-attempt <=15seconds are proposed caps;
existing shell only bounds each request, so it does NOT enforce this overall
wall. Mount requires a separate reviewed implementation to enforce all budgets
across report sections, failovers and grounded retry. No silent PDF truncation:
static original report fallback when exhausted, labeled non-live facts.

## Sources inspected October8,2026

Official docs only. Account state, actual quotas and key permissions unverified.
No model from docs or original stale arrays is selected by this increment.

- https://console.groq.com/docs/api-reference
  Documents POST https://api.groq.com/openai/v1/chat/completions.
- https://console.groq.com/docs/your-data
  Inference data not retained by default; system reliability/abuse logs may be
  retained up to30days unless legally required longer. ZDR is configurable,
  not assumed active. Never call all free providers zero-retention.
- https://ai.google.dev/gemini-api/docs/pricing
  Free tier has limited model access and content used to improve products;
  exceptions/terms need account+region review. Some models lack free tier.
  Paid search/grounding must not be an automatic fallback.
- https://ai.google.dev/gemini-api/docs/rate-limits
  Limits apply per project, not per API key; rotating keys cannot create a
  valid new quota. No numeric account quota is asserted here.
- https://ai.google.dev/gemini-api/docs/generate-content/get-started
  Documents generativelanguage.googleapis.com/v1beta/models/{model}:generateContent.
  The guide calls this legacy and recommends Interactions for new projects.
  Preserving the old Finder API shape is a reviewed compatibility choice, not
  a claim that it is the newest Google API.
- https://docs.mistral.ai/api/endpoint/chat
  Documents POST https://api.mistral.ai/v1/chat/completions.
- https://docs.mistral.ai/admin/billing-usage/usage-limits
  Free mode offers included usage within account limits. Pay-as-you-go may
  extend usage beyond included usage. Verify it is off before free-only use.
- https://docs.mistral.ai/admin/monitor-comply/privacy-data-controls
  API data is not used for model training. This is NOT proof of zero retention.
- https://docs.mistral.ai/admin/monitor-comply/zero-data-retention
  ZDR available on paid plans for supported stateless calls. Do not promise
  free-tier ZDR based on the older2024release announcement.

## Before actual mounting

Owner approves exact providers and prompt fields (product/code/country and
approved report data), account/key scope, audience and free-only budget.
Confirm current model free eligibility and retention terms for that account.
A private server proxy needs authenticated user/CSRF, durable quota ledger,
per-user and shared account budgets, bounded concurrency1-2 on512MB, fixed
provider allowlist, no redirects, no request-driven URLs/tools/grounding or
external retrieval, strict provider response parsing and output escaping.
No third-party shared proxy inherits permission to see prompts or keys.
Never put keys into client HTML/logs or expose one user's prompts to another.
Preserve unsupported-key refusal and failover without moving a saved key to a
different provider. Check existing original proxy/BYOK behavior before deciding
whether to preserve or migrate it; this evaluator does not silently replace it.

Factual labels must distinguish AI model knowledge, dated snapshot data and
verified current sources. Existing full-report UI says official/exact/live-ready
elsewhere; reviewed served-copy corrections required before real exposure.
Test actual PDF pages/first-last sections with enforced budget and static
fallback, browser errors, errors during JSON body, malformed JSON,429,deadline,
quota concurrency/restart and no-private-data leakage. Test real provider smoke
only within source-grounded disclosure permission; this unit performs none.

Mounting/secrets/quotas are later decisions. This source-only unit completes a
design checkpoint, not the requested live feature or full parity.

# Hybrid live adjudication decision preparation

Copyright (c) 2026 Push. All rights reserved.

Source-only design and fixture evaluator, not a connector or mounted feature.
Existing hybrid.plan stays unchanged: keyword product/code+country accept,
no-product reject, uncertain held; supplied AI threshold0.8 remains uncalibrated.

calibration.evaluate accepts explicit threshold candidates and closed hash-bound
caller-labeled examples. It reports confusion counts, decided coverage, held
positives/negatives, precision, overall-positive recall (held positives count as
not retrieved), decided-only accuracy, and positives rejected by the keyword
stage. Missing denominator yields null, not invented zero/100% accuracy. It
never picks a threshold or changes config. Labels and model scores are supplied,
unverified data. Synthetic tests prove calculation behavior, not real accuracy.

Before a live path:
- Have the owner confirm exact provider(s), permitted prompt fields, sender of
  provider requests, audience/disclosure boundaries, saved key scope and limits.
- Check current official model endpoints, free quota, rate limits and retention
  terms. Groq/Gemini/Mistral are allowed choices, not already-approved live
  disclosure. No API/model/free-tier claims are made by this design.
- Build a reviewed transport with no paid fallback, fixed request/output size,
  wall-clock and quota caps, strict JSON schema, no tools/link retrieval. Timeout,
 429, malformed response or quota exhaustion keep item held with explicit reason.
- Treat article/title/summary as untrusted data, never execution instructions.
  Review returned JSON as data. Never allow a result to pick tools, recipients,
  destinations, schedules or expose user/private context.
- Bind results to context and article hashes, provider/model/config version and
  actual transport outcome. Preserve provider_verified=false meaning no factual
  correctness/recipient delivery guarantee. Separate transport attribution from
  model correctness. AI-related is a suggestion, not tariff/legal verification.
- Use owner-reviewed labeled examples representative of actual products,
  countries, dates and sources, including keyword rejects and negatives. A
  confidence value is self-reported, not a probability calibrated by these tests.
  Record sample size, selection bias and false-positive/recall tradeoff before
  recommending a threshold. Keep a held state; never force a binary choice.
- Decide whether to widen recall: country-only/no-product now skips AI, so a
  threshold change cannot recover those missed positives. Synonyms/full-text
  matching is a separate source/privacy/budget decision. No automatic expansion.

Mounting belongs to an explicit later reviewed seam with disclosure and quota
permission; this increment adds no provider call, prompt export, routing, DB,
client, callback, environment, stored keys or activation.

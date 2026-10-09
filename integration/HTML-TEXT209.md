# Geo summary HTML text policy 209

Copyright (c) 2026 Push. All rights reserved.

Owner report October 8, 2026 16:20:09 identified cascading &amp; before &lt;
replacement in geonews processing/classifier.py. Original numbered item 15 asks
single-pass entity decoding/tag handling and numeric/Unicode/malformed/tag tests.
This unit changes Geo summary text only. Sanctions decoder 150 is separate and
unchanged. Title normalization is deferred. Already stored summaries are NOT
rewritten. This does not prove whole item 15 or live collection complete.

## Contract

Remove actual markup by HTMLParser source-position spans, then decode references
once, then remove markup produced by that single decode. Entity parser events are
never reconstructed: raw source text preserves AT&T, &amp 5, &#65 x, &#x41, &;,
&#;, and &foo; exactly. No html.unescape, semicolonless repair, cascading replace,
or regex parsing of HTML. Semicolon-terminated html.entities.html5 keys only;
multi-codepoint values supported. Numeric references use ASCII decimal/hex digits,
x or X and leading zeros, at most 12 digits. Zero, surrogate, out-of-range,
controls except TAB/LF/CR, and Unicode noncharacters remain literal. NBSP and all
Unicode whitespace collapse to ASCII spaces. &hellip; becomes the actual Unicode
ellipsis, not the old three ASCII dots. Encoded once tags are stripped; nested
escaped text stays escaped. Existing HTML renderers must still escape plain text.

Actual/once-encoded script/style element and its content are removed. Unclosed
script/style removes remainder deliberately. Complete comments/declarations/PIs
and CDATA declarations removed; incomplete declarations/comments remain literal.
Raw declaration spans are masked before HTMLParser so unknown declarations cannot
assert. Unterminated ordinary tags remain literal: <div and a <b preserved.
Prose a < b / x <3 y preserved. Script/style always hide content regardless of attributes. Known HTML elements
strip when every valueless attribute is in the fixed broad bare-attribute set;
unknown elements with any bare attribute, or known elements with an unknown bare
attribute, stay literal. Ambiguous start tags with unknown bare attributes
are retained, so if a<b and c>d remains prose. Quoted attributes with > are handled
by HTMLParser, not regex. Tag boundaries become spaces. No version check, import
time assertion, refusal, or exception-swallowing in the helper.

Golden output vectors are independent literal expectations, not helper-derived.
AST parity tests check integration only; they share the actual helper and are not
claimed independent behavioral oracles. Golden vectors run on proven CPython
3.10.12. Other interpreters are unverified. The actual target runtime must pass
this golden suite before any activation/deploy using the helper, a blocking
acceptance prerequisite for items 27-29, not an import-time/runtime gate.

## Caller and field inventory

| Path | title/summary assignment and classifier/text calls | decoding count |
| --- | --- | --- |
| intelligence/geo/collectors/rss.py | _fetch_feed title stripped only; summary/description strip_html; optional extracted full text replaces summary; collect calls classify, truncates stored summary to 300 | feed summary once; extracted plain text zero; classify zero |
| intelligence/geo/collectors/gnews_search.py | title stripped only; description strip_html; classify then documents summary[:300] | summary once, title zero |
| collector120_prep/gnews_supplied.py | executes same pinned collect AST over supplied SDK outcomes, injects classify/strip_html; returns detached documents | same once |
| integration/supplied_feed_fixture.py | executes pinned _fetch_feed AST, wrapper calls hash-pinned helper | once |
| collector129_prep/supplied_feed.py | same supplied AST with separate captured aggregate budget; coordinated runtime decoder-binding adaptation approved | once after reviewed adaptation |
| integration/feedparser_audit/child.py | parser-sanitized fixed synthetic rows, both supplied selection and AST parity oracle call helper independently from original row, never sequentially | once per branch; upstream feedparser sanitization is separate |
| integration/supplied_collector_pipeline.py and supplied_multi_feed.py | supplied feed output to supplied enrichment, then original document preparation | no second decoder |
| integration/supplied_fulltext_fixture.py | optional supplied extraction replaces summary; geo_collector_contract classifies | no second decoder |
| integration/fixed_parser_pipeline.py | fixed parser child output to supplied fulltext preparation | no second decoder |
| integration/geo_collector_contract.py | caller supplies candidate title/summary; pinned original classification/document AST, truncated summary | zero; raw supplied HTML is not automatically decoded |
| integration/collection_prepare.py | manual/offline supplied Geo candidates classified as supplied, summary[:300] | zero; caller responsible for text provenance |
| integration/collector_mail_fixture.py | supplied candidates to document contract, stored supplied rows to escaped mail renderer | zero extra decoding |
| intelligence/geo/collectors/official.py | empty collect stub; no fields/classifier | none |
| intelligence/geo/collectors/events.py | empty event seed; no article title/summary/classifier | none |
| intelligence/geo/collectors/sanctions.py | held legacy service; no article summary/classifier | none |
| intelligence/brics/collectors/rss.py + processing/classifier.py | separate _clean + BRICS classify; does not import Geo strip_html | unchanged, outside scope |
| intelligence/brics/collectors/official.py | manual-check homepage stub title/summary; BRICS processing only | unchanged, outside scope |
| scraper/GDELT | no such collector modules in current repo; no Geo text-helper caller found | not invented |
| tests/text_matching/test_matching.py | direct classify with literal titles/summaries | zero |
| tests/test_supplied_feed_fixture.py, test_supplied_collector_pipeline.py, test_supplied_multi_feed.py | execute actual AST parity wrappers and compare from independently copied raw rows | once per branch |
| tests/test_news182.py | GNews AST with identity strip_html stub for date-only test | zero, not HTML proof |
| tests/test_html209.py | independent golden corpus, named/numeric/control/fuzz vectors, no-downstream-redecode check | explicitly tested |
| remaining tests/collector tests | call named supplied entry/fulltext/GNews/cycle seams above; mutate detached title/summary fixtures only | no new decoder |

Geo classify intentionally still receives raw titles such as AT&amp;T. Supplied
manual candidates and extracted text can reach matcher raw. No title/fulltext
normalization claim. Field storage, matcher/rules/scoring/date policy unchanged.
No DB rewrite, SMTP, collector activation, engine/bootstrap/install/deploy edits.

## Wrapper boundary

Both wrappers execute the actual hash-pinned classifier strip_html AST, whose
only names are text and strip_html_once and which has no attributes. The injected
strip_html_once is the same imported pure helper, separately byte-pinned in each
PINS mapping. No duplicated decoder, dynamic imports or startup effects. Helper
imports html.parser and html.entities only. No wrapper builtin added. Existing
Exception/print builtins remain unchanged. Old classifier source shape refused.
Runtime confirmed no active conflicting wrapper patch. 197 worker pin refresh is
metadata only, no engine edits. Historical original source inventories unchanged.

Prose/tag ambiguity cannot be resolved perfectly: known element b with bare
attribute c remains prose, while b with bare attribute hidden is stripped. Real
HTML bearing unknown bare attributes can remain literal. This is plain-text
processing, not a safe-HTML sanitizer. Bare-attribute whitelist covers tested
legacy and modern WordPress/embed tags. Script/style masking bypasses that
heuristic unconditionally, including defer/async/nomodule/unknown bare attributes.

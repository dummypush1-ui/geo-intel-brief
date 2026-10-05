# Mobile-safe original report preview frame

Only digest_preview digest/weekly output is framed. Original hash-pinned report
sources, direct renderer output and mail builder output remain unchanged. No
new send, event query, data selection, client or runtime activation. Critical
preview remains unchanged; its missing alert glyph is a separate original issue.

Re-sanitizes HTML first, then appends fixed trusted viewport/CSS. Source script,
style, iframe and unsafe links remain blocked. Body style is retained so font,
colors and desktop appearance don't default to browser serif. Source tables
retain order/content, but private preview outer report widths can shrink to
phone width. Cell/anchor long words wrap. Not a changed email template and no
claim all mail clients are responsive. Only internal original body shape used.

11 focused wrapper+existing preview route tests pass locally with restored
original assets. Author actual pixel checks at390px digest/weekly long title and
summary fixtures: no horizontaloverflow, readable font/layout, no external
resource requests. Direct original weekly still width680, originalhashesmatch.
No actual phone/mailclient/hostedproxy check. Desktop/event/empty visual cases
need expanded check before broad UI readiness claim. Fullsuite69:913testsPASS,1skip,1expectedfailure. Reviewer independently
checked four wrapper tests and390/1280pixels, but lackedFlask forroute tests.
Repro python -m unittest tests.test_report_preview_frame tests.test_digest_preview_routes -v;
requirements-staging.txt plus python-dateutil installed, bundled originals.

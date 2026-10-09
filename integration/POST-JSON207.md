# 207: bounded read-context POST bodies

Only /api/related-news and /api/finder-context change. Auth then Origin guards
remain first (403), parser next, reader only after valid body. No v1 POST aliases,
UI/auth/CSRF/CORS changes, app-wide MAX_CONTENT_LENGTH or other route changes.
This closes188's named two-route gap, not whole-app validation.

application/json only, optional single charset=utf-8 (case-insensitive), no other
or duplicate parameters. application/*+json refused415. Raw body cap16384bytes;
JSON escapes count against it. Observable environ CONTENT_LENGTH must be canonical
positive ASCII decimal (no leading zeros/sign/whitespace/comma/duplicate values).
Missing/empty length411, invalid/zero400, declared overcap413 before read.
HTTP_TRANSFER_ENCODING present400. Short/disconnected body400. All errors have
fixed "Invalid read context" JSON, no supplied values/body echo or logging.
StrictUTF8/noBOM; object_pairs_hook refuses nested and top-level duplicate keys,
including identical values. parse_constant refuses NaN/Infinity. Exactobject,
closedkeys/noqueryparams. Decode/JSONValueError/RecursionError400. Oversize nested
arrays/hugeinteger413 before decode/parse. Under-cap recursion/5000digit integer
refused400 in tested Python3.10's integer-string-limit environment.

Nonterminated input: never read beyond declaredlength or bypass request.stream.
Duplicate Content-Length headers and bytes beyond declaredlength are unobservable
at Flask on a nonterminated server. Deployment server unreviewed; HTTP framing
relies on that server/proxy. NO request-smuggling protection claim. Explicit
wsgi.input_terminated=True permits bounded cap+1 read and excess-body detection;
actual bytes must equal declaredlength. These are Werkzeugtestclient/hand-built
environ forms with/without terminated input, not end-to-endHTTPframing proof.

Relatedoptionalkeys: code/system/edition/country/product_terms. Exactstrings,
codeempty orASCII1..12digits (leadingzeroskept),system/edition32,country100chars.
Terms exactlist<=20/exactstring<=200chars. Emptyobject/code/terms keep priornoop
semantics. Allstrings refuseC0/DEL/C1/lonesurrogates, exceptTAB/LF/CR allowed
within terms only;NBSPallowed asordinaryUnicode. No trim/normalization. Matcher
unchanged, including its narrower6..12digit explicit-code evidence behavior.
Finderexactrequiredprojectgeo|brics and lowerhex64article_key; no unknownfields.

## Browser and source bounds

206 index.html503-525 SYS.tag values22tags,max3chars,no whitespacepadding;
sysTagHtml1226 directly inserts tagtext,workspace.js111 reads untrimmedtextContent.
SYS_COUNTRY workspace.js6 longestlabel UnitedArabEmirates20characters. Caps32/100
cover currentlabels, not a promised futurecatalog. workspace.js110 stripscode
nondigits and only guards!code, so all ASCII lengths1..12 accepted here.

Actual data.d6d1b417562b.js340232rows decoded for this audit;SHA256
`d6d1b417562bad99e7b434605d63966772749d573375fb10d74ee52cb6bb82f6`.
Digits-only code lengths per systemindex snapshot:
0:0,2,4,6;1:2,4,5,6,7,8;2:4,6,8,10;3:2,4,6,8,10,12;
4:2,4,6,10;5:2,4,6,7,8,9,10;6:2,4,6,8,10;7:2,4,6,9;
8:4,5,6,7,8,10;9:2,4,5,6,7,8;10:11;11:10;12:2,4,5,6,8;
13:2,4,6,8;14:2,4,6,8,10;15:2,4,6,8,10;16:0,2,4,6,8;
17:0,2,4,6,8;18:0,2,4,6,10;19:2,4,6;20:2,4,6,8;21:2,4,6,8.
Emptycodedrows failbrowser!code guard. Laterindexcode>12 would be refused until
boundreview; this is a snapshot not a dynamicindexvalidator.

Related-news requests from code pages whose description exceeds200characters
already fail today; this unit keeps that behaviour and does not fix it.
Groundedindexmaxdescription2850chars,376rows containTAB/LF/CR,currentcap200.
Frontendexcerpt/split/truncatepolicy or measuredservercost/timebudget remains
queued separately.20x200ASCII fits16KiB;4000fourbytecharacters plus usualJSON
payload roughly16KB fits, but escaped representations can exceed and413.
No promise everymaximal-field combination fits the aggregatecap; no truncation.

Tests compare valid{},code-only,country-only against oldhandler's exactfixture
loop/output; validFinder/currentbrowser-shape preserved. Test multiline/NBSP,
200passes/201fails, closedfields/types/controlbounds, media/charset, duplicate/
nonfinite/UTF8/BOM, query, depth/integer/size, environlength/TE/terminated forms,
auth/Origin403 before read/parser and no reader on refusal.49focused regressions
run; no UI/pixelchange, DBwrite/mail/network/collector/liveeffect.201c held.

Behavior changes: fixed error text is now "Invalid read context"; wrong media
returns415 (previously400). Null fields, nonstring country and unknownkeys now
return400 where oldhandler accepted some. Declaredovercap413 precedes parsing.
These are validation changes, not currentbrowserpayload regressions.

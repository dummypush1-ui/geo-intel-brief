# 203 articles-only supplied digest preview

New pure render_preview takes ORIGINAL closed rows plus explicit193date/channel/
receiptfixture/limit and explicit fixedUTCoffset minutes+label. Invokes202itself;
no arbitrary selection dictionary accepted. Original category/card conventions
read from live push2006/geonews reports/email_report.py and landed digest render.
Category presentation follows original order; missing/empty/unknown category is
merged into GENERAL labelledOther, never dropped. Unknowns share originalOther
group deliberately; originalemoji/risk-colour styling is not reproduced. Cut occurs in193selection order before categorizing.

Two sections: Last24hours and Last7days(includeslast24hours). CountsShowingNofM
always printed from precap selection counts; distinct precap union uses193last7dayseligible_count, since24his subsetof7days
under identicaldatefield/eligibility. No duplicatedrenderereligibility logic. An overlap appears twice in section counts, once
inunion. Rendered-ID multiset equals selected-ID multiset, set equals supplied
selection-only union; counted omitted occurrences tracked. selection_only_union_ids
is NOT receipts, delivery/mark permission or an authenticated alltime ledger.

Fixed offset deterministic display; timezone label and numericoffset+asofclock
printed. No serverzone/IANA/tzdatafallback or DSTclaim. SnapshotID/datefield/channel
andPREVIEWnot-sent/datepolicyandreceipts-unverifiedbanner shown. No ObjectIds in
HTML/plaintext. Byte-deterministic outputs; input rows untouched.

Local link helper inspired by integration.news_view.safe_url; it is intentionally
new, no unreviewed original helper required. Exacthttpsonly(same landedrendererpolicy),2048charcap, no
userinfo/control/format/whitespace/backslash, validates host/port. ALLoriginal
links checked, including receipt-excluded/oldrows. Any invalid link holds the
WHOLErender, no silentitemdrop. Attributes/text HTMLescaped, linksnoopener
noreferrer. plain helper neutralizesUnicodeCc/Cf and collapseswhitespace/newlines,
includingbidi; plainpart noMarkdown/autolinking. Unknown fields/text overflow
stillheld by202/193. No remoteimages/fonts/CSS,JS or fetchedresources.

512KiB cap EACH HTML/plaintext offlinepreview; overflowholds wholeoutput, no
rowsreduced. This is NOTanemailbudget or clienttest. Futureemailunit needs lower
independentlyverifiedsizebudget,inlineCSS/tablelayoutandclienttesting. No darkmode
claim. Article-only preview explicitly says eventsnotsupplied, not zeroevents.

HeadlessChromium suppliedfixture inspected at390and1280px;nohorizontaloverflow,
zeroexternalrequests. Screenshots show completebanner/asof/metadata,twosections,
Othergroup andcap/clientcaveat. No liveapp/route/DBquery/client/env/readclock/
transport/sender/mark/archive/scheduler mounted. Ownerdatepolicy, actualsource,
authenticatedreceipts/norepeat andemaildeliveryremainheld.201cunchanged.

Secondrenderer rationale: landed geonews_digest/render.py implements legacy
unsent selection/event/layout conventions;203is an unmountedtwo-windowpreview
with202/193selection and visibleintegrity/capmetadata. Do not replace/wireeither
until a later reviewedconsolidationpreservescontracts and safepolicies. Local
helperstricterwholeinputrefusal isintentional, not sharedlegacybehaviorchange.

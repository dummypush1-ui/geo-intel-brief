"""Default-OFF data-only report served-copy profile. No provider calls."""
import re,hashlib,base64
FLAG='PUBLIC_FINDER_DATA_REPORT_ENABLED'
class Held(ValueError):pass
def enabled(env):
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise Held('Exact data-report flag required')
 if value=='true'and env.get('PUBLIC_FINDER_CANDIDATE_COMPOSITION_ENABLED')!='true':raise Held('Data report requires selected candidate composition')
 return value=='true'
def once(text,old,new):
 if text.count(old)!=1:raise Held('Report served-copy seam drift')
 return text.replace(old,new,1)
def head_insert(html,value):
 spans=list(re.finditer(r'<script\b[^>]*>.*?</script>',html,re.S|re.I))
 matches=[m for m in re.finditer(r'</head>\s*<body\b',html,re.I)if not any(x.start()<=m.start()<x.end()for x in spans)]
 if len(matches)!=1:raise Held('Actual document head seam drift')
 at=matches[0].start();return html[:at]+value+html[at:]
def transform(html):
 if type(html)is not str or len(html)>40*1024*1024:raise Held('Bounded safe render required')
 # Only the reviewed complete safe render may be supplied by owning Selection.
 if 'const OFFLINE_STORE = {getItem(){return null;},setItem(){},removeItem(){}};'not in html or "const fetch = async()=>{throw new Error('Offline snapshot: live network disabled');};"not in html:raise Held('Network/storage-disabled render required')
 html=once(html,"  const aiUsed = !!narrative;","  narrative = null; // Data report never enables or calls live AI.\n  const aiUsed = false;")
 start=html.index('  const modeLine = aiUsed\n');end=html.index("\n\n  return '<!doctype html>",start)
 html=html[:start]+"  const modeLine = 'Preserved data snapshot. Codes, rates, trade figures and source labels are copied from this dataset, not independently checked for currentness. Narrative sections contain general context, not live AI research. No API key is needed. Verify official sources before filing or trading.';"+html[end:]
 start=html.index('async function openTemplateReport(db, idx, w) {');end=html.index("  const html = buildTemplateReport",start)
 html=html[:start]+"async function openTemplateReport(db, idx, w) {\n  const narrative = null, aiError = ''; // No provider or key lookup.\n"+html[end:]
 start=html.index("  el('d-tpl').addEventListener('click', () => {");end=html.index("  el('d-copy').addEventListener",start)
 html=html[:start]+'''  el('d-tpl').addEventListener('click', () => {
    const w = window.open('', '_blank');
    if (!w) { V.briefError = 'Popup blocked. Allow popups to open the data report.'; paintDetail(); return; }
    V.needKey = false; V.busy = true; V.briefError = null; paintDetail();
    openTemplateReport(db, idx, w).catch(() => { V.briefError = 'Could not open the data report.'; }).finally(() => { V.busy = false; if (S.sel === idx) paintDetail(); });
  });
'''+html[end:]
 html=once(html,"'Writing the report with AI...' : 'Make the PDF report'","'Opening data report...' : 'Make the data PDF report'")
 old="One tap makes the branded 14-section PDF - exact official data with AI-written analysis inside. "
 start=html.index(old);end=html.index("</p></div><span class=",start)
 html=html[:start]+"Make a data-only PDF with all ' + TPL_SECTIONS.length + ' preserved sections. No AI key is needed. Live AI stays unavailable. Snapshot figures and source labels are not a current legal or market verification."+html[end:]
 # The source has21 cross rows for this code, not22 rows merely because SYS
 # lists22 systems. Label both actual represented rows and dataset coverage.
 html=once(html,"' official systems ' + tplTag('fact') + '</h3><table", "' represented systems (dataset: ' + SYS.length + ' systems) ' + tplTag('fact') + '</h3><table")
 html=once(html,"'<h3>Duty / rate for this product across ' + SYS.length + ' official systems '","'<h3>Duty / rate rows for this product: ' + dutyRows.length + ' (dataset: ' + SYS.length + ' systems) '")
 html=once(html,'Every figure, code and rate in this report is exact official data with its data date. Narrative sections are analysis and context - market reading, opportunities, risks; judgment can be wrong, so act on it only after your own verification. Rates change - verify against the official portal before filing.','This report preserves dataset values and source labels. It does not verify current rates, sanctions, law or market conditions. General chapter context is not product-specific research. Check the official sources before filing, shipping or trading.')
 html=once(html,'Paperwork typically needed to move this product to or from India. AI-compiled from current official guidance - confirm each item with your CHA or DGFT before shipping.','Preserved general paperwork checklist, not current AI research. Confirm the requirements for your shipment with your customs adviser or the official source.')
 html=once(html,"This file has no live news feed. What it does have: the dataset rebuilds automatically from official sources (current build ","This report has no live news feed or verified automatic refresh. Preserved dataset build: ")
 html=once(html,"'), and the finder\\'s change-alerts feature flags saved codes whose duty, GST or linkage changed between builds. For same-day policy moves check the CBIC notifications page and the DGFT portal directly.</p>'", "'. For same-day policy moves check the CBIC notifications page and the DGFT portal directly.</p>'")
 # Report claims describe the preserved source, never a live verification.
 html=once(html, '/* ---------- 14-section template report (print to PDF) ---------- */', '/* ---------- Dataset report; contents derive from TPL_SECTIONS ---------- */')
 html=once(html, "'of ' + SYS.length + ' official'", "'of ' + SYS.length + ' in dataset; linked rows in section 03'")
 html=once(html, "'<p>For a full AI-written ' + esc(topic) + ' analysis of this exact product, add a free Gemini key (AI settings on the code page) and regenerate this report.</p>'", "'<p>Product-specific research is not included. Live AI is unavailable in this data report.</p>'")
 html=once(html, 'Verified position ', 'Dataset position ')
 html=once(html, 'Cost factors from verified data ', 'Cost factors from dataset values ')
 html=once(html, 'Data currency ', 'Dataset dates ')
 html=once(html, '. The finder refreshes official sources automatically every week and its change-alerts feature flags saved codes whose duty, GST or linkage changed between builds.', '. This preserved snapshot does not confirm a refresh schedule or currentness. Source dates below describe the dataset, not a new verification.')
 html=once(html, "String(SYS.length) + ' official government systems'", "String(SYS.length) + ' systems in preserved dataset'")
 html=once(html, ' linked official systems publish an open general rate for this product.', ' represented systems have a general rate in this snapshot.')
 html=once(html, ' systems publish an open general rate here; preferential/FTA rates excluded.', ' represented systems have a general rate in this snapshot; preferential/FTA rates excluded.')
 html=once(html, 'General / MFN duty rate where the official source publishes an open figure.', 'Preserved general / MFN duty figures with source labels from the dataset.')
 html=once(html, 'The tariff classification, duty rate and GST rate in this report come from the official government tariff schedule and GST notifications.', 'The dataset labels tariff and GST values with their source schedules and notifications. These source attributions are preserved, not independently verified here.')
 # Screen page numbering must not force section-sized sheets into print.
 # Leave existing runtime listeners intact; print CSS uses natural flow.
 extra="@media print { html,body,#root { min-height:0!important; height:auto!important; background:#fff!important; } .app-shell { min-height:0!important; } .shortlist-view { min-height:0!important; margin:0!important; padding:0!important; } }"
 html=head_insert(html,'<style id="finder-data-report-print">'+extra+'</style>')
 report_css="@media print { @page { size:A4; margin:14mm 12mm 16mm; } body { max-width:none; } .tpl-page,.tpl-sec { min-height:0!important; position:static!important; padding:4mm 0!important; margin:0!important; break-before:auto; break-after:auto; box-shadow:none; border-top:0; } .tpl-page:first-of-type { padding-top:0!important; } .tpl-cover-title { font-size:28px; margin:5mm 0 2mm; } .tpl-kpis { display:grid; grid-auto-flow:column; grid-auto-columns:minmax(0,1fr); gap:2mm; margin:3mm 0; } .tpl-kpi { padding:2mm; } .tpl-contents { columns:2; margin:2mm 0; } .tpl-contents li { padding:1mm 0; font-size:11px; line-height:1.35; } .tpl-sec h2 { font-size:18px; margin:5mm 0 3mm; } .tpl-page h2 { margin:5mm 0 2mm; } .tpl-sec h3 { margin:3mm 0 1mm; } .tpl-sec p { orphans:3; widows:3; } .tpl-foot { margin-top:4mm; } }"
 html=once(html,"    '</style></head><body>' +","    '"+report_css+"' +\n    '</style></head><body>' +")
 # Existing inline CSP has to cover the changed script bytes; header is rebuilt
 # by owning HTTP views as well. No external source or unsafe-eval is added.
 html,n=re.subn(r'<meta http-equiv="Content-Security-Policy"[^>]*>','',html,count=1)
 if n!=1:raise Held('Safe CSP seam drift')
 scripts=re.findall(r'<script>(.*?)</script>',html,re.S|re.I)
 hashes=' '.join("'sha256-"+base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()+"'"for s in scripts)
 html=head_insert(html,'<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src '+hashes+'; style-src \'unsafe-inline\'; img-src data:; connect-src \'none\'; form-action \'none\'; base-uri \'none\'">')
 return html

# Copyright (c) 2026 Push. All rights reserved.
"""Hash-pinned served-copy seams. Original Finder bytes are never edited.

This is a feature-preparation adapter, not wired into public/private routes.
Caller still owns CSP, provider-disclosure approval, quota/model checks and
network gating. AI errors retain the original static report fallback.
"""
import hashlib

SOURCE_SHA = 'c4ad608f8830852430b6f67f6ee004001197e4f2f58629227900e5f72bedfc9e'


def prepare_shell(source):
    if type(source) is not str or hashlib.sha256(source.encode()).hexdigest() != SOURCE_SHA:
        raise ValueError('Finder source requires fresh review')
    replacements = (
        ("  arr.push('nvidia');", '  // Only the three owner-selected providers.'),
        ("  if (['groq', 'gemini', 'mistral', 'nvidia'].includes(V.apiProvider)) return V.apiProvider;",
         "  if (['groq', 'gemini', 'mistral'].includes(V.apiProvider)) return V.apiProvider;\n  if (V.apiProvider === 'nvidia' || /^nvapi-/i.test(V.apiKey.trim())) throw new Error('This merged Finder supports Groq, Gemini and Mistral only. Clear the unsupported saved key.');"),
        ("  if (/^nvapi-/i.test(k)) return 'nvidia';", '  // NVIDIA is not an allowed provider in the merged Finder.'),
        ("  if (AI_PROXY_URL) { set.add('gemini'); set.add('groq'); set.add('mistral'); set.add('nvidia'); }",
         "  if (AI_PROXY_URL) { set.add('gemini'); set.add('groq'); set.add('mistral'); }"),
        ("  if (builtinKeys('nvidia').length) set.add('nvidia');", '  // Unsupported built-in provider ignored.'),
        ("const PROVIDER_CALL = { groq: (k, p, o) => groqPost(k, p, o), gemini: (k, p, o) => geminiText(k, p, o, false), mistral: (k, p, o) => mistralPost(k, p, o), nvidia: (k, p, o) => nvidiaPost(k, p, o) };",
         "const PROVIDER_CALL = { groq: (k, p, o) => groqPost(k, p, o), gemini: (k, p, o) => geminiText(k, p, o, false), mistral: (k, p, o) => mistralPost(k, p, o) };"),
        ("const nvidiaPost = (apiKey, prompt, opts) => oaiPoolPost('nvidia', 'https://integrate.api.nvidia.com/v1/chat/completions', NVIDIA_MODELS, apiKey, prompt, opts);",
         "const nvidiaPost = async () => { throw new Error('Unsupported provider'); };"),
        ("<option value=\"nvidia\"' + (selProv === 'nvidia' ? ' selected' : '') + '>NVIDIA - free key (90-day)</option>", ''),
        ("const aiAvailable = () => Boolean(V.apiKey || AI_PROXY_URL || BUILTIN_GEMINI_KEYS.trim() || BUILTIN_GROQ_KEYS.trim() || BUILTIN_MISTRAL_KEYS.trim() || BUILTIN_NVIDIA_KEYS.trim());",
         "const aiAvailable = () => Boolean(V.apiKey || AI_PROXY_URL || BUILTIN_GEMINI_KEYS.trim() || BUILTIN_GROQ_KEYS.trim() || BUILTIN_MISTRAL_KEYS.trim());"),
    )
    for old, new in replacements:
        if source.count(old) != 1:
            raise ValueError('Finder seam changed')
        source = source.replace(old, new)
    # Provider fetches had no deadlines. Bound each existing request while
    # preserving response parsing and original sequential failover behavior.
    # No request is started here; this function only produces a served copy.
    start = source.index('async function geminiPost(')
    end = source.index('/* ---------- small helpers ---------- */', start)
    section = source[start:end]
    if section.count('await fetch(') != 3:
        raise ValueError('Provider fetch seam changed')
    section = section.replace('await fetch(', 'await mergedProviderFetch(')
    helper = """async function mergedProviderFetch(url, options) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 15000);
  try {
    const res = await fetch(url, Object.assign({}, options, {signal: ctrl.signal}));
    const data = await res.json().catch(() => ({}));
    if (ctrl.signal.aborted) throw new Error('AI response timed out');
    return {ok: res.ok, status: res.status, json: async () => data};
  }
  finally { clearTimeout(timer); }
}
"""
    source = source[:start] + helper + section + source[end:]
    seams = (
        ("Live research edition - narrative sections written with live web research; all codes, rates, GST, trade figures and sanctions facts are exact official data.",
         "AI-assisted research edition - narrative sections may use model knowledge only. Snapshot figures have the dates shown; check current rules and rates before use."),
        ("Live AI research edition", "AI-assisted research edition"),
        ("'@media print { body { background: #fff; max-width: none; } .tpl-page, .tpl-sec { box-shadow: none; margin: 0; } .tpl-actions { display: none; } h2, h3 { break-after: avoid; } }'",
         "'@media print { body { background: #fff; max-width: none; } .tpl-page, .tpl-sec { box-shadow: none; margin: 0; min-height: 0 !important; padding: 6mm 8mm; } .tpl-contents { columns: 2; font-size: 11px; } .tpl-contents li { padding: 1.2mm 0; font-size: 11px; } .tpl-cover-title { font-size: 27px; } .tpl-kpis { margin: 3mm 0; } .pgnum, .tpl-actions { display: none; } h2, h3 { break-after: avoid; } }'"),
    )
    for old, new in seams:
        if source.count(old) != 1:
            raise ValueError('Report print/label seam changed')
        source = source.replace(old, new)
    return source

// Minimal Gemini client for the refresh worker (mirrors the app's model chain).
const GEMINI_MODELS = ['gemini-3.8-flash', 'gemini-3.7-flash', 'gemini-3.6-flash', 'gemini-3.5-flash-lite', 'gemini-3.1-flash-lite', 'gemini-2.5-flash-lite', 'gemini-2.5-flash'];

export async function geminiPost(apiKey, body) {
  let quotaHit = false;
  for (const m of GEMINI_MODELS) {
    let res, data;
    try {
      res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${m}:generateContent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-goog-api-key': apiKey.trim() },
        body: JSON.stringify(body),
      });
      data = await res.json().catch(() => ({}));
    } catch { throw new Error('no connection to Gemini'); }
    if (res.ok) return { data, model: m };
    const msg = (data && data.error && data.error.message) || ('Gemini API error ' + res.status);
    if (res.status === 400 && /key|api/i.test(msg)) throw new Error('GEMINI_API_KEY not accepted: ' + msg);
    if (res.status === 403) throw new Error('GEMINI_API_KEY refused: ' + msg);
    if (res.status === 429) { quotaHit = true; continue; }
    if (res.status === 404 || /not found|no longer|deprecated|not supported|unavailable|retired/i.test(msg)) continue;
    throw new Error('Gemini failed: ' + msg);
  }
  throw new Error(quotaHit ? 'Gemini quota exhausted on all models' : 'no Gemini model available');
}

const stripTags = (s) => s.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
const canon = (s) => stripTags(s).toLowerCase().replace(/[^a-z0-9]+/g, '');

// AI-assisted description cleanup with a hard safety rule: an AI proposal is
// accepted only when its alphanumeric content is identical to the deterministic
// tag-stripped original. Anything else falls back to the deterministic strip.
// Official wording is never rewritten - markup artifacts only.
export async function cleanDescriptions(apiKey, dirty) {
  const cleaned = {};
  const needAI = [];
  for (const d of dirty) cleaned[d] = stripTags(d);
  if (!apiKey) return { cleaned, ai: 0, note: 'GEMINI_API_KEY not set - deterministic tag strip only' };
  for (let i = 0; i < dirty.length; i += 50) {
    const batch = dirty.slice(i, i + 50);
    try {
      const { data, model } = await geminiPost(apiKey, {
        contents: [{ parts: [{ text:
          'These product descriptions from a customs tariff database contain raw HTML tags and markup artifacts. ' +
          'Clean each one: remove the tags and fix spacing, but keep the exact wording, language, and meaning. ' +
          'Return ONLY a JSON array of strings, same length and order as the input.\n\n' + JSON.stringify(batch) }] }],
        generationConfig: { temperature: 0 },
      });
      const text = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
      const arr = JSON.parse(text.replace(/^```[a-z]*\n?/i, '').replace(/```\s*$/, '').trim());
      if (!Array.isArray(arr) || arr.length !== batch.length) throw new Error('bad shape');
      let accepted = 0;
      batch.forEach((orig, j) => {
        const prop = String(arr[j] || '');
        if (prop && canon(prop) === canon(orig)) { cleaned[orig] = stripTags(prop); accepted++; }
      });
      needAI.push({ model, accepted, of: batch.length });
    } catch (e) {
      needAI.push({ error: e.message, of: batch.length });
    }
  }
  const ai = needAI.reduce((a, b) => a + (b.accepted || 0), 0);
  return { cleaned, ai, note: needAI.map((b) => b.error ? `batch error: ${b.error}` : `${b.accepted}/${b.of} verified (${b.model})`).join('; ') };
}

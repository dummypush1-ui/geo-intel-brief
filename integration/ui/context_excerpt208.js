/* Description prefix only. Full Finder detail is never changed. */
export function descriptionContext(text) {
  const points = Array.from(text);
  const excerpt = points.slice(0, 200).join('');
  return {excerpt, length:points.length, shortened:points.length > 200,
    terms:points.length >= 3 ? [excerpt] : []};
}

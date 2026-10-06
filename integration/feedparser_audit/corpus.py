"""Fixed public synthetic corpus only; never caller XML or URL."""
CORPUS={
'rss':b'''<?xml version="1.0"?><rss version="2.0"><channel><title>Fixture</title><link>https://example.invalid/</link><description>Fixture</description><item><title>Trade tariff news</title><link>https://example.invalid/one</link><description>Tariff &amp; trade</description><pubDate>Fri, 02 Jan 2026 12:00:00 GMT</pubDate></item><item><title>No link</title></item></channel></rss>''',
'atom':'''<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Fixture</title><id>urn:fixture</id><updated>2026-01-02T12:00:00Z</updated><entry><title>தமிழ் trade 😀</title><id>urn:one</id><link href="https://example.invalid/atom"/><updated>2026-01-02T17:30:00+05:30</updated><content type="text">Trade content</content></entry></feed>'''.encode(),
'empty':b'<rss version="2.0"><channel><title>Empty</title></channel></rss>',
'broken_entries':b'<rss version="2.0"><channel><item><title>Trade</title><link>https://example.invalid/broken</link><description>Tariff</description>',
'broken_empty':b'<rss><channel>',
'internal_entity':b'<!DOCTYPE rss [<!ENTITY fixture "Synthetic trade">]><rss version="2.0"><channel><item><title>&fixture;</title><link>https://example.invalid/entity</link><description>Trade</description></item></channel></rss>',
'empty_dates':b'<rss version="2.0"><channel><item><title>Trade</title><link>https://example.invalid/date</link><description></description><pubDate></pubDate></item></channel></rss>'}

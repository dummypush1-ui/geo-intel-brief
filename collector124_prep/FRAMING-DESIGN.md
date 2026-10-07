# Inactive114 framing fix candidate

Add malformed stdlib HTTP header parse defects refusal. Add explicit observed
wire byte count equality to declared Content-Length (stdlib read(size) accepts
short EOF unless checked). Refuse close-delimited identity bodies even if they
look like valid RSS: no framing can distinguish complete data from truncation.
Keep close-delimited gzip/deflate only when existing bounded decoder proves
compression completion. Chunked parser requires zero-sized last chunk; stdlib may accept EOF before final blank line.

9 real stdlib wire parser tests, supplied BytesIO, all network/TLS mocked.
No live fetch or production wiring. Stricter refusal can exclude legitimate
close-delimited identity feeds: source-by-source availability/parity must be
verified before activation. Existing114 code unchanged; this is an inactive staged candidate.
A real combined worker/supervisor needs updated reviewed source pins, plus fixed
process isolation/deployment gates. Current source/header rules still conservative.

Worker byte-identical114. Runner changes only connector pin; package-relative
BASE chooses this fixed124 worker/connector. Test patches/imports use124 package.
Extra bytes beyond Content-Length ignored with single Connection:close request.

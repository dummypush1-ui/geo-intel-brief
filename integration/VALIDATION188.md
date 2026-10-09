# Strict read query boundaries

Known single parameters only for13publicreadroutes and v1 aliases, private tariff
jurisdiction and weekly dates. News q200/categorycountry100/project5/sort20:
oversize inputs rejected, not silently truncated. Duplicate keys rejected even
when values match. Controls/NUL/DEL rejected. Raw query ≤2048bytes. No-parameter
routes reject any args. Existing domain/sort/limit/date validation still applies.
Auth runs first; invalid read requests400before any reader. Valid requests retain
same filters/caps/response semantics. No live flags/access/schema/query operators.
Export-full/export snapshot use their existing stricter parsers, unchanged.

POST related-news/Finder body validation gaps are NOT covered by this read-only
unit. Login/account/legacy app form shapes also remain their own contracts.
This is no claim of uniformly strict validation across the whole repository.

# Copyright (c) 2026 Push. All rights reserved.
"""CSV of filtered supplied snapshot; formula-neutralized, no full-store export."""
import csv
import io
from integration.loaded_news import csv_cell

FIELDS = ('project', 'title', 'source', 'original_country', 'category',
          'published_at', 'collected_at', 'url', 'summary', 'exact_trade_codes',
          'scope', 'tariff_verified', 'snapshot_truncated')


def to_csv(data):
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer, lineterminator='\r\n')
    writer.writerow(FIELDS)
    for row in data['items']:
        values = {**row, 'exact_trade_codes': '; '.join(
            m['system'] + ' ' + m['code'] for m in row['trade_context']),
            'scope': data['scope'], 'tariff_verified': 'false',
            'snapshot_truncated': str(data['truncated']).lower()}
        writer.writerow([csv_cell(values.get(field)) for field in FIELDS])
    return buffer.getvalue()

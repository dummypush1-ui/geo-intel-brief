"""Explicit supplied single-database mapping, not a client or live grant.

No production names guessed: the caller supplies reviewed database/collection
names. Old separate database remains untouched. This only prepares the mapping
for a later reviewed runtime, not a store selection by the old compose().
"""
from dataclasses import dataclass
import re


def label(value):
    return type(value) is str and bool(re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', value))


@dataclass(frozen=True)
class SingleDatabasePlan:
    database: str
    geo_articles: str
    other_articles: str

    def __post_init__(self):
        if not all(label(v) for v in (self.database, self.geo_articles, self.other_articles)):
            raise ValueError('Exact explicit database and collection labels required')
        if self.geo_articles == self.other_articles:
            raise ValueError('Separate project article collections required')

    def fake_store_map(self, supplied_database):
        # Plain supplied mapping only. No arbitrary indexer/client hooks.
        if type(supplied_database) is not dict or any(type(k) is not str for k in supplied_database):
            raise ValueError('Plain supplied database map required')
        if set(supplied_database) != {self.geo_articles, self.other_articles}:
            raise ValueError('Exact reviewed collection mapping required')
        if any(type(v) is not dict for v in supplied_database.values()):
            raise ValueError('Plain fake collection maps required')
        if supplied_database[self.geo_articles] is supplied_database[self.other_articles]:
            raise ValueError('Distinct fake collection objects required')
        return {'geo': supplied_database[self.geo_articles], 'brics': supplied_database[self.other_articles]}

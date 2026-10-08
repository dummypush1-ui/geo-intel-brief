"""ADDITIVE feeds, NOT wired. Same (name, url, credibility) shape as DEFAULT_FEEDS.
Cut to 8 after the terms review (2026-10-08, feed-terms-review.md). URLs verified
live 2026-10-08 (HTTP 200, no redirect, <1MiB, parses). Strict publication_date()
re-check is pending date151.

Attribution is REQUIRED for every feed here (see EXTRA_FEED_ATTRIBUTION and
ATTRIBUTION-PLAN.md). Wiring must not land without displaying it.
"""

EXTRA_VERIFIED_FEEDS = [
    ('European Commission Press Corner', 'https://ec.europa.eu/commission/presscorner/api/rss?language=en', 'HIGH'),
    ('Council of the EU Press', 'https://www.consilium.europa.eu/en/rss/pressreleases.ashx', 'HIGH'),
    ('UK Dept for Business and Trade', 'https://www.gov.uk/government/organisations/department-for-business-and-trade.atom', 'HIGH'),
    ('UK FCDO', 'https://www.gov.uk/government/organisations/foreign-commonwealth-development-office.atom', 'HIGH'),
    ('US Federal Reserve Press', 'https://www.federalreserve.gov/feeds/press_all.xml', 'HIGH'),
    ('ECB Press', 'https://www.ecb.europa.eu/rss/press.html', 'HIGH'),
    ('WTO Latest News', 'https://www.wto.org/library/rss/latest_news_e.xml', 'HIGH'),
    ('BIS Publications', 'https://www.bis.org/doclist/bis_fsi_publs.rss', 'HIGH'),
]

EXTRA_FEED_TAGS = {  # url -> (region, topic, kind)
    'https://ec.europa.eu/commission/presscorner/api/rss?language=en': ('europe', 'trade-policy', 'government'),
    'https://www.consilium.europa.eu/en/rss/pressreleases.ashx': ('europe', 'sanctions-policy', 'government'),
    'https://www.gov.uk/government/organisations/department-for-business-and-trade.atom': ('europe', 'trade', 'government'),
    'https://www.gov.uk/government/organisations/foreign-commonwealth-development-office.atom': ('europe', 'geopolitics-sanctions', 'government'),
    'https://www.federalreserve.gov/feeds/press_all.xml': ('americas', 'economy', 'government'),
    'https://www.ecb.europa.eu/rss/press.html': ('europe', 'economy', 'government'),
    'https://www.wto.org/library/rss/latest_news_e.xml': ('global', 'trade', 'multilateral'),
    'https://www.bis.org/doclist/bis_fsi_publs.rss': ('global', 'economy', 'multilateral'),
}

# Shown next to every article from these sources in the data view (not in code credits).
# 'line' is the exact text; 'licence' + 'licence_url' are shown where a licence applies.
EXTRA_FEED_ATTRIBUTION = {
    'https://ec.europa.eu/commission/presscorner/api/rss?language=en': {
        'provider': 'European Commission', 'source': 'Press Corner',
        'licence': 'CC BY 4.0', 'licence_url': 'https://creativecommons.org/licenses/by/4.0/',
        'terms_url': 'https://commission.europa.eu/legal-notice_en',
        'line': 'Source: European Commission, Press Corner. CC BY 4.0.'},
    'https://www.consilium.europa.eu/en/rss/pressreleases.ashx': {
        'provider': 'Council of the European Union', 'source': 'Press releases',
        'licence': None, 'licence_url': None,
        'terms_url': 'https://www.consilium.europa.eu/en/about-site/copyright/',
        'line': 'Source: Council of the European Union, press releases.'},
    'https://www.gov.uk/government/organisations/department-for-business-and-trade.atom': {
        'provider': 'UK Department for Business and Trade', 'source': 'GOV.UK',
        'licence': 'Open Government Licence v3.0', 'licence_url': 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/',
        'terms_url': 'https://www.gov.uk/help/terms-conditions',
        'line': 'Source: UK Department for Business and Trade, GOV.UK. Contains public sector information licensed under the Open Government Licence v3.0.'},
    'https://www.gov.uk/government/organisations/foreign-commonwealth-development-office.atom': {
        'provider': 'UK Foreign, Commonwealth & Development Office', 'source': 'GOV.UK',
        'licence': 'Open Government Licence v3.0', 'licence_url': 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/',
        'terms_url': 'https://www.gov.uk/help/terms-conditions',
        'line': 'Source: UK Foreign, Commonwealth & Development Office, GOV.UK. Contains public sector information licensed under the Open Government Licence v3.0.'},
    'https://www.federalreserve.gov/feeds/press_all.xml': {
        'provider': 'Board of Governors of the Federal Reserve System', 'source': 'Press releases',
        'licence': None, 'licence_url': None,
        'terms_url': 'https://www.federalreserve.gov/disclaimer.htm',
        'line': 'Source: Board of Governors of the Federal Reserve System, press releases.'},
    'https://www.ecb.europa.eu/rss/press.html': {
        'provider': 'European Central Bank', 'source': 'Press',
        'licence': None, 'licence_url': None,
        'terms_url': 'https://www.ecb.europa.eu/services/disclaimer/html/index.en.html',
        'line': 'Source: European Central Bank.'},
    'https://www.wto.org/library/rss/latest_news_e.xml': {
        'provider': 'World Trade Organization', 'source': 'Latest news',
        'licence': None, 'licence_url': None,
        'terms_url': 'https://www.wto.org/english/info_e/copyrights_permissions_e.htm',
        'line': 'Source: World Trade Organization, wto.org. Non-commercial use.'},
    'https://www.bis.org/doclist/bis_fsi_publs.rss': {
        'provider': 'Bank for International Settlements', 'source': 'BIS and FSI publications',
        'licence': None, 'licence_url': None,
        'terms_url': 'https://www.bis.org/about/terms-conditions',
        'line': 'Source: Bank for International Settlements, bis.org. Non-commercial use.'},
}

# Ingest rules for wiring (inert data; enforced and tested only in the wiring phase).
# ECB: named-author speeches and interviews appear in this feed, and the ECB terms
# restrict reprinting author-named documents. Keep headline, link and date only.
EXTRA_FEED_INGEST_RULES = {
    'https://www.ecb.europa.eu/rss/press.html': {'drop_fields': ('summary', 'body', 'full_text')},
}

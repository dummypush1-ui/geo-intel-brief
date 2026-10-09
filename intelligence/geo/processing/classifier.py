from integration.text_matching.matcher import contains, country_contains
import re
from dateutil import parser as dateparser
from datetime import datetime, timezone
from integration.publication_dates.policy import publication_date

from integration.html_text209 import strip_html_once


def strip_html(text):
    """Plain summary text, one entity pass only; no stored-data rewrite."""
    return strip_html_once(text)


RULES = {
    "GEOPOLITICS": ["geopolit", "diplomatic", "foreign policy", "war", "conflict", "ceasefire", "military", "alliance", "border", "nato", "brics", "sco"],
    "TRADE": ["tariff", "trade war", "trade agreement", "export control", "import restriction", "export restriction", "customs", "supply chain", "critical mineral", "semiconductor", "trade dispute", "notification", "circular", "gazette", "trade order", "fta", "trade policy", "import ban", "export ban", "trade deal"],
    "SANCTIONS": ["sanction", "embargo", "asset freeze", "designated entity", "secondary sanctions", "export ban", "financial restriction", "circular", "notification", "sanctions list", "ofac", "denied party", "blacklist"],
    "RISK": ["risk", "escalation", "crisis", "instability", "shortage", "disruption", "shock", "volatility", "chokepoint"],
    "CONFERENCE": ["summit", "conference", "forum", "ministerial", "assembly", "meeting", "g20", "brics", "sco", "wto", "imf", "world bank"],
    "RESEARCH": ["working paper", "research paper", "policy brief", "preprint", "white paper", "arxiv", "ssrn", "nber", "peer-reviewed", "journal article"],
}
HIGH_IMPACT = ["breaking", "new sanctions", "sanctions package", "invasion", "ceasefire", "tariff", "export ban", "trade war", "nuclear", "military operation", "emergency"]
COUNTRIES = ["United States","China","India","Russia","Ukraine","Iran","Israel","Türkiye","Turkey","Japan","South Korea","North Korea","Germany","France","United Kingdom","Saudi Arabia","United Arab Emirates","Canada","Mexico","Taiwan","Pakistan","Australia","Indonesia","Brazil","South Africa","European Union"]

def classify(title, summary):
    text = f"{title} {summary}".lower()
    scores = {k: sum(1 for w in words if contains(text, w)) for k, words in RULES.items()}
    category = max(scores, key=scores.get) if max(scores.values()) else "GENERAL"
    score = min(100, sum(scores.values()) * 2 + sum(5 for w in HIGH_IMPACT if contains(text, w)))
    level = "CRITICAL" if score >= 30 else "HIGH" if score >= 20 else "MODERATE" if score >= 10 else "LOW"
    country = next((c for c in COUNTRIES if country_contains(text, c)), "")
    return category, score, level, country

def parse_date(value):
    """Compatibility API: unknown/naive/incomplete/future dates are not fresh."""
    return publication_date(value, datetime.now(timezone.utc))[0]

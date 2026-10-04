# Copyright (c) 2026 Push
"""Geonews digest / alerts / weekly / chat digests, ported as pure modules.

Delivery is OFF by default and only possible with explicit enabled=True."""
from .model import (Settings, normalise_all, normalise_article, unemailed_articles, critical_since,
                    weekly_top_articles, category_counts, top_countries, upcoming_events)
from .render import (build_digest, build_alert, build_weekly, build_telegram_message,
                     build_whatsapp_message, digest_subject, alert_subject, should_send_digest)
from .delivery import (DeliveryDisabled, DeliveryError, Outcome, smtp_sender, telegram_sender,
                       whatsapp_sender, deliver_digest, deliver_critical_alert, deliver_weekly,
                       deliver_chat, parse_mark_request)

__all__ = [n for n in dir() if not n.startswith("_")]

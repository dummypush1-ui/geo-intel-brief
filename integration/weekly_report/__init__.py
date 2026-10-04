# Copyright (c) 2026 Push
"""Offline weekly intelligence PDF generator (pure functions, no I/O)."""
from .report import (
    NEWS_FIELDS,
    TARIFF_FIELDS,
    MAX_NEWS_INPUT,
    MAX_TARIFF_INPUT,
    sanitize_news_rows,
    sanitize_tariff_records,
    summarize_week,
    MIN_PERIOD,
    MAX_PERIOD,
)
from ._render import render_pdf, build_weekly_report

__all__ = [
    "NEWS_FIELDS", "TARIFF_FIELDS", "MAX_NEWS_INPUT", "MAX_TARIFF_INPUT",
    "sanitize_news_rows", "sanitize_tariff_records", "summarize_week",
    "render_pdf", "build_weekly_report", "MIN_PERIOD", "MAX_PERIOD",
]

# Copyright (c) 2026 Push
"""Per-user saved channels and watchlist (extras only).

The compulsory Republic row is code-defined by the caller, never stored, never removable.
Validators default to the server-side mirrors in validators.py and can be replaced."""
import json

from . import validators as V

REPUBLIC = {"name": "Republic", "video": "jndNegut8RY"}


class SettingsPolicy:
    def __init__(self, compulsory_channels=(REPUBLIC,), channel_validator=V.channel_validator,
                 watch_validator=V.watch_validator, max_channels=V.MAX_EXTRA_CHANNELS,
                 max_watch=V.MAX_WATCH, watch_allowed=None):
        self.compulsory = tuple(dict(c) for c in compulsory_channels)
        self.channel_validator, self.watch_validator = channel_validator, watch_validator
        self.max_channels, self.max_watch = max_channels, max_watch
        self.watch_allowed = None if watch_allowed is None else frozenset(watch_allowed)

    def clean(self, channels, watchlist):
        """Return (channels, watchlist) sanitized or raise ValueError. Input is never mutated."""
        if not isinstance(channels, (list, tuple)) or not isinstance(watchlist, (list, tuple)):
            raise ValueError("shape")
        if len(channels) > self.max_channels + len(self.compulsory) or len(watchlist) > self.max_watch:
            raise ValueError("too_many")
        reserved_v = {c["video"] for c in self.compulsory}
        reserved_n = {V.fold(c["name"]) for c in self.compulsory}
        out_c, seen = [], set()
        for it in channels:
            c = self.channel_validator(it)
            if c["video"] in reserved_v:
                continue                      # legacy duplicate of the mandatory row: dropped
            if V.fold(c["name"]) in reserved_n:
                raise ValueError("reserved_name")
            if c["video"] in seen:
                raise ValueError("duplicate")
            seen.add(c["video"])
            out_c.append(c)
        if len(out_c) > self.max_channels:
            raise ValueError("too_many")
        out_w, seen = [], set()
        for it in watchlist:
            w = self.watch_validator(it)
            if w in seen:
                raise ValueError("duplicate")
            if self.watch_allowed is not None and w not in self.watch_allowed:
                raise ValueError("unknown_label")
            seen.add(w)
            out_w.append(w)
        if len(json.dumps(out_c, ensure_ascii=False)) > V.CHANNEL_JSON_MAX or \
           len(json.dumps(out_w, ensure_ascii=False)) > V.WATCH_JSON_MAX:
            raise ValueError("too_large")
        return out_c, out_w

    def view(self, doc):
        doc = doc or {"version": 0, "channels": [], "watchlist": []}
        return {"version": doc["version"],
                "channels": [dict(c, compulsory=True) for c in self.compulsory] + [dict(c) for c in doc["channels"]],
                "watchlist": list(doc["watchlist"])}

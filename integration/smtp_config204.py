"""Inert, closed legacy-profile settings. No caller or sender is activated."""
import copy
import ipaddress
import re

from integration.smtp_policy import SMTPPolicyRefused, transport_plan


class SMTPConfigRefused(ValueError):
    """Static errors never include supplied keys or values."""


_DEFAULTS = {'geo': ('implicit_tls', 465), 'brics': ('starttls', 587)}
_KEYS = frozenset(('profile', 'host', 'port', 'mode', 'timeout'))
_LABEL = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', re.ASCII)
_PORT = re.compile(r'[1-9][0-9]{0,4}', re.ASCII)


def _refuse():
    raise SMTPConfigRefused('SMTP configuration refused')


def _hostname(value):
    if type(value) is not str or not 1 <= len(value) <= 253:
        _refuse()
    if any(_LABEL.fullmatch(label) is None for label in value.split('.')):
        _refuse()
    try:
        ipaddress.ip_address(value)
    except ValueError:
        pass
    else:
        _refuse()
    # Also refuse noncanonical numeric IPv4 spellings (e.g. leading zeros).
    if all(label.isdigit() for label in value.split('.')):
        _refuse()
    return value


def _port(value):
    if type(value) is int:
        result = value
    elif type(value) is str and _PORT.fullmatch(value) is not None:
        result = int(value)
    else:
        _refuse()
    if not 1 <= result <= 65535:
        _refuse()
    return result


def profile_plan(settings):
    """Validate an exact dict of scalar settings and return independent plain data.

    No secrets are accepted. Absence means a missing key, not None or empty text.
    Host is required. Defaults apply only when BOTH mode and port are absent.
    """
    if type(settings) is not dict:
        _refuse()
    if any(type(key) is not str or key not in _KEYS for key in settings):
        _refuse()
    profile = settings.get('profile')
    if type(profile) is not str or profile not in _DEFAULTS:
        _refuse()
    host = _hostname(settings.get('host'))
    timeout = settings.get('timeout', 30)
    if type(timeout) is not int or not 1 <= timeout <= 30:
        _refuse()
    explicit = 'port' in settings
    if explicit != ('mode' in settings):
        _refuse()
    if explicit:
        port = _port(settings['port'])
        mode = settings['mode']
    else:
        mode, port = _DEFAULTS[profile]
    if type(mode) is not str or mode not in ('implicit_tls', 'starttls'):
        _refuse()
    # All accepted inputs are exact immutable built-ins before copying.
    snapshot = copy.deepcopy(settings)
    try:
        policy = transport_plan(snapshot['profile'], mode, port, timeout)
    except SMTPPolicyRefused:
        _refuse()
    return {
        'settings': {'profile': profile, 'host': host, 'port': port,
                     'mode': mode, 'timeout': timeout},
        'settings_source': 'explicit_pair' if explicit else 'pinned_profile_default',
        'policy': policy,
        'starttls_required': mode == 'starttls',
        'caller_wired': False,
        'smtp_fallback_held': True,
    }


def binding_data(settings):
    """Return scalar future sender arguments only, never a sender or context."""
    selected = profile_plan(settings)['settings']
    return {'profile': selected['profile'], 'host': selected['host'],
            'port': selected['port'], 'tls_mode': selected['mode'],
            'timeout': selected['timeout']}

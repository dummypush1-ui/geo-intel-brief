"""Unselected closure-construction caller for 204 -> 174. No send on build.
A prepared callable is a REAL send capability, never selected by this module.
"""
import re

_FIELDS = {'settings', 'user', 'password', 'mail_from', 'mail_to'}
_EMAIL = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', re.ASCII)


class CallerRefused(ValueError):
    pass


def _refuse():
    raise CallerRefused('SMTP caller refused') from None


def _ascii(value, cap, low):
    if type(value) is not str or not 1 <= len(value) <= cap or any(not low <= ord(c) <= 126 for c in value):
        _refuse()


def _address(value):
    if type(value) is not str or not 1 <= len(value) <= 254 or _EMAIL.fullmatch(value) is None:
        _refuse()


def build_sender(*, enabled=False, **arguments):
    """Return (callable-or-None, static secret-free metadata).

    OFF touches no supplied arguments. ON constructs a real wrapped 174 send
    capability, but does not select SMTP or send. Subject/body stay 174-owned.
    Missing/extra arguments refuse only when enabled. No env/client/ledger.
    """
    if type(enabled) is not bool:
        _refuse()
    if not enabled:
        return None, {'selected': False, 'prepared_not_sent': False, 'state': 'disabled',
                      'selected_rail': 'apps_script', 'smtp_fallback_held': True}
    if set(arguments) != _FIELDS:
        _refuse()
    settings = arguments['settings']
    if type(settings) is not dict:
        _refuse()
    user, password = arguments['user'], arguments['password']
    _ascii(user, 320, 33)
    _ascii(password, 1024, 32)  # Refuse non-ASCII, never alter credentials.
    sender, recipients = arguments['mail_from'], arguments['mail_to']
    _address(sender)
    if type(recipients) is not list or not 1 <= len(recipients) <= 20:
        _refuse()
    for recipient in recipients:
        _address(recipient)
    if len({value.lower() for value in recipients}) != len(recipients):
        _refuse()
    # Reject key/value subclasses before any adapter lookup/copy/caller hooks.
    if any(type(k) is not str for k in settings) or any(type(v) not in (str, int) for v in settings.values()):
        _refuse()
    failed = False
    try:
        from integration.smtp_config204 import binding_data
        from integration.geonews_digest.delivery import smtp_sender
        binding = binding_data(dict(settings))
        prepared = smtp_sender(enabled=True, user=user, password=password,
                               mail_from=sender, mail_to=list(recipients), **binding)
        if not callable(prepared):
            failed = True
    except Exception:
        failed = True
    # Raise OUTSIDE except: even __context__ cannot retain upstream secrets.
    if failed:
        _refuse()

    def send(subject, html_body):
        # No validation or retry policy added here. Preserve 174-owned inputs,
        # but hide upstream errors and exception context from future caller.
        failed = False
        try:
            result = prepared(subject, html_body)
        except Exception:
            failed = True
        if failed:
            _refuse()
        return result  # None is NOT recipient acceptance/delivery proof.

    return send, {'selected': False, 'prepared_not_sent': True,
                  'state': 'prepared_capability_not_selected',
                  'selected_rail': 'apps_script', 'smtp_fallback_held': True}

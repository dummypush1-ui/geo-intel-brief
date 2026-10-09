import ast
import copy
import inspect
import socket
import unittest
from unittest.mock import patch

from integration import smtp_config204 as adapter
from integration.geonews_digest.delivery import DeliveryError, smtp_sender


class SMTP204(unittest.TestCase):
    def config(self, **extra):
        return dict(profile='geo', host='smtp.example.org', **extra)

    def refuse(self, settings):
        with self.assertRaises(adapter.SMTPConfigRefused) as caught:
            adapter.profile_plan(settings)
        self.assertEqual(str(caught.exception), 'SMTP configuration refused')

    def test_full_mixed_settings_table_and_pinned_defaults(self):
        for profile, mode, port in [('geo', 'implicit_tls', 465), ('brics', 'starttls', 587)]:
            base = {'profile': profile, 'host': 'smtp.gmail.com'}
            default = adapter.profile_plan(base)
            self.assertEqual(default['settings'], dict(base, port=port, mode=mode, timeout=30))
            self.assertEqual(default['settings_source'], 'pinned_profile_default')
            for extra in [{'port': port}, {'mode': mode}]:
                self.refuse(dict(base, **extra))
            explicit = adapter.profile_plan(dict(base, port=port, mode=mode))
            self.assertEqual(explicit['settings'], default['settings'])
            self.assertEqual(explicit['settings_source'], 'explicit_pair')
            for other_mode, other_port in [('implicit_tls', 465), ('starttls', 587)]:
                self.assertEqual(adapter.profile_plan(dict(base, mode=other_mode, port=other_port))['settings']['port'], other_port)
            for bad_mode, bad_port in [('implicit_tls', 587), ('starttls', 465)]:
                self.refuse(dict(base, mode=bad_mode, port=bad_port))

    def test_strict_ports(self):
        for value in [465, '465']:
            self.assertEqual(adapter.profile_plan(self.config(port=value, mode='implicit_tls'))['settings']['port'], 465)
        for value in [True, False, 465.0, '465 ', '0465', '４６５', '+465', '-465', '', 0, 65536, '65536', None, [], {}]:
            self.refuse(self.config(port=value, mode='implicit_tls'))

    def test_exact_modes_and_no_weaker_options(self):
        for mode in ['STARTTLS', 'tls', 'starttls ', 'plaintext', 'optional', None, True, []]:
            self.refuse(self.config(port=587, mode=mode))
        for mode, port in [('starttls', 587), ('implicit_tls', 465)]:
            plan = adapter.profile_plan(self.config(mode=mode, port=port))
            self.assertEqual(plan['starttls_required'], mode == 'starttls')
            self.assertTrue(plan['policy']['tls_hostname_verified'])
            self.assertFalse(plan['policy']['plaintext_fallback'])
            self.assertFalse(plan['policy']['runtime_activation'])
            self.assertTrue(plan['smtp_fallback_held'])
            self.assertFalse(plan['caller_wired'])
            self.assertEqual(set(plan['settings']), {'profile', 'host', 'port', 'mode', 'timeout'})

    def test_required_starttls_fails_before_credentials(self):
        import smtplib
        with patch('integration.geonews_digest.delivery.smtplib.SMTP') as plain:
            server = plain.return_value.__enter__.return_value
            server.starttls.side_effect = smtplib.SMTPNotSupportedError('not offered')
            kwargs = adapter.binding_data(self.config(port=587, mode='starttls'))
            sender = smtp_sender(enabled=True, user='u', password='p', mail_from='a@example.org', mail_to='b@example.org', **kwargs)
            with self.assertRaises(DeliveryError):
                sender('subject', 'body')
            server.login.assert_not_called()
            server.sendmail.assert_not_called()

    def test_host_validation_and_caps(self):
        for host in ['localhost', 'smtp.example.org', 'SMTP.example.org', 'a-b.example', 'a' * 63 + '.org']:
            self.assertEqual(adapter.profile_plan(dict(profile='geo', host=host))['settings']['host'], host)
        for host in ['', None, True, [], 'https://smtp.example.org', 'u@smtp.example.org', 'smtp.example.org:465', 'smtp.example.org/x', ' smtp.example.org', 'smtp.example.org\n', 'smtp.\x00org', 'smtp..org', 'smtp.org.', '-smtp.org', 'smtp-.org', 'smtp_org', 'smtр.org', '127.0.0.1', '0127.0.0.1', '::1', '[::1]', '123', 'a' * 64 + '.org', '.'.join(['a'*63]*4)]:
            self.refuse(dict(profile='geo', host=host))

    def test_timeout_exact_int_bounds(self):
        for timeout in [1, 30]:
            self.assertEqual(adapter.profile_plan(self.config(timeout=timeout))['settings']['timeout'], timeout)
        for timeout in [True, False, 0, 31, 1.0, '30', None, float('nan'), float('inf')]:
            self.refuse(self.config(timeout=timeout))

    def test_closed_inputs_and_canary_no_echo(self):
        canary = 'CANARY-SECRET-204'
        for key in ['password', 'username', 'token', 'from', 'env', 'enabled', 'verify', 'starttls_optional', canary]:
            self.refuse(dict(self.config(), **{key: canary}))
        for value in [canary, None, True, [], {'token': canary}]:
            self.refuse({'profile': value, 'host': 'smtp.example.org'})
        self.refuse({1: canary})
        for settings in [None, [], (), 'geo']:
            self.refuse(settings)
        with patch('builtins.print') as printing:
            self.refuse({'profile': canary, 'host': 'smtp.example.org'})
            printing.assert_not_called()

    def test_deep_copy_and_plain_binding(self):
        original = self.config(mode='starttls', port='587', timeout=12)
        before = copy.deepcopy(original)
        with patch.object(adapter.copy, 'deepcopy', wraps=copy.deepcopy) as copying:
            plan = adapter.profile_plan(original)
            copying.assert_called_once_with(original)
        self.assertEqual(original, before)
        original['host'] = 'changed.example'
        self.assertEqual(plan['settings']['host'], 'smtp.example.org')
        plan['settings']['host'] = 'output.example'
        self.assertEqual(original['host'], 'changed.example')
        data = adapter.binding_data(before)
        self.assertEqual(data, dict(profile='geo', host='smtp.example.org', port=587, tls_mode='starttls', timeout=12))
        self.assertTrue(all(type(v) in (str, int) for v in data.values()))

    def test_ast_and_network_inertness(self):
        tree = ast.parse(inspect.getsource(adapter))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module)
        self.assertEqual(imports, {'copy', 'ipaddress', 're', 'integration.smtp_policy'})
        self.assertNotIn('environ', {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)})
        with patch.object(socket, 'socket', side_effect=AssertionError('network')), patch.object(socket, 'getaddrinfo', side_effect=AssertionError('dns')):
            import importlib
            importlib.reload(adapter)
            adapter.profile_plan(self.config())
            adapter.binding_data(self.config())


if __name__ == '__main__':
    unittest.main()

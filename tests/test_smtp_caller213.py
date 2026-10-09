import ast
import importlib
import inspect
import os
import socket
import ssl
import smtplib
import unittest
from pathlib import Path
from unittest.mock import patch
from integration import smtp_caller213 as m


class Tests(unittest.TestCase):
    def arguments(self,profile='geo',**extra):
        value={'settings':{'profile':profile,'host':'smtp.example.org'}, 'user':'user',
               'password':'SECRET213', 'mail_from':'a@example.org','mail_to':['b@example.org']}
        value.update(extra);return value
    def refuse(self,args):
        with self.assertRaises(m.CallerRefused)as caught:m.build_sender(enabled=True,**args)
        self.clean(caught.exception)
    def clean(self,error):
        self.assertEqual(str(error),'SMTP caller refused')
        self.assertNotIn('SECRET213',repr(error));self.assertIsNone(error.__cause__);self.assertIsNone(error.__context__)
    def test_default_profiles_and_explicit_pairs_exact_transport(self):
        for profile in ['geo','brics']:
            for pair in [None,('implicit_tls',465),('starttls',587)]:
                args=self.arguments(profile)
                mode,port=pair or (('implicit_tls',465)if profile=='geo'else('starttls',587))
                if pair:args['settings'].update(mode=mode,port=str(port),timeout=12)
                with patch('integration.geonews_digest.delivery.smtplib.SMTP_SSL')as secure,patch('integration.geonews_digest.delivery.smtplib.SMTP')as start:
                    sender,meta=m.build_sender(enabled=True,**args)
                    secure.assert_not_called();start.assert_not_called()
                    self.assertFalse(meta['selected']);self.assertTrue(meta['prepared_not_sent']);self.assertEqual(meta['selected_rail'],'apps_script')
                    self.assertNotIn('SECRET213',repr(sender));self.assertNotIn('SECRET213',repr(meta))
                    result=sender('subject','body');self.assertIsNone(result)
                    if mode=='implicit_tls':
                        start.assert_not_called();self.assertEqual(secure.call_args.args,('smtp.example.org',465))
                        context=secure.call_args.kwargs['context'];server=secure.return_value.__enter__.return_value
                        self.assertEqual([c[0]for c in server.method_calls],['login','sendmail'])
                    else:
                        secure.assert_not_called();self.assertEqual(start.call_args.args,('smtp.example.org',587))
                        server=start.return_value.__enter__.return_value;context=server.starttls.call_args.kwargs['context']
                        self.assertEqual([c[0]for c in server.method_calls],['ehlo','starttls','ehlo','login','sendmail'])
                    self.assertIsInstance(context,ssl.SSLContext);self.assertTrue(context.check_hostname);self.assertEqual(context.verify_mode,ssl.CERT_REQUIRED)
                    called=secure if mode=='implicit_tls'else start
                    self.assertEqual(called.call_args.kwargs['timeout'],12 if pair else 30)
                    server.login.assert_called_once_with('user','SECRET213')
                    self.assertEqual(server.sendmail.call_args.args[:2],('a@example.org',['b@example.org']))

    def test_missing_starttls_before_login_no_fallback(self):
        for error in [smtplib.SMTPNotSupportedError('SECRET213'),smtplib.SMTPException('SECRET213')]:
            with patch('integration.geonews_digest.delivery.smtplib.SMTP')as plain,patch('integration.geonews_digest.delivery.smtplib.SMTP_SSL')as secure:
                server=plain.return_value.__enter__.return_value;server.starttls.side_effect=error
                sender,_=m.build_sender(enabled=True,**self.arguments('brics'))
                with self.assertRaises(m.CallerRefused)as caught:sender('s','b')
                self.clean(caught.exception);server.login.assert_not_called();server.sendmail.assert_not_called();secure.assert_not_called()

    def test_mismatched_pairs_refused_before_sender_factory(self):
        with patch('integration.geonews_digest.delivery.smtp_sender',side_effect=AssertionError('factory'))as factory:
            for mode,port in [('implicit_tls',587),('starttls',465),('none',25)]:
                args=self.arguments();args['settings'].update(mode=mode,port=port);self.refuse(args)
            factory.assert_not_called()

    def test_ascii_credentials_construction_caps_nonascii_never174(self):
        with patch('integration.geonews_digest.delivery.smtp_sender')as factory:
            for field,values in [('user',['', 'x'*321,'with space','üSECRET213','x\n',None]),('password',['','x'*1025,'SECRET213界','\x00','\n','\x7f',None])]:
                for value in values:self.refuse(self.arguments(**{field:value}))
            factory.assert_not_called()
        with patch('integration.geonews_digest.delivery.smtp_sender',return_value=lambda s,b:None)as factory:
            m.build_sender(enabled=True,**self.arguments(user='x'*320,password=' '*1024))
            self.assertEqual(factory.call_args.kwargs['password'],' '*1024)

    def test_address_fullmatch_ascii_and_casefold_duplicate(self):
        for address in ['a@b.co\n',' a@b.co','a\t@b.co','a@b.co,b@b.co','a@b.cö','x'*249+'@b.com','',None]:
            self.refuse(self.arguments(mail_from=address));self.refuse(self.arguments(mail_to=[address]))
        for recipients in [[],['b@example.org']*21,['a@B.co','a@b.co'],'a@b.co',('a@b.co',)]:self.refuse(self.arguments(mail_to=recipients))
        with patch('integration.geonews_digest.delivery.smtp_sender',return_value=lambda s,b:None):
            m.build_sender(enabled=True,**self.arguments(mail_from='x'*248+'@b.com',mail_to=['x'*248+'@b.com']))

    def test_exact_types_extra_missing_keys(self):
        class S(str):pass
        class D(dict):pass
        class L(list):pass
        for args in [self.arguments(user=S('user')),self.arguments(password=S('SECRET213')),self.arguments(mail_from=S('a@b.co')),self.arguments(mail_to=L(['a@b.co'])),self.arguments(mail_to=[S('a@b.co')]),self.arguments(settings=D(profile='geo',host='smtp.example.org'))]:self.refuse(args)
        for key in ['profile','host']:
            args=self.arguments();args['settings'][key]=S(args['settings'][key]);self.refuse(args)
        args=self.arguments();args['settings']['extra']='SECRET213';self.refuse(args)
        self.refuse(dict(self.arguments(),extra='SECRET213'))
        for key in self.arguments():
            args=self.arguments();del args[key];self.refuse(args)
        for value in [1,None,'true']:
            with self.assertRaises(m.CallerRefused)as caught:m.build_sender(enabled=value)
            self.clean(caught.exception)

    def test_fixed_errors_no_chain_for_adapter_factory_and_send(self):
        args=self.arguments()
        for target in ['integration.smtp_config204.binding_data','integration.geonews_digest.delivery.smtp_sender']:
            with patch(target,side_effect=RuntimeError('SECRET213')):self.refuse(args)
        with patch('integration.geonews_digest.delivery.smtp_sender',return_value=lambda s,b:(_ for _ in ()).throw(UnicodeError('SECRET213'))):
            sender,metadata=m.build_sender(enabled=True,**args)
            self.assertNotIn('SECRET213',repr(metadata));self.assertNotIn('SECRET213',repr(sender))
            with self.assertRaises(m.CallerRefused)as caught:sender('s','b')
            self.clean(caught.exception)

    def test_off_before_import_and_hostile_objects(self):
        class Hostile:
            def __getattribute__(self,k):raise AssertionError('touch')
            def __iter__(self):raise AssertionError('touch')
            def __repr__(self):raise AssertionError('touch')
        with patch('builtins.__import__',side_effect=AssertionError('import')):
            sender,metadata=m.build_sender(settings=Hostile(),user=Hostile(),password=Hostile(),mail_from=Hostile(),mail_to=Hostile(),unknown=Hostile())
        self.assertIsNone(sender);self.assertEqual(metadata,{'selected':False,'prepared_not_sent':False,'state':'disabled','selected_rail':'apps_script','smtp_fallback_held':True})

    def test_import_and_construction_inert_copy_no_env_reads(self):
        args=self.arguments();before=repr(args)
        with patch.object(socket,'socket',side_effect=AssertionError('network')),patch.object(socket,'getaddrinfo',side_effect=AssertionError('dns')),patch.object(ssl,'create_default_context',side_effect=AssertionError('context')),patch.dict(os.environ,{},clear=True):
            importlib.reload(m)
            sender,_=m.build_sender(enabled=True,**args)
            self.assertTrue(callable(sender));self.assertEqual(repr(args),before)
        args['mail_to'].clear();args['settings']['host']='changed.example.org'
        with patch('integration.geonews_digest.delivery.smtplib.SMTP_SSL')as secure:
            sender('s','b');self.assertEqual(secure.call_args.args,('smtp.example.org',465));self.assertEqual(secure.return_value.__enter__.return_value.sendmail.call_args.args[1],['b@example.org'])
        tree=ast.parse(inspect.getsource(m));self.assertNotIn('environ',{n.attr for n in ast.walk(tree)if isinstance(n,ast.Attribute)})

    def test_partial_recipient_refusal_none_and_quit_error_unknown(self):
        with patch('integration.geonews_digest.delivery.smtplib.SMTP_SSL')as secure:
            server=secure.return_value.__enter__.return_value;server.sendmail.return_value={'b@example.org':(550,b'refused')}
            sender,_=m.build_sender(enabled=True,**self.arguments());self.assertIsNone(sender('s','b'))
            secure.return_value.__exit__.side_effect=smtplib.SMTPException('SECRET213 after accepted')
            with self.assertRaises(m.CallerRefused)as caught:sender('s','b')
            self.clean(caught.exception);self.assertEqual(server.sendmail.call_count,2)

    def test_no_current_activation_import_edge(self):
        root=Path(__file__).resolve().parents[1]
        for path in root.rglob('*.py'):
            if '__pycache__'in path.parts or path.name=='test_smtp_caller213.py':continue
            tree=ast.parse(path.read_bytes())
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):self.assertFalse(any('smtp_caller213'in alias.name for alias in node.names),str(path))
                elif isinstance(node,ast.ImportFrom):
                    self.assertFalse('smtp_caller213'in (node.module or '')or any(alias.name=='smtp_caller213'for alias in node.names),str(path))


if __name__=='__main__':unittest.main()

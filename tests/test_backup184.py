import unittest,ast
from pathlib import Path
from integration.edge_guard import EdgeGuard
class Tests(unittest.TestCase):
 def test_default_off_requested_not_capability(self):
  tree=ast.parse(Path('intelligence/geo/config.py').read_text());n=next(n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='ENABLE_TELEGRAM_BACKUP'for t in n.targets));calls=[x for x in ast.walk(n)if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr=='getenv'];self.assertEqual(ast.literal_eval(calls[0].args[1]),'false')
  cap=next(n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='TELEGRAM_BACKUP_CAPABILITY'for t in n.targets));self.assertEqual(ast.literal_eval(cap.value),'held_pending_durable_adapter')
 def test_flood_refusal_not_new_ban(self):
  now=[0];g=EdgeGuard(clock=lambda:now[0],rate_limit=2,window_seconds=10);self.assertTrue(g.allow_rate('fixture'));self.assertTrue(g.allow_rate('fixture'));self.assertFalse(g.allow_rate('fixture'));self.assertEqual(g._bans,{});now[0]=11;self.assertTrue(g.allow_rate('fixture'))
 def test_honeypot_strikes_still_explicit_ban(self):
  g=EdgeGuard(honeypot_strikes=3);self.assertFalse(g.strike('fixture'));self.assertFalse(g.strike('fixture'));self.assertTrue(g.strike('fixture'));g.ban('fixture');self.assertFalse(g.allow_rate('fixture'))
 def test_companion_no_backup_promise(self):
  s=Path('intelligence/geo/apps_script/Code.gs').read_text();self.assertNotIn('full records get backed up',s);self.assertNotIn('when Telegram backup happens',s)

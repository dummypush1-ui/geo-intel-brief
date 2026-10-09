import ast
import copy
import inspect
import json
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
from integration import schedule_caller214 as m


class Tests(unittest.TestCase):
    def utc(self,text):return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
    def settings(self,zone='Asia/Calcutta',time='09:00',day='monday'):
        return {'GEO_SCHEDULER_TIMEZONE':zone,'GEO_DAILY_RUN_TIME':time,'GEO_WEEKLY_REPORT_DAY':day}
    def arm(self,anchor=None,settings=None,cadences=None,**kw):
        return m.arm(settings or self.settings(),anchor=anchor or self.utc('2026-10-09T03:29:00'),cadences=cadences or ['daily','weekly'],ambiguous=kw.get('ambiguous','first'),nonexistent=kw.get('nonexistent','skip'),enabled=True)
    def tick(self,state,now,late=60):return m.tick(state,now=now,max_lateness_seconds=late)
    def refuse(self,fn):
        with self.assertRaises(m.CallerRefused)as e:fn()
        self.assertNotIn('PRIVATE',str(e.exception));self.assertIsNone(e.exception.__cause__);self.assertIsNone(e.exception.__context__)

    def test_actual205_daily_weekly_atdue_latebound_no_mutation(self):
        state=self.arm();before=copy.deepcopy(state);due=self.utc('2026-10-09T03:30:00')
        for seconds,status in [(-1,'waiting'),(0,'due'),(60,'due'),(61,'missed_held')]:
            out=self.tick(state,due+timedelta(seconds=seconds));self.assertEqual(out['occurrences'][0]['state'],status)
            self.assertEqual(state,before)
        self.assertEqual(self.tick(state,due,0)['occurrences'][0]['state'],'due')
        self.assertEqual(self.tick(state,due+timedelta(seconds=1),0)['occurrences'][0]['state'],'missed_held')
        self.assertEqual(state['occurrences']['weekly']['evidence']['utc'],'2026-10-12T03:30:00+00:00')
        out=self.tick(state,due);self.refuse(lambda:self.tick(out['state'],due-timedelta(seconds=1)))

    def test_dayslate_oneheld_each_no_catchup_ack_anchors_occurrence_not_now(self):
        state=self.arm();now=self.utc('2026-10-20T03:30:00');out=self.tick(state,now)
        self.assertEqual([r['state']for r in out['occurrences']],['missed_held','missed_held'])
        self.assertEqual(len(out['occurrences']),2)
        nextstate=m.acknowledge_occurrence(out['state'],state['occurrences']['daily']['id'])
        self.assertEqual(nextstate['anchors']['daily'],'2026-10-09T03:30:00.000000+00:00')
        self.assertEqual(nextstate['occurrences']['daily']['evidence']['utc'],'2026-10-10T03:30:00+00:00')
        self.assertEqual(nextstate['last_seen'],out['state']['last_seen'])
        self.assertEqual(self.tick(nextstate,now)['occurrences'][0]['state'],'missed_held')
        self.refuse(lambda:m.acknowledge_occurrence(nextstate,state['occurrences']['daily']['id']))

    def test_coincident_not_dedup_daily_weekly_distinct_static_flags(self):
        state=self.arm(anchor=self.utc('2026-10-12T03:29:00'));out=self.tick(state,self.utc('2026-10-12T03:30:00'))
        self.assertTrue(out['coincident']);self.assertEqual(len(out['occurrences']),2)
        self.assertNotEqual(out['occurrences'][0]['id'],out['occurrences'][1]['id'])
        self.assertEqual(out['note'],'dispatch_not_allowed')
        for occurrence in out['occurrences']:
            self.assertFalse(occurrence['send_allowed']);self.assertFalse(occurrence['dispatch_allowed']);self.assertFalse(occurrence['activation'])
        self.assertEqual(json.loads(json.dumps(out)),out)

    def test_dst_gap_fold_policies_distinct_ids_and_skips(self):
        anchor=self.utc('2026-11-01T05:00:00');settings=self.settings('America/New_York','01:30')
        first=self.arm(anchor,settings,['daily'],ambiguous='first');second=self.arm(anchor,settings,['daily'],ambiguous='second')
        self.assertEqual(first['occurrences']['daily']['evidence']['fold'],0);self.assertEqual(second['occurrences']['daily']['evidence']['fold'],1)
        self.assertNotEqual(first['occurrences']['daily']['id'],second['occurrences']['daily']['id'])
        gap=self.arm(self.utc('2026-03-01T07:30:00'),self.settings('America/New_York','02:30','sunday'),['weekly'])
        self.assertEqual(gap['occurrences']['weekly']['evidence']['skipped_nonexistent'],1)
        self.assertEqual(gap['occurrences']['weekly']['evidence']['utc'],'2026-03-15T06:30:00+00:00')
        self.refuse(lambda:self.arm(self.utc('2026-03-01T07:30:00'),self.settings('America/New_York','02:30','sunday'),['weekly'],nonexistent='refuse'))
        lord=self.arm(self.utc('2026-04-04T14:00:00'),self.settings('Australia/Lord_Howe','01:45'),['daily'],ambiguous='second')
        self.assertEqual(lord['occurrences']['daily']['evidence']['utc'],'2026-04-04T15:15:00+00:00')
        unchangedutc=self.arm(cadences=['daily'],nonexistent='refuse')
        self.assertNotEqual(unchangedutc['occurrences']['daily']['id'],self.arm(cadences=['daily'])['occurrences']['daily']['id'])

    def test_every_occurrence_field_mutated_refused(self):
        state=self.arm(cadences=['daily']);paths=[]
        def leaves(value,path):
            if type(value)is dict:
                for k,v in value.items():leaves(v,path+[k])
            else:paths.append(path)
        leaves(state['occurrences']['daily'],['occurrences','daily'])
        for path in paths:
            changed=copy.deepcopy(state);target=changed
            for key in path[:-1]:target=target[key]
            original=target[path[-1]]
            target[path[-1]]='PRIVATE'if type(original)is str else True if type(original)is int else 1 if type(original)is bool else 'PRIVATE'
            self.refuse(lambda:self.tick(changed,self.utc('2026-10-09T03:30:00')))
        changed=copy.deepcopy(state);changed['occurrences']['daily']['extra']='PRIVATE';self.refuse(lambda:self.tick(changed,self.utc('2026-10-09T03:30:00')))

    def test_state_keys_types_subclasses_and_config_hash(self):
        state=self.arm()
        class S(str):pass
        class D(datetime):pass
        for key,value in [('schema',True),('profile','brics'),('settings_hash','PRIVATE'),('cadences',['daily','daily']),('ambiguous','PRIVATE'),('nonexistent','PRIVATE'),('last_seen','naive'),('send_allowed',True),('settings',{'BRICS_DAILY_RUN_TIME':'09:00'}),('anchors',{}),('occurrences',{}),('extra',1)]:
            changed=copy.deepcopy(state);changed[key]=value;self.refuse(lambda:self.tick(changed,self.utc('2026-10-09T03:30:00')))
        changed=copy.deepcopy(state);changed['settings']['GEO_DAILY_RUN_TIME']='10:00';self.refuse(lambda:self.tick(changed,self.utc('2026-10-09T03:30:00')))
        changed=copy.deepcopy(state);changed['settings']['GEO_DAILY_RUN_TIME']=S('09:00');self.refuse(lambda:self.tick(changed,self.utc('2026-10-09T03:30:00')))
        changed=copy.deepcopy(state);changed['last_seen']=S(state['last_seen']);self.refuse(lambda:self.tick(changed,self.utc('2026-10-09T03:30:00')))
        for now in [datetime(2026,10,9),datetime(2026,10,9,tzinfo=timezone(timedelta(hours=1))),D(2026,10,9,tzinfo=timezone.utc),'2026-10-09']:
            self.refuse(lambda:self.tick(state,now))
        for late in [True,-1,3601,1.0,'60']:self.refuse(lambda:self.tick(state,self.utc('2026-10-09T03:30:00'),late))

    def test_tzdata_provenance_drift_recompute_holds(self):
        state=self.arm(cadences=['daily'])
        from integration import schedule_occurrence205 as engine
        real=engine.next_occurrence
        for field in ['zonefile_sha256','system_tzdata_version','tzdata_package_version','source']:
            def changed(*args,**kw):
                result=real(*args,**kw);result['tzdata'][field]='PRIVATE';return result
            with patch.object(engine,'next_occurrence',side_effect=changed):self.refuse(lambda:self.tick(state,self.utc('2026-10-09T03:30:00')))

    def test_none_in_window_held_not_waiting(self):
        from integration import schedule_occurrence205 as engine
        real=engine.next_occurrence
        def none(*args,**kw):
            result=real(*args,**kw);result.update(state='none_in_window',utc=None,local=None,offset_seconds=None,fold=None,local_weekday=None);return result
        with patch.object(engine,'next_occurrence',side_effect=none):
            state=self.arm(cadences=['daily']);out=self.tick(state,self.utc('2026-10-09T03:30:00'))
            self.assertEqual(out['occurrences'][0]['state'],'held_no_occurrence')
            self.refuse(lambda:m.acknowledge_occurrence(state,state['occurrences']['daily']['id']))

    def test_off_no_arg_touch_no205import(self):
        class Hostile:
            def __getattribute__(self,k):raise AssertionError('touch')
            def __iter__(self):raise AssertionError('touch')
        before=set(sys.modules)
        with patch('builtins.__import__',side_effect=AssertionError('import')):
            result=m.arm(Hostile(),anchor=Hostile(),cadences=Hostile(),ambiguous=Hostile(),nonexistent=Hostile())
        self.assertEqual(set(sys.modules),before);self.assertEqual(result['state'],'disabled');self.assertFalse(result['activation'])
        self.refuse(lambda:m.arm(enabled=1))
        self.refuse(lambda:self.arm(cadences=['weekly','weekly']))
        self.refuse(lambda:m.arm(self.settings(),anchor=self.utc('2026-10-09T03:29:00'),cadences=['daily'],enabled=True))

    def test_duplicate_poll_sameid_is_not_permit(self):
        state=self.arm(cadences=['daily']);now=self.utc('2026-10-09T03:30:00')
        first=self.tick(state,now);second=self.tick(first['state'],now)
        self.assertEqual(first,second);self.assertFalse(second['occurrences'][0]['dispatch_allowed'])

    def test_ast_surface_no_effect_imports_current_graph(self):
        imports=set();tree=ast.parse(inspect.getsource(m))
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imports.update(a.name for a in node.names)
            elif isinstance(node,ast.ImportFrom):imports.add(node.module)
        self.assertEqual(imports,{'copy','datetime','hashlib','json','integration.scheduler_policy','integration.schedule_occurrence205'})
        root=Path(__file__).resolve().parents[1]
        for path in root.rglob('*.py'):
            if '__pycache__'in path.parts or path.name=='test_schedule_caller214.py':continue
            for node in ast.walk(ast.parse(path.read_bytes())):
                if isinstance(node,ast.Import):self.assertFalse(any('schedule_caller214'in a.name for a in node.names),str(path))
                elif isinstance(node,ast.ImportFrom):self.assertFalse('schedule_caller214'in (node.module or '')or any(a.name=='schedule_caller214'for a in node.names),str(path))


if __name__=='__main__':unittest.main()

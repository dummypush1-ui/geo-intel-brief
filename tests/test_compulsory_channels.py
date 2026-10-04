import unittest,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class CompulsoryChannelTests(unittest.TestCase):
 def check(self,body):
  module=(ROOT/'integration/ui/live_channels.js').read_text()
  script=module+'\n'+body
  result=subprocess.run(['node','--input-type=module','-e',script],capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr)
 def test_empty_saved_extras_preserves_republic(self):
  self.check("if(effectiveChannels([]).length!==1 || effectiveChannels([])[0].name!=='Republic')throw Error('fixed lost');")
 def test_default_four_are_extras(self):
  self.check("if(DEFAULT_EXTRAS.length!==4 || DEFAULT_EXTRAS.some(c=>c.name==='Republic'))throw Error('defaults');")
 def test_legacy_tampered_name_cannot_replace_admin(self):
  self.check("const rows=effectiveChannels([{name:'Wrong title',video:COMPULSORY_CHANNELS[0].video,compulsory:false}]);if(rows.length!==1 || rows[0].name!=='Republic')throw Error('tampered');")
 def test_extra_limit_duplicate_and_video_validation(self):
  self.check("for(const v of [[...DEFAULT_EXTRAS,...DEFAULT_EXTRAS],[{name:'Extra',video:'javascript:1'}],Array(21).fill(DEFAULT_EXTRAS[0])]){let bad=false;try{extraChannels(v)}catch{bad=true}if(!bad)throw Error('invalid accepted')} ")
 def test_fixed_configuration_frozen(self):
  self.check("if(!Object.isFrozen(COMPULSORY_CHANNELS)||!Object.isFrozen(COMPULSORY_CHANNELS[0]))throw Error('mutable');")
 def test_html_has_scope_notice(self):
  s=(ROOT/'integration/ui/workspace.html').read_text();self.assertIn('Republic is compulsory',s);self.assertIn('not across devices',s)
 def test_reserved_name_and_invisible_only(self):
  self.check("for(const v of [[{name:'rEpUbLiC',video:'gCNeDWCI0vo'}],[{name:'\\u3164',video:'gCNeDWCI0vo'}],[{name:'\\u2800',video:'gCNeDWCI0vo'}]]){let bad=false;try{extraChannels(v)}catch{bad=true}if(!bad)throw Error('name accepted')}")
 def test_url_forms_collide(self):
  self.check("let bad=false;try{extraChannels([{name:'A',video:'https://youtu.be/gCNeDWCI0vo'},{name:'B',video:'https://www.youtube.com/watch?v=gCNeDWCI0vo'}])}catch{bad=true}if(!bad)throw Error('collision')")
 def test_proto_inheritance_cannot_supply_name_or_video(self):
  self.check("let bad=false;try{extraChannels([{__proto__:{name:'inherited',video:'gCNeDWCI0vo'}}])}catch{bad=true}if(!bad)throw Error('proto accepted');const v=JSON.parse('{\"name\":\"Extra\",\"video\":\"gCNeDWCI0vo\",\"__proto__\":{\"admin\":true}}');if(extraChannels([v]).length!==1 || ({}).admin)throw Error('pollution')")
 def test_fullwidth_reserved_name(self):
  self.check("let bad=false;try{extraChannels([{name:'Ｒｅｐｕｂｌｉｃ',video:'gCNeDWCI0vo'}])}catch{bad=true}if(!bad)throw Error('compatibility name')")

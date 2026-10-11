import fs from 'node:fs';
const load=p=>import('data:text/javascript;base64,'+fs.readFileSync(p).toString('base64'));
const pub=await load('integration/ui/public_brics_streams.js');
const narrow=await load('integration/ui/live_channels.js');
const vectors=JSON.parse(fs.readFileSync('tests/fixtures/brics_url_vectors.json'));
for(const v of vectors){if(pub.videoId(v.input)!==(Object.hasOwn(v,'new_js')?v.new_js:v.public))throw Error('public parity '+v.input);if(narrow.videoId(v.input)!==v.narrow)throw Error('narrow inherited '+v.input);}
for(const name of ['Republic','REPUBLIC','Ｒｅｐｕｂｌｉｃ',' republic ']){let rejected=false;try{pub.extrasChecked([{name,video:'abcdefghijk'}]);}catch{rejected=true;}if(!rejected)throw Error('Republic reserved');}
for(const value of [Array.from({length:9},(_,i)=>({name:'x'+i,video:'abcdefghij'+i})),[{name:'x',video:'jndNegut8RY'}],[{name:'x',video:'abcdefghijk',__proto__:{bad:true}}],[{name:'x',video:'abcdefghijk',extra:true}]]){let fail=false;try{pub.extrasChecked(value);}catch{fail=true;}if(!fail)throw Error('bounds/types');}
const reads=[];const loaded=pub.loadExtras({getItem(key){reads.push(key);return '[{"name":"Republic","video":"jndNegut8RY"}]';}});if(reads.join()!==pub.STORAGE_KEY||loaded.extras.length!==4||!loaded.message.includes('restored'))throw Error('storage');
console.log(JSON.stringify({vectors:vectors.length,public_narrow:true,reservation:true,storage_key_isolated:true,max8:true}));

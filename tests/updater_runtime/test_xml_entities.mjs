import assert from 'node:assert/strict';import {decodeXmlEntities as dec} from '../../updater_runtime/xml-entities.mjs';
for(const [a,b] of [['&amp;amp;lt;','&amp;lt;'],['&amp;lt;','&lt;'],['&lt;','<'],['&quot;&apos;','"\''],['&#128578;','🙂'],['&#x1F642;','🙂'],['&#0;','&#0;'],['&#55296;','&#55296;'],['&#1114112;','&#1114112;'],['&bogus;','&bogus;'],['&#xno;','&#xno;'],['&AMP;','&AMP;']])assert.equal(dec(a),b);
console.log('12 single-pass XML assertions pass');

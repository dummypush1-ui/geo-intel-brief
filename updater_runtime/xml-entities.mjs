// One source scan, no cascading replacements, XML predefined + numeric refs.
const named=Object.freeze({amp:'&',lt:'<',gt:'>',quot:'"',apos:"'"});
export function decodeXmlEntities(s){
 if(typeof s!=='string')throw new TypeError('Plain XML text required');
 return s.replace(/&(?:([A-Za-z]+)|#(\d+)|#x([0-9a-fA-F]+));/g,(raw,name,decimal,hex)=>{
  if(name)return Object.hasOwn(named,name)?named[name]:raw;
  const n=Number.parseInt(decimal||hex,decimal?10:16);
  // XML 1.0 legal scalar values only.
  if(!(n===9||n===10||n===13||n>=32&&n<=0xd7ff||n>=0xe000&&n<=0xfffd||n>=0x10000&&n<=0x10ffff))return raw;
  return String.fromCodePoint(n);
 });
}

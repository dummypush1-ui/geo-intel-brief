/* Strict offline channel configuration and embed URL construction. */
export const DEFAULT_CHANNELS = Object.freeze([
 {name:'Al Jazeera English',video:'gCNeDWCI0vo'},
 {name:'France24 English',video:'HvZt-nh9sGg'},
 {name:'DW News',video:'LuKwFajn37U'},
 {name:'ANI News',video:'nOuWVqeUGt4'},
 {name:'Republic',video:'jndNegut8RY'},
].map(Object.freeze));
// Admin-owned configuration is never read from browser settings.
export const COMPULSORY_CHANNELS = Object.freeze(DEFAULT_CHANNELS.filter(c=>c.name==='Republic'));
export const DEFAULT_EXTRAS = Object.freeze(DEFAULT_CHANNELS.filter(c=>c.name!=='Republic'));
export function extraChannels(value){
 const checked=channelList(value);
 for(const c of checked)if(COMPULSORY_CHANNELS.some(f=>c.video!==f.video && c.name.normalize('NFKC').toLocaleLowerCase('en')===f.name.normalize('NFKC').toLocaleLowerCase('en')))throw new Error('The compulsory channel name is reserved.');
 // Legacy v1 saved lists included mandatory rows. Remove that duplicate, retain
 // the immutable admin record. Local names/flags cannot replace compulsory data.
 return checked.filter(c=>!COMPULSORY_CHANNELS.some(f=>f.video===c.video));
}
export function effectiveChannels(extras){return [...COMPULSORY_CHANNELS,...extraChannels(extras)];}
export function videoId(value){
 if(typeof value!=='string' || value.length>200 || /[\s\\%]/.test(value))return null;
 if(/^[A-Za-z0-9_-]{11}$/.test(value))return value;
 const watch=value.match(/^https:\/\/www\.youtube\.com\/watch\?v=([A-Za-z0-9_-]{11})$/);
 const short=value.match(/^https:\/\/youtu\.be\/([A-Za-z0-9_-]{11})$/);
 return watch?.[1] || short?.[1] || null;
}
export function channelList(value){
 if(!Array.isArray(value) || value.length>20)throw new Error('Use up to 20 channels.');
 const seen=new Set();return value.map(row=>{
  if(!row || typeof row!=='object' || Array.isArray(row) || typeof row.name!=='string' || !row.name.trim() || row.name.length>80 || /[\p{C}]/u.test(row.name) || !/[\p{L}\p{N}\p{P}\p{S}]/u.test(row.name.replace(/[\u115f\u1160\u2800\u3164\uffa0]/g,'')) || ![Object.prototype,null].includes(Object.getPrototypeOf(row)) || !Object.hasOwn(row,'name') || !Object.hasOwn(row,'video'))throw new Error('A visible channel name is required.');
  const video=videoId(row.video);if(!video)throw new Error('Use a video ID or exact YouTube watch link.');
  if(seen.has(video))throw new Error('This video is already in your list.');seen.add(video);
  return {name:row.name.trim(),video};
 });
}
export function embedUrl(video){
 const id=videoId(video);if(!id)throw new Error('Invalid video ID.');
 return 'https://www.youtube-nocookie.com/embed/'+id+'?autoplay=1&mute=1&playsinline=1&rel=0';
}
export function watchUrl(video){const id=videoId(video);if(!id)throw new Error('Invalid video ID.');return 'https://www.youtube.com/watch?v='+id;}

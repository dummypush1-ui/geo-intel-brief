'use strict';
// Synchronous known-completion only. WebSocket binaryType must be arraybuffer.
const MAX_FRAME_BYTES=256*1024;
function validateFrame(ev){
 const d=ev&&ev.data;
 if(typeof d==='string')return d.length<=MAX_FRAME_BYTES&&Buffer.byteLength(d,'utf8')<=MAX_FRAME_BYTES;
 return d instanceof ArrayBuffer&&d.byteLength<=MAX_FRAME_BYTES;
}
function decodeFrame(ev){
 if(!validateFrame(ev))throw Error('bounded_frame_required');
 return typeof ev.data==='string'?ev.data:Buffer.from(ev.data).toString('utf8');
}
module.exports=Object.freeze({MAX_FRAME_BYTES,validateFrame,decodeFrame});

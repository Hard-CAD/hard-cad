(function(root){
'use strict';
function validate(c){
 const finite=x=>typeof x==='number'&&Number.isFinite(x),vec=x=>Array.isArray(x)&&x.length===3&&x.every(finite);
 if(!c||c.schema_version!=='hardcad.contract.v1'||c.frame!=='world'||c.unit!=='mm'||typeof c.state!=='string'||!c.state.trim()||!Array.isArray(c.requirements)||!c.requirements.length||c.requirements.length>5000)throw Error('invalid contract');
 const ids=new Set();for(const r of c.requirements){if(!r||typeof r.id!=='string'||!r.id.trim()||ids.has(r.id)||!['keep_in','keep_out'].includes(r.kind)||!finite(r.tolerance_mm3)||r.tolerance_mm3<0||!r.region||!vec(r.region.origin))throw Error('invalid requirement');ids.add(r.id);const g=r.region;if(g.kind==='box'){if(!vec(g.size)||!g.size.every(x=>x>0))throw Error('invalid box')}else if(g.kind==='cylinder'){if(!vec(g.axis)||!Number.isFinite(Math.hypot(...g.axis))||Math.hypot(...g.axis)===0||!finite(g.radius)||g.radius<=0||!finite(g.height)||g.height<=0)throw Error('invalid cylinder')}else throw Error('unsupported region')}
 return c;
}
async function bind(bytes, report, subtle){if(!subtle)throw Error('SHA-256 unavailable');const raw=new Uint8Array(bytes);const hash=Array.from(new Uint8Array(await subtle.digest('SHA-256',raw))).map(x=>x.toString(16).padStart(2,'0')).join('');if(!report||hash!==report.contract_sha256)throw Error('contract hash mismatch');const c=validate(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)));if(!report.scope||report.scope.frame!==c.frame||report.scope.state!==c.state||report.scope.unit!==c.unit||report.requirements.length!==c.requirements.length)throw Error('contract scope mismatch');for(const r of report.requirements){const x=c.requirements.find(t=>t.id===r.id);if(!x||x.kind!==r.kind||x.tolerance_mm3!==r.tolerance||r.unit!=='mm3')throw Error('contract requirement mismatch')}return c}
const api={validate,bind};if(typeof module==='object'&&module.exports)module.exports=api;else root.HardCadContract=api;
})(typeof globalThis==='object'?globalThis:this);

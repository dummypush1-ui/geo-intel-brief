// Fixed operational labels only. Provider message prose never decides bad-key.
export function classifyGeminiError(status, data) {
 const error=data&&data.error;
 const reasons=Array.isArray(error?.details)?error.details.filter(x=>x&&x['@type']==='type.googleapis.com/google.rpc.ErrorInfo').map(x=>x.reason):[];
 if(reasons.some(x=>['API_KEY_INVALID','API_KEY_EXPIRED'].includes(x)))return 'invalid_key';
 if(status===403)return 'permission_denied';
 if(status===429)return 'quota';
 if(status===404)return 'model_missing';
 if(status>=500&&status<=599)return 'service_unavailable';
 if(status===400)return 'invalid_request';
 return 'request_failed';
}

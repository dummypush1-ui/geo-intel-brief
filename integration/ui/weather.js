'use strict';
const root=document.querySelector('main');const available=root.dataset.weatherAvailable==='true';const button=document.getElementById('weather-fetch');const status=document.getElementById('weather-status');const result=document.getElementById('weather-result');
const ports={INBOM:'Mumbai (Bombay)',INMAA:'Chennai (Madras)',INKOC:'Kochi (Cochin)'};
const fields={temperature_2m:['Temperature','°C'],relative_humidity_2m:['Relative humidity','%'],weather_code:['Weather code','wmo code'],wind_speed_10m:['Wind speed','km/h'],wind_direction_10m:['Wind direction','°']};
function element(tag,text){const e=document.createElement(tag);e.textContent=text;return e;}
function render(data,place){
 if(!data||data.place!==place||data.label!==ports[place]||data.scope!=='land_forecast_not_marine_or_safety'||data.source?.name!=='Open-Meteo'||data.source?.url!=='https://open-meteo.com/'||data.source?.licence!=='CC BY 4.0')throw Error('Invalid forecast');
 if(!Number.isFinite(data.age_seconds)||data.age_seconds<0||data.age_seconds>3600||!['cached_forecast','stale_forecast'].includes(data.freshness))throw Error('Invalid freshness');
 for(const key of ['forecast_time','fetched_at'])if(typeof data[key]!=='string'||data[key].length>40||!data[key].endsWith('+00:00')||!Number.isFinite(Date.parse(data[key])))throw Error('Invalid UTC time');
 const list=element('dl','');
 for(const [key,[label,unit]]of Object.entries(fields)){
  const row=data.values?.[key];if(!row||row.unit!==unit||!['forecast','unavailable'].includes(row.state)||(row.state==='unavailable'?row.value!==null:typeof row.value!=='number'||!Number.isFinite(row.value)))throw Error('Invalid values');
  const div=element('div','');div.append(element('dt',label),element('dd',row.state==='unavailable'?'Unavailable':String(row.value)+' '+unit));list.append(div);
 }
 const fresh=element('p',(data.freshness==='stale_forecast'?'Stale forecast':'Cached forecast')+' - fetched '+data.age_seconds+' seconds ago.');fresh.className='freshness';
 result.replaceChildren(element('h2',ports[place]),fresh,element('p','Forecast time: '+data.forecast_time+' (UTC)'),element('p','Fetched at: '+data.fetched_at+' (UTC)'),list,element('p','Weather data by Open-Meteo (CC BY 4.0). Land forecast, not marine or safety advice.'));result.hidden=false;
}
if(available){button.disabled=false;document.getElementById('availability').textContent='Manual forecast available';status.textContent='No forecast requested.';}
button.addEventListener('click',async event=>{
 if(!event.isTrusted||!available||button.disabled)return;const place=document.getElementById('weather-place').value;if(!ports[place])return;
 button.disabled=true;result.hidden=true;result.replaceChildren();status.textContent='Fetching land forecast...';const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),7000);
 try{const response=await fetch('/api/public-weather?'+new URLSearchParams({place}),{method:'GET',credentials:'omit',redirect:'error',cache:'no-store',signal:controller.signal});
  if(!response.ok)throw Error(response.status===429?'busy':response.status===403?'refused':'unavailable');if(!response.headers.get('content-type')?.startsWith('application/json'))throw Error('unavailable');const text=await response.text();if(text.length>65536)throw Error('unavailable');render(JSON.parse(text),place);status.textContent='Forecast loaded. Request again only when needed.';
 }catch(error){result.hidden=true;status.textContent=error.message==='busy'?'Weather busy. Wait, then retry manually.':error.message==='refused'?'Weather request refused. Use the manual button in this page; address-bar API requests (Sec-Fetch-Site: none) receive 403.':'Weather unavailable. Your selected port is unchanged. Retry manually later.';}
 finally{clearTimeout(timer);button.disabled=false;}
});

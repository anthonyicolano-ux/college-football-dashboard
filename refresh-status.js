/* Latest recorded workflow result and age of the published datasets. */
(async function(){
'use strict';
const box=document.getElementById('refreshHealth');if(!box)return;
const staleHours=108;
const page=location.pathname.split('/').pop()||'index.html';
const needed=page==='players.html'||page==='player.html'?['players']:page==='matchups.html'?['teams','players','schedule']:page==='rankings.html'?['teams','schedule']:['teams'];
async function get(name){const r=await fetch('data/'+name+'.json',{cache:'no-cache'});if(!r.ok)throw Error('Unavailable');return r.json();}
const results=await Promise.allSettled([get('refresh-status'),...needed.map(get)]);
const status=results[0].status==='fulfilled'&&results[0].value.schemaVersion===1?results[0].value:null;
const now=Date.now();let stale=[],missing=[],dates=[];
needed.forEach((name,i)=>{const result=results[i+1];const time=result.status==='fulfilled'?Date.parse(result.value.generatedAt):NaN;if(!Number.isFinite(time)){missing.push(name);return;}dates.push(name+': '+new Date(time).toLocaleString());if(now-time>staleHours*3600000)stale.push(name);});
const failed=status?.outcome==='failed';
box.style.cssText='padding:14px 16px;margin-bottom:14px;border-radius:7px;border:1px solid '+(failed||stale.length||missing.length?'#d6a338':'#b9d7cc')+';background:'+(failed||stale.length||missing.length?'#fff1cd':'#eaf6f0')+';color:#25384a;font-size:14px;line-height:1.6';
const main=failed?'Latest recorded refresh failed. Showing the last validated data.':stale.length?'Published data needs a refresh.':missing.length?'Some dataset timestamps are unavailable.':status?.outcome==='success'?'Latest recorded refresh passed.':'Refresh history will appear after the updated workflow runs.';
const strong=document.createElement('strong');strong.textContent=main;box.appendChild(strong);
function line(text){const div=document.createElement('div');div.textContent=text;box.appendChild(div);}
if(status?.finishedAt&&Number.isFinite(Date.parse(status.finishedAt)))line('Last recorded attempt: '+new Date(status.finishedAt).toLocaleString()+' · Requested season '+status.attemptedSeason);
if(status?.lastSuccessAt&&Number.isFinite(Date.parse(status.lastSuccessAt)))line('Last validated refresh: '+new Date(status.lastSuccessAt).toLocaleString());
if(stale.length)line('Stale datasets: '+stale.join(', ')+'. The freshness warning starts after '+staleHours+' hours (4.5 days), allowing for the longest scheduled refresh gap.');
if(missing.length)line('Missing timestamps: '+missing.join(', ')+'.');
if(status?.apiUsage){const usage=status.apiUsage;const month=new Date(now).toISOString().slice(0,7);line('API requests tracked this UTC month: '+(usage.monthlyRequests?.[month]??0)+' · Latest attempt: '+(usage.latestRequests??'not recorded'));line('Tracking started '+new Date(usage.trackingStartedAt).toLocaleString()+'. Earlier usage and other applications are excluded; this is not your official account quota counter.');}
const details=document.createElement('details');details.style.cssText='margin-top:8px;padding:0;border:0;background:transparent';const summary=document.createElement('summary');summary.textContent='Dataset times and refresh details';details.appendChild(summary);
const text=document.createElement('p');text.textContent=dates.join(' · ')||'No valid dataset timestamps available.';details.appendChild(text);
const note=document.createElement('p');note.textContent='This reports the latest result successfully published by the workflow. A cancelled run or failed status publication may not appear here. Source statistics can lag behind a successful refresh.';details.appendChild(note);
if(status?.runUrl){try{const url=new URL(status.runUrl);if(url.origin==='https://github.com'&&/^\/anthonyicolano-ux\/college-football-dashboard\/actions\/runs\/\d+$/.test(url.pathname)){const link=document.createElement('a');link.href=url.href;link.textContent='Open refresh workflow run';details.appendChild(link);}}catch{}}
if(status?.apiUsage){const usage=status.apiUsage;const count=document.createElement('p');count.textContent='Latest request attempts by endpoint: '+Object.entries(usage.latestByEndpoint||{}).map(([path,n])=>path+' '+n).join(' · ');details.appendChild(count);const scope=document.createElement('p');scope.textContent=usage.scope;details.appendChild(scope);}
box.appendChild(details);
})();


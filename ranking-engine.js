/* Descriptive matchup screening; no probabilities or projections. */
(function(root){
'use strict';
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const weights={balanced:{efficiency:.45,production:.25,volume:.20,context:.10},efficiency:{efficiency:.75,production:.10,volume:.05,context:.10}};
function eligible(r,min){return r&&r.games>=min&&r.adjustedEligible===true&&r.effEligible===true&&['adjustedEffRatio','eff','ratio','ypg','attemptsPerGame','volumeRatio'].every(k=>finite(r[k]));}
function metric(r,key){if(key==='intRate')return finite(r.ints)&&r.attemptsPerGame*r.games>0?r.ints/(r.attemptsPerGame*r.games):null;return r[key];}
function percentile(value,pool,key){if(!finite(value))return null;const values=pool.map(r=>metric(r,key)).filter(finite);if(!values.length)return null;const p=100*(values.filter(v=>v<value).length+.5*values.filter(v=>v===value).length)/values.length;return key==='intRate'?100-p:p;}
function groups(row,pool,unit){const specs={efficiency:[['adjustedEffRatio',8],['eff',1]],production:[['ratio',3],['ypg',2]],volume:[['attemptsPerGame',1],['volumeRatio',1]],context:unit==='pass'?[['comp',1],['td',5],['intRate',4]]:[['td',1]]};const result={};for(const [group,keys]of Object.entries(specs)){let total=0,den=0,available=0;for(const [key,w]of keys){const p=percentile(metric(row,key),pool,key);if(p!==null){total+=w*p;den+=w;available++;}}result[group]={value:den?total/den:null,available,fields:keys.length};}return result;}
function scorePair(off,def,op,dp,unit,mode){const a=groups(off,op,unit),b=groups(def,dp,unit),breakdown={};let sum=0,den=0;for(const [k,w]of Object.entries(weights[mode])){const values=[a[k].value,b[k].value].filter(finite);const value=values.length?values.reduce((x,y)=>x+y,0)/values.length:null;breakdown[k]={value,weight:w,offense:a[k],defense:b[k]};if(value!==null){sum+=value*w;den+=w;}}return {score:den?sum/den:null,breakdown};}
function rankRows(rows,key){const ordered=rows.slice().sort((a,b)=>b[key]-a[key]||a.off.team.localeCompare(b.off.team)||String(a.game.id).localeCompare(String(b.game.id)));let previous=null,rank=0;ordered.forEach((r,i)=>{const rounded=Math.round(r[key]*1e6);if(rounded!==previous)rank=i+1;r[key+'Rank']=rank;previous=rounded;});return ordered;}
function rank(teams,games,{unit='pass',period='season',mode='balanced',min=3}={}){const op=(teams.offenseWindows?.[unit]?.[period]||[]).filter(r=>eligible(r,min)),dp=(teams.windows?.[unit]?.[period]||[]).filter(r=>eligible(r,min));const rows=[];let excluded=0;for(const game of games)for(const side of ['home','away']){const off=op.find(r=>r.teamId===(side==='home'?game.homeId:game.awayId)),def=dp.find(r=>r.teamId===(side==='home'?game.awayId:game.homeId));if(!off||!def){excluded++;continue;}const balanced=scorePair(off,def,op,dp,unit,'balanced'),efficiency=scorePair(off,def,op,dp,unit,'efficiency');rows.push({game,side,off,def,balanced:balanced.score,efficiency:efficiency.score,breakdown:(mode==='balanced'?balanced:efficiency).breakdown});}rankRows(rows,'balanced');rankRows(rows,'efficiency');return {rows:rankRows(rows,mode),excluded,offensePool:op.length,defensePool:dp.length};}
function localDate(date){return new Intl.DateTimeFormat('en-CA',{timeZone:'America/Chicago',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(date));}
function monday(date){const d=new Date(date+'T12:00:00Z');d.setUTCDate(d.getUTCDate()-(d.getUTCDay()+6)%7);return d.toISOString().slice(0,10);}
function gameWeek(g){return g.startDate?monday(g.startTimeTBD?g.startDate.slice(0,10):localDate(g.startDate)):null;}
function upcoming(g,now=new Date()){if(!g.startDate)return false;if(g.startTimeTBD)return g.startDate.slice(0,10)>=localDate(now);return new Date(g.startDate)>now;}
function sensitivity(teams,games,{unit='pass'}={}){
 const results=new Map(),scenarios=[];
 const key=(game,side)=>String(game.id)+':'+side;
 for(const period of ['season','last3'])for(const min of [3,2]){
  // Both scoring-view ranks come from the same calculation for this population.
  const ranked=rank(teams,games,{unit,period,min,mode:'balanced'});
  const lookup=new Map(ranked.rows.map(r=>[key(r.game,r.side),r]));
  for(const mode of ['balanced','efficiency']){
   const scenario={period,min,mode};scenarios.push(scenario);
   for(const game of games)for(const side of ['home','away']){
    const id=key(game,side),row=lookup.get(id);
    let reason='';
    if(!row){const off=(teams.offenseWindows?.[unit]?.[period]||[]).find(r=>r.teamId===(side==='home'?game.homeId:game.awayId));const def=(teams.windows?.[unit]?.[period]||[]).find(r=>r.teamId===(side==='home'?game.awayId:game.homeId));reason=!off||!def?'Window stats unavailable':off.games<min||def.games<min?'Below '+min+' games: offense '+off.games+', defense '+def.games:'Core stats or adjustment coverage incomplete';}
    if(!results.has(id))results.set(id,[]);
    results.get(id).push({...scenario,rank:row?.[mode+'Rank']??null,score:row?.[mode]??null,slateSize:ranked.rows.length,reason});
   }
  }
 }
 const summaries=new Map();
 for(const [id,screens]of results){const comparable=screens.filter(x=>x.rank!==null),ranks=comparable.map(x=>x.rank);summaries.set(id,{screens,comparable:comparable.length,total:scenarios.length,best:ranks.length?Math.min(...ranks):null,worst:ranks.length?Math.max(...ranks):null,top5:comparable.filter(x=>x.rank<=5).length});}
 return summaries;
}
const api={weights,eligible,percentile,groups,scorePair,rank,sensitivity,localDate,monday,gameWeek,upcoming};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.MatchupRanking=api;
})(typeof globalThis!=='undefined'?globalThis:this);


"use strict";
// No third-party scripts, localStorage, query strings or analytics for health text.
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = { catalog:null, mode:"", page:1, total:0, topics:[], session:null, accounts:[], request:0, controller:null, animations:[], aiOptOutQuery:"", active:false, directoryMoved:false };
const initials = (name) => name.split(" ").slice(0,2).map(n => n[0]).join("");
let toastTimer;
function toast(text){ $("#toast").textContent=text; $("#toast").hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>$("#toast").hidden=true,4500); }
async function api(path, {method="GET", data, signal, csrf=false}={}) {
  const headers={"Accept":"application/json"};
  if(method!=="GET"){headers["Content-Type"]="application/json"; headers["X-Conecta-Request"]="demo";}
  if(csrf && state.session) headers["X-CSRF-Token"]=state.session.csrf;
  const res=await fetch(path,{method,headers,body:data===undefined?undefined:JSON.stringify(data),credentials:"same-origin",cache:"no-store",signal});
  let result; try{result=await res.json();}catch{throw new Error("O servidor n\u00e3o retornou uma resposta v\u00e1lida.");}
  if(!res.ok) throw new Error(typeof result.detail==="string" ? result.detail : "N\u00e3o foi poss\u00edvel concluir. Confira os campos e tente novamente.");
  return result;
}
function params(){const query=$("#search-query").value.trim();return {query,profession:$("#profession").value,city:$("#city").value,mode:state.mode,audience:$("#audience").value,topics:state.topics,page:state.page,page_size:12,accepting:$("#accepting").checked,allow_ai:Boolean($("#ai-consent")?.checked),ai_opt_out:state.aiOptOutQuery===query};}
function fillSelect(selector, entries){const el=$(selector); for(const [value,label] of entries){const option=document.createElement("option"); option.value=value; option.textContent=label; el.append(option);}}
function card(p){const c=state.catalog; return `<article class="profile-card"><div class="card-top"><div class="avatar avatar-${esc(p.profession)}" aria-hidden="true">${esc(initials(p.name))}</div><span class="demo-badge">PERFIL FICT\u00cdCIO</span></div><h3>${esc(p.name)}</h3><p class="profession-label">${esc(c.professions[p.profession])}</p><p class="card-headline">${esc(p.headline)}</p><div class="tag-row">${p.audiences.slice(0,2).map(a=>`<span class="tag">${esc(c.audiences[a])}</span>`).join("")}${p.audiences.length>2?'<span class="tag">+ faixas et\u00e1rias</span>':''}</div><div class="card-meta"><span><span class="meta-icon" aria-hidden="true">\u2316</span>${esc(p.city)} / ${esc(p.state)}</span><span><span class="meta-icon" aria-hidden="true">\u25ce</span>${p.modes.map(m=>m==="online"?"Online":"Presencial").join(" e ")}</span></div><button class="card-link" data-profile="${esc(p.id)}" aria-label="Conhecer perfil fict\u00edcio de ${esc(p.name)}">Conhecer perfil <span aria-hidden="true">\u2197</span></button>${p.alumni?'<span class="card-alumni">V\u00ednculo Vivaion simulado</span>':'<span class="card-alumni">Profissional externo simulado</span>'}</article>`;}
function renderChips(result){const selected=[]; const c=state.catalog;const p=params();
 if(p.profession)selected.push(["profession",c.professions[p.profession]]);
 if(p.city)selected.push(["city",p.city]);
 if(p.mode)selected.push(["mode",p.mode==="online"?"Online":"Presencial"]);
 if(p.audience)selected.push(["audience",c.audiences[p.audience]]);
 if(p.accepting)selected.push(["accepting","Novos atendimentos"]);
 for(const t of p.topics)selected.push(["topic:"+t,c.topics[t].label]);
 const i=result.interpretation; const box=$("#interpretation");
 if(i.source==="ollama")for(const t of i.topics)selected.push(["ai-topic:"+t,c.topics[t].label]);
 $("#active-filters").innerHTML=selected.map(([k,v])=>`<button class="active-chip" data-clear="${esc(k)}" aria-label="Remover filtro ${esc(v)}">${esc(v)} <span aria-hidden="true">\u00d7</span></button>`).join("");
 box.hidden=!p.query || (!i.topics.length && !i.professions.length && i.source!=="safety_notice" && i.ai_status!=="unavailable");
 box.classList.toggle("urgent",i.source==="safety_notice");
 box.innerHTML=`<strong>${i.source==="safety_notice"?"N\u00e3o espere pelo buscador":i.source==="ollama"?`Sua busca foi relacionada a: ${esc(i.topics.map(t=>c.topics[t].label).join(" \u00b7 "))}`:`Sua busca se aproxima de: ${esc(i.topics.map(t=>c.topics[t].label).join(" \u00b7 ")||i.professions.map(t=>c.professions[t]).join(" \u00b7 "))}`}</strong><p>${esc(i.message)}</p>`;
}
function cancelCardAnimations(){
 for(const animation of state.animations)animation.cancel();
 state.animations=[];
 $$("#cards .profile-card[inert]").forEach(card=>{card.inert=false;card.removeAttribute("aria-hidden");card.style.willChange="";});
}
function animateResultCards(){
 if(window.matchMedia("(prefers-reduced-motion: reduce)").matches)return;
 const cards=$$("#cards .profile-card"); if(!cards.length)return;
 cancelCardAnimations();
 const source=$(".search-shell").getBoundingClientRect();
 const run=state.request;
 for(const [index,card] of cards.entries()){
  const target=card.getBoundingClientRect(); const spread=(index%4-1.5)*13;
  const x=source.left+source.width/2-target.left-target.width/2+spread;
  const y=source.bottom-target.top-4-(index%4)*11;
  const rotation=(index%2?1:-1)*(7+(index%3)*2);
  card.inert=true;card.setAttribute("aria-hidden","true");card.style.willChange="transform, opacity";
  const animation=card.animate([{transform:`translate(${x}px, ${y}px) rotate(${rotation}deg) scale(.91)`,opacity:.18},{offset:.42,transform:`translate(${x*.18}px, ${y*.18}px) rotate(${rotation*.28}deg) scale(1.02)`,opacity:1},{transform:"translate(0, 0) rotate(0)",opacity:1}],{duration:820,delay:Math.min(index,7)*80,easing:"cubic-bezier(.16,.84,.27,1)",fill:"both"});
  state.animations.push(animation);
 }
 Promise.allSettled(state.animations.map(animation=>animation.finished)).then(()=>{
  if(run!==state.request)return;
  for(const animation of state.animations)animation.cancel();
  state.animations=[];
  $$("#cards .profile-card[inert]").forEach(card=>{card.inert=false;card.removeAttribute("aria-hidden");card.style.willChange="";});
 });
}
function activateDirectory(){
 if(state.active)return;
 state.active=true;
 const hero=$("#hero"),discovery=$("#discovery"),directory=$("#directory");
 directory.hidden=false;
 hero.classList.add("hero-dismissed");hero.setAttribute("aria-hidden","true");hero.inert=true;
 discovery.classList.add("discovery-dismissed");discovery.setAttribute("aria-hidden","true");discovery.inert=true;
 if(window.matchMedia("(max-width: 760px)").matches&&!state.directoryMoved){$(".search-shell").after(directory);state.directoryMoved=true;}
}
function activateAndSearch({animate=true}={}){activateDirectory();search(false,false,animate);}
function setSearching(searching){
 $("#search-loading").hidden=!searching;$("#search-button").setAttribute("aria-busy",String(searching));
 $("#search-button-label").textContent=searching?"Buscando...":"Encontrar";
}
async function search(append=false,scroll=false,animate=false){
 if(!state.catalog)return;
 if(!append)state.page=1;
 const current=++state.request;
 if(state.controller)state.controller.abort();
 if(!append)cancelCardAnimations();
 state.controller=new AbortController();
 $("#cards").setAttribute("aria-busy","true");$("#search-button").disabled=true;$("#load-more").disabled=true;$("#search-error").hidden=true;setSearching(true);
 try{
  const result=await api('/api/search',{method:'POST',data:params(),signal:state.controller.signal});
  if(current!==state.request)return;
  state.total=result.total;
  if(!append)$("#cards").innerHTML="";
  $("#cards").insertAdjacentHTML("beforeend",result.items.map(card).join(""));
  $("#results-summary").textContent=`${result.total} ${result.total===1?'perfil fict\u00edcio encontrado':'perfis fict\u00edcios encontrados'}`;
  $("#empty-state").hidden=result.total!==0 || result.interpretation.source==='safety_notice';
  $("#load-more").hidden=state.page>=result.pages;
  $("#page-info").textContent=result.total ? `Exibindo ${Math.min(state.page*12,result.total)} de ${result.total} perfis de teste` : '';
  renderChips(result);
  if(animate && !append && result.items.length)requestAnimationFrame(animateResultCards);
  if(scroll && !animate)$("#directory").scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'nearest'});
 }catch(error){if(error.name!=="AbortError" && current===state.request){$("#search-error").textContent=error.message;$("#search-error").hidden=false;$("#cards").innerHTML="";$("#results-summary").textContent='Busca n\u00e3o conclu\u00edda';$("#load-more").hidden=true;$("#empty-state").hidden=true;$("#page-info").textContent='';}}
 finally{if(current===state.request){$("#cards").setAttribute('aria-busy','false');$("#search-button").disabled=false;$("#load-more").disabled=false;setSearching(false);}}
}
function mode(value){state.mode=value;$$('[data-mode]').forEach(b=>{b.classList.toggle('active',b.dataset.mode===value);b.setAttribute('aria-pressed',String(b.dataset.mode===value));});}
function reset(){ $("#search-query").value='';['#city','#profession','#audience','#topic'].forEach(s=>$(s).value='');$("#accepting").checked=false;state.topics=[];mode('');$("#directory").classList.remove('filters-open');$("#mobile-refine").setAttribute('aria-expanded','false');search(false,false,true);}
function openDialog(id){const d=$('#'+id);if(!d.open)d.showModal();}
async function showProfile(id){
 try{const p=await api('/api/professionals/'+encodeURIComponent(id)); const c=state.catalog;
 $("#profile-content").innerHTML=`<div class="dialog-top"><p class="eyebrow">CONHE\u00c7A O PERFIL \u00b7 DEMONSTRA\u00c7\u00c3O</p><button class="icon-button" data-close="profile-dialog" aria-label="Fechar">\u00d7</button></div><div class="profile-identity"><div class="avatar avatar-${esc(p.profession)}" aria-hidden="true">${esc(initials(p.name))}</div><div><h2 id="profile-title">${esc(p.name)}</h2><p>${esc(c.professions[p.profession])} \u00b7 Perfil fict\u00edcio</p></div></div><div class="notice">Dados inteiramente inventados. Credenciais n\u00e3o verificadas. N\u00e3o realiza atendimento real.</div><div class="profile-details"><div><span class="detail-label">LOCALIZA\u00c7\u00c3O</span><span class="detail-value">${esc(p.city)} / ${esc(p.state)}</span></div><div><span class="detail-label">MODALIDADE</span><span class="detail-value">${p.modes.map(m=>m==='online'?'Online':'Presencial').join(' e ')}</span></div><div><span class="detail-label">P\u00daBLICO</span><span class="detail-value">${p.audiences.map(a=>esc(c.audiences[a])).join(', ')}</span></div><div><span class="detail-label">EXPERI\u00caNCIA SIMULADA</span><span class="detail-value">${p.experience_years} anos \u00b7 ${p.accepting?'Com disponibilidade simulada':'Sem novas vagas simuladas'}</span></div></div><section class="profile-content-section"><h3>${esc(p.headline)}</h3><p>${esc(p.bio)}</p><div class="tag-row">${p.topics.map(t=>`<span class="tag">${esc(c.topics[t].label)}</span>`).join('')}</div></section><section class="profile-content-section"><h3>Forma\u00e7\u00e3o acad\u00eamica fict\u00edcia</h3>${p.qualifications.map(q=>`<div class="qualification"><strong>${esc(q.level)} \u00b7 ${esc(q.title)}</strong><p>${esc(q.institution)} \u00b7 ${q.year} \u00b7 N\u00e3o verificada</p></div>`).join('')}</section><div class="profile-bottom"><button class="button button-primary" id="simulate-contact">Simular interesse <span aria-hidden="true">\u2197</span></button><p>Nenhuma mensagem ser\u00e1 enviada. Este perfil n\u00e3o representa uma pessoa real.</p><div id="contact-result" class="notice" role="status" hidden></div></div>`;
 openDialog('profile-dialog');
 }catch(e){toast(e.message);}
}
function renderAccounts(){const profession=$("#account-filter").value;$("#account-list").innerHTML=state.accounts.filter(p=>!profession||p.profession===profession).map(p=>`<button class="account-option" data-login="${esc(p.id)}"><span class="avatar avatar-${esc(p.profession)}" aria-hidden="true">${esc(initials(p.name))}</span><span><strong>${esc(p.name)}</strong><small>${esc(state.catalog.professions[p.profession])} \u00b7 ${esc(p.id)}</small></span></button>`).join('');}
async function showAccounts(){if(!state.catalog){toast('Aguarde o carregamento do cat\u00e1logo.');return;}if(state.session){showEditor();return;}try{const result=await api('/api/demo/accounts');state.accounts=result.accounts;renderAccounts();$("#account-error").hidden=true;openDialog('account-dialog');}catch(e){toast(e.message);}}
async function login(id){$$('[data-login]').forEach(b=>b.disabled=true);try{state.session=await api('/api/demo/session',{method:'POST',data:{user_id:id}});$("#account-dialog").close();$("#account-button").textContent='Meu perfil de teste';showEditor();}catch(e){$("#account-error").textContent=e.message;$("#account-error").hidden=false;}finally{$$('[data-login]').forEach(b=>b.disabled=false);}}
function showEditor(){const p=state.session.profile;$("#editor-identity").innerHTML=`<div class="profile-identity"><div class="avatar avatar-${esc(p.profession)}" aria-hidden="true">${esc(initials(p.name))}</div><div><strong>${esc(p.name)}</strong><p>${esc(state.catalog.professions[p.profession])} \u00b7 ${esc(p.id)}</p></div></div>`;$("#edit-headline").value=p.headline;$("#edit-bio").value=p.bio;$("#edit-accepting").checked=p.accepting;$("#edit-topics").innerHTML=Object.entries(state.catalog.topics).filter(([,v])=>v.professions.includes(p.profession)).map(([k,v])=>`<label><input type="checkbox" value="${esc(k)}" ${p.topics.includes(k)?'checked':''}>${esc(v.label)}</label>`).join('');$("#edit-status").hidden=true;openDialog('editor-dialog');}
$("#search-form").addEventListener('submit',e=>{e.preventDefault();state.topics=[];state.aiOptOutQuery='';$("#topic").value='';activateAndSearch();});
$("#profession").addEventListener('change',()=>activateAndSearch());$("#city").addEventListener('change',()=>activateAndSearch());$("#audience").addEventListener('change',()=>activateAndSearch());$("#accepting").addEventListener('change',()=>activateAndSearch());
$("#topic").addEventListener('change',()=>{state.topics=$("#topic").value?[$("#topic").value]:[];activateAndSearch();});
$("#clear-filters").addEventListener('click',reset);$("#empty-reset").addEventListener('click',reset);
$("#load-more").addEventListener('click',()=>{state.page++;search(true);});
$("#browse-all").addEventListener('click',()=>activateAndSearch());
$("#mobile-refine").addEventListener('click',()=>{const directory=$("#directory"),open=directory.classList.toggle('filters-open');$("#mobile-refine").setAttribute('aria-expanded',String(open));$("#mobile-refine").innerHTML=open?'Ocultar filtros <span aria-hidden="true">&#8593;</span>':'Refinar filtros <span aria-hidden="true">&#8595;</span>';});
$("#account-button").addEventListener('click',showAccounts);$("#demo-start").addEventListener('click',showAccounts);$("#account-filter").addEventListener('change',renderAccounts);$("#privacy-button").addEventListener('click',()=>openDialog('info-dialog'));
document.addEventListener('click',e=>{
 const b=e.target.closest('button');if(!b)return;
 if(b.dataset.mode!==undefined){mode(b.dataset.mode);activateAndSearch();}
 if(b.dataset.query!==undefined){$("#search-query").value=b.dataset.query;state.topics=[];state.aiOptOutQuery='';$("#topic").value='';activateAndSearch();}
 if(b.dataset.profile)showProfile(b.dataset.profile);
 if(b.dataset.close)$('#'+b.dataset.close).close();
 if(b.dataset.login)login(b.dataset.login);
 if(b.dataset.clear){const key=b.dataset.clear;if(key==='mode')mode('');else if(key.startsWith('topic:')){state.topics=state.topics.filter(t=>t!==key.slice(6));$("#topic").value=state.topics.length===1?state.topics[0]:'';}else if(key.startsWith('ai-topic:'))state.aiOptOutQuery=$("#search-query").value.trim();else if(key==='accepting')$("#accepting").checked=false;else $('#'+key).value='';search(false,false,true);}
 if(b.id==='simulate-contact'){$('#contact-result').textContent='Interesse simulado! Na vers\u00e3o validada, este passo apresentar\u00e1 os canais autorizados pelo profissional. Nenhuma mensagem foi enviada.';$('#contact-result').hidden=false;}
});
$("#editor-form").addEventListener('submit',async e=>{e.preventDefault();const topics=$$('#edit-topics input:checked').map(i=>i.value);if(!topics.length||topics.length>5){$("#edit-status").textContent='Selecione de 1 a 5 temas.';$("#edit-status").hidden=false;return;}$('#save-profile').disabled=true;try{const result=await api('/api/me/profile',{method:'PATCH',data:{headline:$('#edit-headline').value,bio:$('#edit-bio').value,topics,accepting:$('#edit-accepting').checked},csrf:true});state.session.profile=result.profile;$('#edit-status').textContent='Perfil fict\u00edcio salvo. A busca j\u00e1 reflete a altera\u00e7\u00e3o.';$('#edit-status').hidden=false;search();}catch(err){$('#edit-status').textContent=err.message;$('#edit-status').hidden=false;}finally{$('#save-profile').disabled=false;}});
$('#logout').addEventListener('click',async()=>{try{await api('/api/logout',{method:'POST',data:{},csrf:true});state.session=null;$('#editor-dialog').close();$('#account-button').textContent='Sou profissional \u2197';toast('Sess\u00e3o de teste encerrada.');}catch(e){toast(e.message);}});
async function init(){
 try{state.catalog=await api('/api/catalog');fillSelect('#profession',Object.entries(state.catalog.professions));fillSelect('#account-filter',Object.entries(state.catalog.professions));fillSelect('#audience',Object.entries(state.catalog.audiences));fillSelect('#city',state.catalog.cities.map(c=>[c,c]));fillSelect('#topic',Object.entries(state.catalog.topics).map(([k,v])=>[k,v.label]));$("#ai-consent-note").hidden=!state.catalog.ai_enabled;
 // A missing demo session is normal and does not prevent directory use.
 try{state.session=await api('/api/session');$('#account-button').textContent='Meu perfil de teste';}catch{}
 }catch(e){$('#cards').innerHTML='';$('#cards').setAttribute('aria-busy','false');$('#results-summary').textContent='Cat\u00e1logo indispon\u00edvel';$('#search-error').textContent='N\u00e3o foi poss\u00edvel carregar o cat\u00e1logo. Recarregue a p\u00e1gina para tentar novamente.';$('#search-error').hidden=false;}
}
init();

"""Deterministic discovery and ranking. No generative text or diagnosis."""
from .taxonomy import interpret_rules, normalize, TOPICS

STOP={'a','o','as','os','de','do','da','em','um','uma','para','por','com','e','que','quero','preciso','busco','procuro','meu','minha','ajuda','atendimento','profissional','encontrar','me','tem','na','no'}

def public_profile(profile):
    return {k:v for k,v in profile.items() if k!='email'}

def search_catalog(profiles,query='',profession='',city='',mode='',audience='',topics=(),page=1,page_size=12,accepting=False):
    interpretation=interpret_rules(query)
    if interpretation['source']=='safety_notice':
        return {'items':[],'total':0,'page':page,'pages':0,'interpretation':interpretation}
    inferred=topics or interpretation['topics']
    profs=[profession] if profession else interpretation['professions']
    age=audience or interpretation['audience']
    tokens=[w for w in normalize(query).split() if w not in STOP and len(w)>2]
    manual=bool(profession or city or mode or audience or topics)
    if interpretation.get('manual_only') and not manual:
        return {'items':[], 'total':0, 'page':page, 'pages':0, 'interpretation':interpretation}
    ranked=[]
    for p in profiles:
        if profs and p['profession'] not in profs: continue
        if city and normalize(city)!=normalize(p['city']+' / '+p['state']): continue
        if mode and mode not in p['modes']: continue
        if age and age not in p['audiences']: continue
        if accepting and not p['accepting']: continue
        overlap=set(inferred)&set(p['topics'])
        if inferred and not overlap: continue
        hay=normalize(' '.join([p['name'],p['headline'],p['bio'],p['city']]+[TOPICS[t]['label'] for t in p['topics']]))
        lexical=sum(1 for t in tokens if t in hay)
        if query and interpretation['needs_clarification'] and not manual:
            if not tokens or lexical!=len(tokens): continue
        score=len(overlap)*10+lexical
        # No alumni bonus, paid placement, rating or fabricated clinical score.
        ranked.append((score,p['id'],p))
    ranked.sort(key=lambda v:(-v[0],v[1]))
    total=len(ranked)
    start=(page-1)*page_size
    return {'items':[public_profile(p) for _,_,p in ranked[start:start+page_size]],'total':total,'page':page,'pages':(total+page_size-1)//page_size,'interpretation':interpretation}

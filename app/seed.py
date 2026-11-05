"""Exactly 40 fictional accounts. Never import student or patient records."""
from .taxonomy import TOPICS, PROFESSIONS

# Names, qualifications and trajectories below are invented.
NAMES=["Clara Almeida","Marina Duarte","Helena Prado","Luiza Martins","Beatriz Campos","Rafael Azevedo","Isabela Moura","Laura Nogueira","Camila Tavares","Pedro Valente","Sofia Reis","Renata Dias","Bruno Monteiro","Alice Fonseca","Daniela Pires","Lucas Amaral","Ana Carvalho","Gabriel Torres","Juliana Barros","Felipe Lima","Carolina Mendes","Thiago Vieira","Bianca Rocha","Gustavo Freitas","Leticia Castro","Eduardo Melo","Natalia Ribeiro","Vitor Teixeira","Manuela Costa","Andre Farias","Cecilia Lopes","Vinicius Salles","Paula Borges","Diego Silveira","Livia Moreira","Rodrigo Antunes","Aline Cardoso","Henrique Melo","Elisa Macedo","Matheus Peixoto"]
FOCUS=[
 ('fono',['linguagem','neuro'],['crianca']),('fono',['caa','linguagem'],['crianca','adolescente']),
 ('fono',['fala'],['crianca','adolescente']),('fono',['linguagem'],['crianca']),
 ('fono',['caa','neuro'],['crianca','adolescente','adulto']),('fono',['disfagia'],['adulto','idoso']),
 ('fono',['voz'],['adulto']),('fono',['motricidade','alimentacao'],['crianca','adulto']),
 ('fono',['linguagem','fala'],['crianca']),('fono',['caa'],['adulto','idoso']),
 ('fono',['fala','voz'],['adolescente','adulto']),('fono',['disfagia','motricidade'],['adulto','idoso']),
 ('fono',['voz'],['adulto']),('fono',['linguagem','caa'],['crianca']),
 ('fono',['neuro','caa'],['crianca','adolescente']),('fono',['motricidade','fala'],['crianca','adulto']),
 ('psi',['ansiedade'],['adolescente','adulto']),('psi',['infancia','neuro'],['crianca','adolescente']),
 ('psi',['trabalho','ansiedade'],['adulto']),('psi',['dependencias'],['adolescente','adulto']),
 ('psi',['mulheres','ansiedade'],['adulto']),('psi',['luto'],['adulto','idoso']),
 ('psi',['infancia'],['crianca']),('psi',['neuro'],['crianca','adolescente','adulto']),
 ('psi',['ansiedade','luto'],['adulto']),('psi',['dependencias','luto'],['adulto']),
 ('psi',['mulheres','infancia'],['adulto']),('psi',['trabalho'],['adulto']),
 ('to',['autonomia','neuro'],['crianca','adolescente']),('to',['autonomia'],['adulto','idoso']),
 ('to',['caa','autonomia'],['crianca','adolescente','adulto']),('to',['alimentacao','autonomia'],['crianca']),
 ('nutri',['alimentacao'],['crianca','adolescente']),('nutri',['alimentacao'],['adulto']),
 ('nutri',['alimentacao'],['adulto','idoso']),('nutri',['alimentacao'],['crianca','adulto']),
 ('fisio',['reabilitacao'],['adulto','idoso']),('fisio',['reabilitacao'],['crianca']),
 ('fisio',['reabilitacao'],['adulto']),('fisio',['reabilitacao'],['adolescente','adulto','idoso']),
]
CITIES=[('Cascavel','PR'),('Curitiba','PR'),('S\u00e3o Paulo','SP'),('Florian\u00f3polis','SC'),('Toledo','PR'),('Londrina','PR'),('Porto Alegre','RS'),('Foz do Igua\u00e7u','PR'),('Belo Horizonte','MG'),('Maring\u00e1','PR')]

def generate_profiles():
    profiles=[]
    for i,(name,(profession,topics,audiences)) in enumerate(zip(NAMES,FOCUS),1):
        city,state=CITIES[(i-1)%len(CITIES)]
        modes=['online','presencial'] if i%3==1 else (['online'] if i%3==2 else ['presencial'])
        # Ensure same-city and online examples across all five areas.
        focus=TOPICS[topics[0]]['label']
        profiles.append({
            'id':f'demo-{i:03d}','name':name,'email':f'profissional{i:02d}@example.test',
            'profession':profession,'city':city,'state':state,'topics':topics,'audiences':audiences,
            'modes':modes,'experience_years':3+(i*3)%16,'alumni':i%4!=0,'is_demo':True,
            'headline':focus,'bio':f'Perfil fict\u00edcio para testar a busca em {PROFESSIONS[profession]}. Atua\u00e7\u00e3o simulada em {focus.lower()}, com escuta e objetivos compartilhados. N\u00e3o representa um profissional real.',
            'qualifications':[
                {'level':'Gradua\u00e7\u00e3o','title':PROFESSIONS[profession], 'institution':'Institui\u00e7\u00e3o fict\u00edcia A','year':2003+i%14,'verified':False},
                {'level':'Especializa\u00e7\u00e3o','title':focus,'institution':'Institui\u00e7\u00e3o fict\u00edcia B','year':2018+i%7,'verified':False},
            ] + ([{'level':'Mestrado' if i%2 else 'Doutorado','title':f'Ci\u00eancias da sa\u00fade (simulado)','institution':'Universidade fict\u00edcia C','year':2022+i%3,'verified':False}] if i%5==0 else []),
            'accepting':i%7!=0,'credential_status':'demo_not_verified','registration_number':None,
        })
    assert len(profiles)==40
    return profiles

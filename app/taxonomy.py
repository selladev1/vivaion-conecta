"""Curated discovery taxonomy, not clinical triage or a diagnostic ontology."""
import re
import unicodedata

PROFESSIONS = {
    "fono": "Fonoaudiologia", "psi": "Psicologia",
    "to": "Terapia ocupacional", "nutri": "Nutri\u00e7\u00e3o", "fisio": "Fisioterapia",
}
AUDIENCES = {"crianca": "Crian\u00e7as", "adolescente": "Adolescentes", "adulto": "Adultos", "idoso": "Pessoas idosas"}
TOPICS = {
 "linguagem": {"label": "Linguagem infantil", "professions": ["fono"], "terms": ["linguagem", "fala poucas palavras", "nao fala", "demora para falar", "dificuldade para falar", "atraso na fala", "atraso de fala", "meu filho fala pouco", "meu filho nao fala", "crianca fala pouco", "desenvolvimento da fala"]},
 "fala": {"label": "Fala e flu\u00eancia", "professions": ["fono"], "terms": ["fala", "gagueira", "gaguejo", "troca letras", "troca sons", "apraxia", "fluencia", "disartria"]},
 "caa": {"label": "CAA e comunica\u00e7\u00e3o", "professions": ["fono", "to"], "terms": ["caa", "comunicacao alternativa", "comunicacao aumentativa", "prancha de comunicacao", "comunicador"]},
 "disfagia": {"label": "Degluti\u00e7\u00e3o e disfagia", "professions": ["fono"], "terms": ["disfagia", "engasga", "engasgos", "degluticao", "engolir", "traqueostomia"]},
 "voz": {"label": "Voz e orat\u00f3ria", "professions": ["fono"], "terms": ["voz", "rouquidao", "oratoria", "falar em publico", "comunicacao profissional"]},
 "motricidade": {"label": "Motricidade orofacial", "professions": ["fono"], "terms": ["motricidade", "orofacial", "miofuncional", "mastigacao", "respiracao oral"]},
 "ansiedade": {"label": "Ansiedade e bem-estar", "professions": ["psi"], "terms": ["ansiedade", "ansioso", "ansiosa", "preocupacao", "preocupacoes", "panico"]},
 "infancia": {"label": "Inf\u00e2ncia e parentalidade", "professions": ["psi"], "terms": ["parentalidade", "comportamento infantil", "psicologia infantil", "birras", "orientacao de pais", "emocao da crianca"]},
 "neuro": {"label": "Neurodesenvolvimento e inclus\u00e3o", "professions": ["fono", "psi", "to"], "terms": ["autismo", "autista", "tea", "neurodesenvolvimento", "inclusao escolar", "pei", "tdah"]},
 "trabalho": {"label": "Sa\u00fade mental no trabalho", "professions": ["psi"], "terms": ["burnout", "esgotamento", "estresse no trabalho", "saude mental no trabalho"]},
 "luto": {"label": "Luto e rela\u00e7\u00f5es", "professions": ["psi"], "terms": ["luto", "perdi minha mae", "relacionamento", "separacao", "perda de um familiar"]},
 "dependencias": {"label": "Depend\u00eancias e afetos", "professions": ["psi"], "terms": ["dependencia", "alcool", "drogas", "compulsao", "vicio"]},
 "mulheres": {"label": "Sa\u00fade mental das mulheres", "professions": ["psi"], "terms": ["saude da mulher", "saude mental das mulheres", "maternidade", "puerperio"]},
 "autonomia": {"label": "Autonomia e rotina", "professions": ["to"], "terms": ["autonomia", "atividades diarias", "terapia ocupacional", "rotina", "integracao sensorial", "processamento sensorial"]},
 "alimentacao": {"label": "Alimenta\u00e7\u00e3o e nutri\u00e7\u00e3o", "professions": ["nutri", "fono", "to"], "terms": ["alimentacao", "alimentar", "seletividade", "nutricao", "nutricionista", "comida", "comer"]},
 "reabilitacao": {"label": "Movimento e reabilita\u00e7\u00e3o", "professions": ["fisio"], "terms": ["fisioterapia", "fisioterapeuta", "reabilitacao", "mobilidade", "dor nas costas", "equilibrio", "movimento"]},
}
PROFESSION_TERMS={"fono":["fonoaudiologia","fonoaudiologo","fonoaudiologa","fono"],"psi":["psicologia","psicologo","psicologa"],"to":["terapeuta ocupacional","terapia ocupacional"],"nutri":["nutricao","nutricionista"],"fisio":["fisioterapia","fisioterapeuta"]}

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))).strip()

def phrase(text: str, term: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text))

def privacy_violation(text: str) -> bool:
    # Conservative rejection, not a claim of complete de-identification.
    return bool(re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b|(?:\+?55\s*)?\(?\d{2}\)?[ -]?9?\d{4}[ -]?\d{4}\b", text))

def interpret_rules(text: str) -> dict:
    q=normalize(text)
    # These reminders are deliberately not a medical triage classifier.
    immediate=["nao consigo respirar", "sem respirar", "dor no peito", "quero me matar", "vou me matar", "me machucar agora", "engasgando agora", "convulsao agora", "desmaiou agora", "dificuldade subita para falar"]
    if any(phrase(q,t) for t in immediate):
        return {"source":"safety_notice", "topics":[], "professions":[], "audience":None, "needs_clarification":True, "message":"Este buscador n\u00e3o avalia urg\u00eancias. Em risco imediato, procure um servi\u00e7o de emerg\u00eancia. N\u00e3o espere uma resposta da busca."}
    if re.search(r"\b(nao quero|nao procuro|nao preciso|exceto|menos de|sem ser|ignore|ignorar|instrucoes anteriores|system prompt)\b",q):
        return {"source":"rules", "topics":[], "professions":[], "audience":None, "needs_clarification":True, "manual_only":True, "message":"Para n\u00e3o interpretar sua busca de forma incorreta, selecione a \u00e1rea e os filtros abaixo."}
    topics=[key for key,item in TOPICS.items() if any(phrase(q,t) for t in item['terms'])]
    # A generic word 'fala' must not swamp a more specific communication search.
    if 'linguagem' in topics and 'fala' in topics and not any(phrase(q,t) for t in ['gagueira','apraxia','troca sons','troca letras']): topics.remove('fala')
    professions=[key for key,terms in PROFESSION_TERMS.items() if any(phrase(q,t) for t in terms)]
    age=None
    if any(phrase(q,t) for t in ['crianca','criancas','infantil','bebe','meu filho de 4','minha filha de 4']): age='crianca'
    elif any(phrase(q,t) for t in ['adolescente','adolescentes']): age='adolescente'
    elif any(phrase(q,t) for t in ['idoso','idosa','idosos']): age='idoso'
    elif any(phrase(q,t) for t in ['adulto','adulta']): age='adulto'
    found=bool(topics or professions)
    return {"source":"rules", "topics":topics, "professions":professions, "audience":age, "needs_clarification":bool(q and not found), "message":"Estes filtros representam temas da sua busca, n\u00e3o um diagn\u00f3stico. Voc\u00ea pode ajust\u00e1-los." if found else "Conte o que procura ou escolha uma \u00e1rea. N\u00e3o inclua nomes, documentos ou informa\u00e7\u00f5es de contato."}

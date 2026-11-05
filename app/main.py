"""Vivaion Conecta: demo-only ASGI application, isolated from academic accounts."""
import base64
import hashlib
import hmac
import os
import secrets
import threading
import time
from collections import OrderedDict, deque
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict, field_validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from .ai import LocalInterpreter
from .search import search_catalog, public_profile
from .storage import Repository
from .taxonomy import TOPICS, PROFESSIONS, AUDIENCES, privacy_violation

ROOT=Path(__file__).resolve().parent.parent

class StrictModel(BaseModel):
    model_config=ConfigDict(extra='forbid')

class SearchInput(StrictModel):
    query:str=Field(default='',max_length=600)
    profession:str=Field(default='',max_length=20)
    city:str=Field(default='',max_length=80)
    mode:Literal['','online','presencial']=''
    audience:str=Field(default='',max_length=20)
    topics:list[str]=Field(default_factory=list,max_length=5)
    page:int=Field(default=1,ge=1,le=10000)
    page_size:int=Field(default=12,ge=1,le=24)
    accepting:bool=False
    @field_validator('query')
    @classmethod
    def no_pii(cls,v):
        if privacy_violation(v): raise ValueError('Use apenas uma queixa ficticia, sem documentos, telefones ou e-mail')
        return v.strip()
    @field_validator('profession')
    @classmethod
    def known_profession(cls,v):
        if v and v not in PROFESSIONS: raise ValueError('Unknown profession')
        return v
    @field_validator('audience')
    @classmethod
    def known_audience(cls,v):
        if v and v not in AUDIENCES: raise ValueError('Unknown audience')
        return v
    @field_validator('topics')
    @classmethod
    def known_topics(cls,v):
        if any(t not in TOPICS for t in v): raise ValueError('Unknown topic')
        return list(dict.fromkeys(v))

class InterpretInput(StrictModel):
    query:str=Field(min_length=2,max_length=600)
    consent:bool=False
    @field_validator('query')
    @classmethod
    def no_pii(cls,v): return SearchInput.no_pii(v)

class DemoLogin(StrictModel):
    user_id:str=Field(pattern=r'^demo-\d{3}$')

class ProfileUpdate(StrictModel):
    headline:str=Field(min_length=3,max_length=120)
    bio:str=Field(min_length=20,max_length=1000)
    topics:list[str]=Field(min_length=1,max_length=5)
    accepting:bool
    @field_validator('headline','bio',mode='before')
    @classmethod
    def safe_demo_text(cls,v):
        if not isinstance(v,str): raise ValueError('Text required')
        if privacy_violation(v): raise ValueError('Real contact or document data is not accepted in the demo')
        return v.strip()
    @field_validator('topics')
    @classmethod
    def valid_topics(cls,v): return SearchInput.known_topics(v)

class RateLimiter:
    def __init__(self):
        self.salt=secrets.token_bytes(32)
        self.buckets=OrderedDict()
        self.lock=threading.Lock()
    def allow(self,client,route,limit):
        key=hmac.new(self.salt,(client+'|'+route).encode(),hashlib.sha256).digest()
        now=time.monotonic()
        with self.lock:
            # Touch order tracks the most recently used bucket, bounding memory.
            while self.buckets:
                old_key,old_values=next(iter(self.buckets.items()))
                if old_values and old_values[-1]>now-60: break
                self.buckets.pop(old_key)
            if key not in self.buckets and len(self.buckets)>=2048: return False
            values=self.buckets.setdefault(key,deque())
            self.buckets.move_to_end(key)
            while values and values[0]<=now-60: values.popleft()
            if len(values)>=limit: return False
            values.append(now)
            return True

class GuardMiddleware(BaseHTTPMiddleware):
    def __init__(self,app,origins,access_token,secure,limiter):
        super().__init__(app)
        self.origins=origins
        self.access_token=access_token
        self.secure=secure
        self.limiter=limiter
    async def dispatch(self,request,call_next):
        if self.access_token:
            valid=False
            try:
                kind,encoded=request.headers.get('authorization','').split(' ',1)
                user,password=base64.b64decode(encoded,validate=True).decode().split(':',1)
                valid=kind.lower()=='basic' and hmac.compare_digest(user.encode(),b'demo') and hmac.compare_digest(password.encode(),self.access_token.encode())
            except (ValueError,UnicodeError): pass
            if not valid:
                return JSONResponse({'detail':'Ambiente de testes restrito'},401,headers={'WWW-Authenticate':'Basic realm="Conecta demo", charset="UTF-8"','Cache-Control':'no-store','X-Robots-Tag':'noindex, nofollow, noarchive'})
        if request.method in ('POST','PUT','PATCH','DELETE'):
            if request.headers.get('origin') not in self.origins:
                return JSONResponse({'detail':'Origem nao autorizada'},403,headers={'Cache-Control':'no-store'})
            if request.headers.get('x-conecta-request')!='demo':
                return JSONResponse({'detail':'Cabecalho de requisicao ausente'},403)
            if request.headers.get('content-type','').split(';')[0]!='application/json':
                return JSONResponse({'detail':'Use application/json'},415)
            total=0
            chunks=[]
            async for chunk in request.stream():
                total+=len(chunk)
                if total>16384:
                    return JSONResponse({'detail':'Corpo muito grande'},413)
                chunks.append(chunk)
            request._body=b''.join(chunks)
        if request.url.path.startswith('/api/'):
            client=request.client.host if request.client else 'unknown'
            group='ai' if request.url.path=='/api/interpret' else 'login' if request.url.path=='/api/demo/session' else 'api'
            limit={'ai':6,'login':15,'api':180}[group]
            if not self.limiter.allow(client,group,limit):
                return JSONResponse({'detail':'Muitas solicitacoes. Tente novamente em um minuto.'},429,headers={'Retry-After':'60','Cache-Control':'no-store'})
        response=await call_next(request)
        response.headers['X-Robots-Tag']='noindex, nofollow, noarchive'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
        if request.url.path.startswith('/assets/'):
            response.headers['Cache-Control']='private, max-age=3600, must-revalidate'
        else:
            response.headers['Cache-Control']='no-store'
        if self.secure: response.headers['Strict-Transport-Security']='max-age=86400'
        return response

def create_app(db_path=None,environment=None,ai_enabled=None,access_token=None):
    env=environment or os.getenv('APP_ENV','development')
    if env not in ('development','test','staging'):
        raise RuntimeError('Demo is not approved for production; APP_ENV must be development, test or staging')
    token=access_token if access_token is not None else os.getenv('DEMO_ACCESS_TOKEN','')
    origin_list=[o.strip().rstrip('/') for o in os.getenv('APP_ORIGINS','http://127.0.0.1:8080,http://localhost:8080').split(',') if o.strip()]
    if env=='staging' and (len(token)<24 or not origin_list or any(urlparse(o).scheme!='https' or not urlparse(o).netloc or urlparse(o).path not in ('','/') for o in origin_list)):
        raise RuntimeError('Staging requires DEMO_ACCESS_TOKEN >=24 chars and exact HTTPS APP_ORIGINS')
    repository=Repository(db_path or os.getenv('DATABASE_PATH',str(ROOT/'var'/'conecta-demo.sqlite3')))
    ai=LocalInterpreter(enabled=ai_enabled if ai_enabled is not None else os.getenv('OLLAMA_ENABLED','false').lower()=='true',url=os.getenv('OLLAMA_URL','http://127.0.0.1:11434'),model=os.getenv('OLLAMA_MODEL','qwen2.5:3b'))
    app=FastAPI(title='Vivaion Conecta - demo',docs_url=None,redoc_url=None,openapi_url=None)
    app.state.repository=repository
    app.state.ai=ai
    app.state.limiter=RateLimiter()
    app.state.searches=0
    app.add_middleware(GZipMiddleware,minimum_size=800)
    app.add_middleware(GuardMiddleware,origins=set(origin_list),access_token=token,secure=env=='staging',limiter=app.state.limiter)

    # Pydantic's default error response echoes supplied input. Do not echo health text.
    from fastapi.exceptions import RequestValidationError
    @app.exception_handler(RequestValidationError)
    async def validation_error(request,exc):
        return JSONResponse({'detail':'Confira os campos. Use somente dados ficticios e nao informe documentos, telefones ou e-mail.'},422)

    def session(request):
        value=request.cookies.get('conecta_session','')
        found=repository.session_get(hashlib.sha256(value.encode()).hexdigest()) if value else None
        if not found: raise HTTPException(401,'Entre em uma conta de demonstracao')
        return found
    def csrf_session(request):
        data=session(request)
        if not hmac.compare_digest(data['csrf'],request.headers.get('x-csrf-token','')):
            raise HTTPException(403,'Token CSRF invalido')
        return data

    @app.get('/healthz')
    def health(): return {'status':'ok','mode':'demo','profiles':len(repository.catalog())}

    @app.get('/api/catalog')
    def catalog():
        return {'professions':PROFESSIONS,'audiences':AUDIENCES,'topics':{k:{'label':v['label'],'professions':v['professions']} for k,v in TOPICS.items()},'cities':sorted({p['city']+' / '+p['state'] for p in repository.catalog()}),'demo':True,'ai_enabled':ai.enabled,'count':len(repository.catalog())}

    @app.post('/api/search')
    def search(data:SearchInput):
        app.state.searches+=1
        return search_catalog(repository.catalog(),**data.model_dump())

    @app.post('/api/interpret')
    async def interpret(data:InterpretInput):
        return await ai.interpret(data.query,data.consent)

    @app.get('/api/professionals/{profile_id}')
    def get_profile(profile_id:str):
        profile=repository.get(profile_id)
        if not profile: raise HTTPException(404,'Perfil nao encontrado')
        return public_profile(profile)

    @app.get('/api/demo/accounts')
    def demo_accounts():
        return {'accounts':[{'id':p['id'],'name':p['name'],'profession':p['profession'],'email':p['email']} for p in repository.catalog()]}

    @app.post('/api/demo/session')
    def demo_login(data:DemoLogin,response:Response):
        profile=repository.get(data.user_id)
        if not profile or not profile['is_demo']: raise HTTPException(404,'Conta de demonstracao nao encontrada')
        raw=secrets.token_urlsafe(32)
        csrf=secrets.token_urlsafe(32)
        repository.session_create(hashlib.sha256(raw.encode()).hexdigest(),data.user_id,csrf)
        response.set_cookie('conecta_session',raw,max_age=3600,httponly=True,secure=env=='staging',samesite='strict',path='/')
        return {'profile':public_profile(profile),'csrf':csrf,'demo':True}

    @app.get('/api/session')
    def current_session(request:Request):
        current=session(request)
        return {'profile':public_profile(repository.get(current['user_id'])),'csrf':current['csrf'],'demo':True}

    @app.patch('/api/me/profile')
    def update_profile(data:ProfileUpdate,request:Request):
        current=csrf_session(request)
        profile=repository.get(current['user_id'])
        if any(profile['profession'] not in TOPICS[t]['professions'] for t in data.topics):
            raise HTTPException(422,'Selecione temas compativeis com a profissao do perfil de teste')
        result=repository.update(current['user_id'],data.model_dump())
        return {'profile':public_profile(result)}

    @app.post('/api/logout')
    def logout(request:Request,response:Response):
        csrf_session(request)
        raw=request.cookies.get('conecta_session','')
        repository.session_delete(hashlib.sha256(raw.encode()).hexdigest())
        response.delete_cookie('conecta_session',path='/',httponly=True,secure=env=='staging',samesite='strict')
        return {'ok':True}

    app.mount('/assets',StaticFiles(directory=ROOT/'public'/'assets'),name='assets')
    @app.get('/robots.txt')
    def robots(): return Response('User-agent: *\nDisallow: /\n',media_type='text/plain')
    @app.get('/')
    def index(): return FileResponse(ROOT/'public'/'index.html')
    return app

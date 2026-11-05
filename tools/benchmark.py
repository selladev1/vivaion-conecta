"""Bounded LOCAL benchmark. Starts its own demo server, never the VPS/Ollama."""
import asyncio,gzip,json,os,socket,statistics,subprocess,sys,tempfile,time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
async def load(origin):
    sem=asyncio.Semaphore(10)
    queries=['CAA','ansiedade','linguagem infantil','fisioterapia','']
    samples=[]
    statuses=[]
    async with httpx.AsyncClient(base_url=origin,timeout=15,trust_env=False,headers={'Origin':origin,'X-Conecta-Request':'demo'}) as client:
        async def one(i):
            async with sem:
                before=time.perf_counter()
                r=await client.post('/api/search',json={'query':queries[i%len(queries)],'page_size':12})
                samples.append((time.perf_counter()-before)*1000)
                statuses.append(r.status_code)
        start=time.perf_counter()
        await asyncio.gather(*(one(i) for i in range(120)))
        wall=time.perf_counter()-start
    samples.sort()
    return {'requests':120,'concurrency':10,'statuses':{str(s):statuses.count(s) for s in set(statuses)},'wall_seconds':round(wall,3),'median_ms':round(statistics.median(samples),2),'p95_ms':round(samples[int(.95*(len(samples)-1))],2),'max_ms':round(max(samples),2)}

with tempfile.TemporaryDirectory() as temp:
    with socket.socket() as s:
        s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
    origin=f'http://127.0.0.1:{port}'
    env={**os.environ,'APP_ENV':'test','APP_ORIGINS':origin,'DATABASE_PATH':temp+'/bench.sqlite3','OLLAMA_ENABLED':'false','DEMO_ACCESS_TOKEN':''}
    proc=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:create_app','--factory','--host','127.0.0.1','--port',str(port),'--workers','1','--no-access-log'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try:
                if httpx.get(origin+'/healthz',timeout=.5,trust_env=False).status_code==200: break
            except httpx.HTTPError: time.sleep(.1)
        else: raise RuntimeError('Local benchmark server failed to start')
        results=asyncio.run(load(origin))
        rss=None
        try:
            import psutil
            rss=round(psutil.Process(proc.pid).memory_info().rss/1024**2,2)
        except ImportError: pass
        assets={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'gzip_bytes':len(gzip.compress(p.read_bytes()))} for p in [ROOT/'public/index.html',*sorted((ROOT/'public/assets').glob('*'))]}
        report={'environment':'local development container, NOT Vivaion VPS','python':sys.version.split()[0],'ollama_calls':0,'database':'SQLite WAL, 40 synthetic profiles','http':results,'process_rss_after_load_mib':rss,'assets':assets,'frontend_total_bytes':sum(v['bytes'] for v in assets.values()),'frontend_total_gzip_bytes':sum(v['gzip_bytes'] for v in assets.values()),'limitations':'Not a capacity guarantee. Excludes public network, TLS proxy, VPS contention, real clinical quality and model inference. Rate limits remained enabled.'}
        print(json.dumps(report,indent=2))
        if set(results['statuses'])!={'200'}: raise RuntimeError('HTTP benchmark had errors')
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill();proc.wait()

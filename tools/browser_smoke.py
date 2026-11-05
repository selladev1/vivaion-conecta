"""Offline browser smoke test with real ASGI API via an in-process transport.

No remote network, live server, SSO or real Ollama is tested by this script.
Requires playwright (dev only) and a Chromium executable in CHROMIUM_PATH.
"""
import base64,json,os,re,sys,tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright,expect
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.main import create_app

ROOT=Path(__file__).resolve().parents[1]
ARTIFACTS=Path(os.getenv('SCREENSHOT_DIR',str(ROOT/'artifacts')))
ARTIFACTS.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as d:
 app=create_app(db_path=d+'/browser.sqlite3',environment='test',ai_enabled=False)
 with TestClient(app,headers={'Origin':'http://127.0.0.1:8080','X-Conecta-Request':'demo'}) as client, sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path=os.getenv('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1440,'height':1040},device_scale_factor=1)
  errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def transport(source,req):
   assert req['path'].startswith('/api/')
   response=client.request(req['method'],req['path'],content=req.get('body'),headers=req.get('headers',{}))
   return {'status':response.status_code,'body':response.text}
  page.expose_binding('__test_api',transport)
  html=(ROOT/'public/index.html').read_text()
  html=re.sub(r'<link[^>]+>', '', html)
  html=re.sub(r'<script[^>]*></script>', '', html)
  image='data:image/svg+xml;base64,'+base64.b64encode((ROOT/'public/assets/mark.svg').read_bytes()).decode()
  html=html.replace('/assets/mark.svg',image)
  page.set_content(html)
  page.add_style_tag(content=(ROOT/'public/assets/style.css').read_text())
  page.evaluate('''() => { window.fetch = async (path, options={}) => {
    const result = await window.__test_api({path,method:options.method||'GET',headers:options.headers||{},body:options.body});
    return new Response(result.body,{status:result.status,headers:{'Content-Type':'application/json'}});
  }; }''')
  page.add_script_tag(content=(ROOT/'public/assets/app.js').read_text())
  expect(page.locator('.profile-card')).to_have_count(12)
  expect(page.locator('#results-summary')).to_contain_text('40')
  page.screenshot(path=str(ARTIFACTS/'conecta-desktop.png'),full_page=True)
  assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
  page.locator('#load-more').click()
  expect(page.locator('.profile-card')).to_have_count(24)
  page.locator('#clear-filters').click()
  page.locator('#search-query').fill('Meu filho de 4 anos fala poucas palavras')
  page.locator('#search-button').click()
  expect(page.locator('#interpretation')).to_be_visible()
  expect(page.locator('.profile-card')).to_have_count(5)
  page.locator('[data-mode="online"]').click()
  page.locator('#cards .card-link').first.click()
  expect(page.locator('#profile-dialog')).to_be_visible()
  page.locator('#simulate-contact').click()
  expect(page.locator('#contact-result')).to_be_visible()
  page.keyboard.press('Escape')
  page.locator('#clear-filters').click()
  page.locator('#profession').select_option('psi')
  expect(page.locator('#results-summary')).to_contain_text('12')
  page.locator('#search-query').fill('encanador')
  page.locator('#profession').select_option('')
  page.locator('#search-button').click()
  expect(page.locator('#empty-state')).to_be_visible()
  expect(page.locator('#ai-box')).to_be_visible()
  page.locator('#clear-filters').click()
  page.locator('#search-query').fill('dor no peito')
  page.locator('#search-button').click()
  expect(page.locator('#interpretation.urgent')).to_be_visible()
  expect(page.locator('.profile-card')).to_have_count(0)
  page.locator('#clear-filters').click()
  page.locator('#account-button').click()
  expect(page.locator('.account-option')).to_have_count(40)
  page.locator('[data-login="demo-001"]').click()
  expect(page.locator('#editor-dialog')).to_be_visible()
  page.locator('#edit-headline').fill('Linguagem infantil - exemplo editado')
  page.locator('#save-profile').click()
  expect(page.locator('#edit-status')).to_contain_text('salvo')
  page.screenshot(path=str(ARTIFACTS/'conecta-painel.png'))
  page.keyboard.press('Escape')
  page.locator('[data-profile="demo-001"]').click()
  expect(page.locator('.profile-content-section h3').first).to_have_text('Linguagem infantil - exemplo editado')
  page.screenshot(path=str(ARTIFACTS/'conecta-perfil.png'))
  page.keyboard.press('Escape')
  page.locator('#account-button').click()
  page.locator('#logout').click()
  expect(page.locator('#editor-dialog')).not_to_be_visible()
  page.locator('#clear-filters').click()
  expect(page.locator('#toast')).not_to_be_visible(timeout=6000)
  page.set_viewport_size({'width':390,'height':844})
  page.evaluate('scrollTo(0,0)')
  page.screenshot(path=str(ARTIFACTS/'conecta-mobile.png'),full_page=True)
  assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
  page.locator('#profession').select_option('fisio')
  expect(page.locator('.profile-card')).to_have_count(4)
  page.locator('#cards .card-link').first.click()
  expect(page.locator('#profile-dialog')).to_be_visible()
  page.keyboard.press('Escape')
  assert not errors,errors
  report={'status':'passed','transport':'offline browser + real in-process ASGI API','desktop':'1440x1040','mobile':'390x844','horizontal_overflow':False,'javascript_errors':errors,'scenarios':['initial catalog','pagination','natural language rules','modality','profile','simulated interest','profession','unknown search fallback','urgent notice','40-account chooser','session','edit persistence','logout','mobile filters','mobile profile']}
  (ARTIFACTS/'browser-results.json').write_text(json.dumps(report,indent=2))
  print(json.dumps(report,indent=2))
  browser.close()

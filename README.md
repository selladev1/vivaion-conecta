# Vivaion Conecta

Primeira versao funcional de demonstracao de um diretorio de profissionais da saude.
Busca por linguagem cotidiana, filtros, perfis e painel profissional, com baixo consumo.

**Somente testes.** Os 40 usuarios e seus perfis sao ficticios. Nenhum CPF, registro de conselho,
contato, certificado, aluno ou paciente real foi usado. Nao ha atendimento, diagnostico,
agendamento ou contato real. O cadastro publico e o SSO academico ainda nao foram implementados.

## Executar localmente

Requer Python 3.12 ou 3.13. Nao precisa de Node, build frontend, Redis ou Docker para executar.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.lock
python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8080 --workers 1 --no-access-log
```

Abra `http://127.0.0.1:8080`. O banco local `var/conecta-demo.sqlite3` nasce com 40 contas.
O seed e idempotente: reiniciar nao duplica usuarios nem apaga edicoes.
Clique em **Sou profissional**, escolha uma conta ficticia e teste a edicao do perfil.
As sessoes duram uma hora. Nao use dados reais.

## O que funciona

- Busca por texto, area, tema, cidade/UF, faixa etaria, modalidade e disponibilidade simulada.
- 16 perfis de Fonoaudiologia, 12 de Psicologia, 4 de Terapia Ocupacional, 4 de Nutricao e 4 de Fisioterapia.
- CAA, linguagem, fala, voz, motricidade, disfagia, infancia, ansiedade, dependencias, trabalho, alimentacao e reabilitacao.
- Paginas de perfil em dialogo acessivel, formacoes ficticias, interesse simulado e painel de edicao persistente.
- Paginacao, estados vazios, avisos de seguranca, resposta a falha de rede e interface responsiva.
- IA local opcional, desligada por padrao. Busca normal nunca chama Ollama.

## Arquitetura inicial

Frontend HTML/CSS/JavaScript sem dependencias de execucao ou recursos de terceiros.
Backend FastAPI/Uvicorn, um processo. SQLite WAL isolado APENAS para demonstracao,
com catalogo em memoria e invalidacao apos edicoes. Nao toca no PostgreSQL academico.
Nao e necessario iniciar Redis para esses 40 perfis.

A escolha de SQLite para o piloto reduz a necessidade de provisionamento. Ela nao altera
o plano de usar o PostgreSQL existente, com credenciais e esquema proprios, antes de
ativar cadastros reais ou multiplos processos. A migracao ainda precisa ser implementada
e validada: nao esta automatizada nesta versao.

## IA: opcional e limitada

`OLLAMA_ENABLED=false` e o padrao. Quando habilitada pelo operador, o botao de IA exige
consentimento para um exemplo ficticio. Primeiro tenta regras; apenas consultas desconhecidas
podem chegar ao Qwen. Resultados gerados exigem confirmacao humana antes de aplicar filtros.

- Modelo inicial configuravel: `qwen2.5:3b`, sem baixar modelo automaticamente.
- Apenas endereco IP literal loopback, sem redirects ou proxies de ambiente.
- Um pedido por vez e sem fila no aplicativo; indisponibilidade retorna aos filtros.
- Prazo total de 6 s, contexto 2.048, saida 96 tokens, 4 threads solicitadas.
- Cache volatil limitado a 128 classificacoes por 5 minutos, chaves HMAC por processo.
- Cooldown de 30 s apos falha; timeout do cliente nao prova que Ollama interrompeu a geracao.
- JSON Schema fechado: somente IDs de temas autorizados. Sem SQL, ferramentas, PII ou acesso ao banco para a IA.

O modelo REAL da VPS ainda NAO foi ensaiado nesta versao. Testes de IA usam respostas simuladas.
A taxonomia e as regras de descoberta precisam de revisao profissional. O aviso de urgencia
nao constitui triagem e nao detecta todos os riscos.

## Testar

```sh
python -m pip install -r requirements-dev.txt
pytest -q
node --check public/assets/app.js
python tools/benchmark.py
```

O benchmark inicia e encerra um servidor LOCAL descartavel. Faz 120 buscas, no maximo 10 em paralelo,
com IA desligada e sem acessar a VPS. Nao e uma garantia de capacidade em producao.

Teste visual opcional (Playwright e Chromium somente no ambiente de desenvolvimento):

```sh
python -m pip install playwright==1.57.0
CHROMIUM_PATH=/usr/bin/chromium python tools/browser_smoke.py
```

O teste visual usa navegador offline e a API ASGI real dentro do processo. Nao confirma DNS,
TLS, cookies no proxy publico, deploy ou conexao com Ollama. Os testes de cookies, CSRF,
validacao de entradas e acesso restrito sao exercitados separadamente pela suite HTTP.

## Publicacao de teste: bloqueada no MCP

Em 05/11/2026, o MCP retornou:

- `work_resume(project_id="vivaion-conecta")`: nenhum workspace registrado.
- `release_workflow(action="catalog")`: somente mcp, unyom e vivian-lab configurados.
- `staging_provision(project_id="vivaion-conecta")`: `staging_project_disabled`.

Portanto esta entrega **nao foi publicada online** e nao alterou o servidor da Vivaion.
Nao ha URL de homologacao validada. `conecta-hml.vivaion.com.br` nos templates e apenas uma proposta.
Os arquivos em `ops/` sao templates, nao comandos ja aplicados.

O operador precisa registrar o repositorio e workspace, habilitar staging isolado,
provisionar DNS/TLS e instalar a configuracao sob a politica de autorizacao do MCP.
Nao reutilizar o ambiente Unyom ou tocar na Area do Aluno/checkout para contornar esse bloqueio.
Veja `docs/OPERACAO.md` e `docs/ACEITE.md`.

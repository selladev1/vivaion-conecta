# Operacao e crescimento

## Contrato do ambiente de homologacao

Repositorio: selladev1/vivaion-conecta. Branch de desenvolvimento: mcp/conecta-demo-mvp.
O projeto ainda precisa ser admitido no MCP. Nenhuma permissao e concedida por estes arquivos.

Configurar pelo operador, fora do Git:

- APP_ENV=staging
- APP_ORIGINS com a origem HTTPS exata do novo subdominio, sem wildcard ou caminho.
- DEMO_ACCESS_TOKEN aleatorio com pelo menos 24 caracteres. Guardar em arquivo 0600.
- DATABASE_PATH em diretorio proprio e local, nunca no banco da plataforma academica.
- OLLAMA_ENABLED=false inicialmente.

O usuario do acesso HTTP Basic e `demo`; a senha e o segredo criado pelo operador.
Sem segredo e origem HTTPS validos, staging recusa iniciar. Todos os perfis permanecem ficticios.
Nao divulgar o segredo no Git, issue, PR, chat publico ou screenshot.

O template systemd usa loopback na porta 8088, DynamicUser, um worker, cota inicial de 1 CPU,
MemoryHigh de 192 MiB e limite de 384 MiB. Sao limites PROPOSTOS, nao recursos ja alocados.
Confirmar disponibilidade de porta e compatibilidade do sistema antes de instalar.
O proxy Apache deve ser NOVO e independente. Nao editar os VirtualHosts academicos.

Publicar artefato imutavel, verificar hash/commit e guardar versao anterior para rollback.
Validar a URL real com senha, TLS, cookies Secure, CSRF, ausencia de indexacao, filtros,
login demo, edicao e logout antes de informar que o site esta online.

## Privacidade e seguranca

A demo rejeita padroes comuns de documento, telefone e e-mail em consultas; isso nao garante
anonimizacao. O uso de dados reais e proibido, inclusive no texto livre do painel.
Buscas nao sao gravadas no banco, localStorage, URLs ou analytics. Nao registrar corpos de requisicao.
A configuracao de proxy limita logs a rota, metodo, status e tempo; revisar logs globais do host.
Cookies de sessao: HttpOnly, SameSite=Strict, Secure em staging, uma hora de duracao.
Tokens de sessao sao armazenados por hash. Edicoes exigem sessao, origem exata e token CSRF.
Rate limits volateis: 180 chamadas API/minuto/IP, 15 criacoes de sessao/minuto/IP e 6 pedidos IA/minuto/IP.
Esses limites sao por processo; usar somente um worker. NAT compartilhado pode precisar de ajuste.
Nenhuma conta demo e prova de identidade, registro profissional, habilitacao ou vinculo academico.

## Quando ampliar

Medir latencia p50/p95, erros, taxa de bloqueio, CPU, RAM, consultas/minuto e filas.
Nao dimensionar por numero de visitantes isoladamente. Uma meta inicial de busca sem IA
p95 <300 ms na VPS e uma META de aceite, nao resultado ja medido.

Antes de contas reais: PostgreSQL isolado com migracoes e backup/restauracao testados,
autenticacao real (OIDC quando houver contrato de identidade), autorizacao explicita para
vincular conta de aluno, verificacao de e-mail, revisao de credenciais, fluxo de moderacao,
tratamento de exclusao/retencao e revisao juridica/clinica. CPF e documentos exigem desenho
especifico de minimizacao, acesso, criptografia e armazenamento privado; nao usar campos
publicos nem reaproveitar o banco demo para isso.

Quando houver multiplos workers/replicas: estado compartilhado para sessoes, rate limiting,
cache e limitador GLOBAL do Ollama. Adicionar Redis apenas nessa fase ou quando a medicao justificar.
Separar a IA em servico dedicado/GPU se benchmarks reais mostrarem que e necessario.
Nao aumentar paralelismo do Ollama apenas porque existe RAM livre.

## Referencias tecnicas

- https://www.sqlite.org/whentouse.html
- https://www.sqlite.org/wal.html
- https://fastapi.tiangolo.com/deployment/manually/
- https://docs.ollama.com/capabilities/structured-outputs
- https://docs.ollama.com/api/chat

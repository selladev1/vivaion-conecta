# Ativacao de ambiente proprio — Vivaion Conecta

**Estado:** instrucoes de provisionamento, NAO ambiente criado ou politica instalada. Documento para operador autorizado. A VPS nao deve ser alterada fora de uma sessao administrativa assinada e valida.

## Identidade e limites

| Item | Valor |
| --- | --- |
| Project ID MCP | `vivaion-conecta` |
| Repositorio | `selladev1/vivaion-conecta` |
| Branch com o MVP | `mcp/conecta-demo-mvp` |
| Commit inicial revisado | `8870a437595abba0464c4813efa356b6f5e557c3` (substituir pelo HEAD verificado ao implantar) |
| Subdominio staging proposto | `conecta-hml.vivaion.com.br` (nao publicado/validado) |
| Subdominio de producao futuro | `conecta.vivaion.com.br` (nao implantar agora) |
| Porta loopback sugerida | `127.0.0.1:8088`, verificar livre |
| Ollama interno | `127.0.0.1:11434`, nunca expor publicamente |
| Modelo inicial | `qwen2.5:3b` |
| Dados | 40 perfis FICTICIOS, SQLite para piloto, sem conexao ao cadastro de alunos |
| Controles de IA | Desligada inicialmente, 1 requisicao por vez, timeout de 6s, fallback |

## Operacoes de admissao pelo administrador da VPS/MCP

1. Obter autorizacao do **Root Operator** pelo protocolo existente de desafio + assinatura humana offline Ed25519. Um pedido pendente nao concede acesso. Nunca copiar chave privada ou assinatura para Git.
2. Verificar repositorio, HEAD e integridade da branch; admitir o novo repositorio no catalogo de desenvolvimento com workspace exclusivo, sem compartilhar a workspace `unyom`.
3. Registrar projeto `vivaion-conecta` no catalogo de releases do MCP e vincular exclusivamente esse repositorio. Configurar staging proprio e permissoes de release; aprovar explicitamente as acoes minimas no operador. **Nao editar manualmente os arquivos internos do MCP sem conhecer o schema/politica vigente.**
4. Preparar diretorio de artefatos e dados exclusivos do projeto (exemplo: `/srv/vivaion-conecta`, `/var/lib/vivaion-conecta-demo`), identidades e permissoes minimas. Nao reutilizar banco da plataforma academica ou do Unyom.
5. Verificar se a porta `8088` esta livre e se Python/venv e dependencias do `requirements.lock` estao presentes. O arquivo `ops/conecta-demo.service` e um **template**, nao instalacao automaticamente autorizada.
6. Configurar em arquivo protegido (0600), nao versionado:
   `APP_ENV=staging`;
   `APP_ORIGINS=https://conecta-hml.vivaion.com.br`;
   `DATABASE_PATH=/var/lib/vivaion-conecta-demo/conecta.sqlite3`;
   `DEMO_ACCESS_TOKEN=<segredo aleatorio exclusivo de pelo menos 24 caracteres>`;
   `OLLAMA_ENABLED=false`;
   `OLLAMA_URL=http://127.0.0.1:11434`;
   `OLLAMA_MODEL=qwen2.5:3b`.
   O aplicativo nao carrega .env automaticamente: o servico deve carregar o arquivo de ambiente.
7. Criar service/VHost **novos**, em paths exclusivos; verificar DNS e obter TLS antes de habilitar staging. `ops/apache-staging.conf.example` e template que exige certificado valido. Nao alterar VirtualHosts academicos existentes.
8. Usar **staging_provision**, release e validacao do MCP apos admissao. Preferir artefatos imutaveis e rollback independente.
9. Validar URL HTTPS (nao basta um processo ativo), autenticacao Basic exclusiva, 40 perfis sinteticos, buscas, filtros, edicao da conta demo, encerramento da sessao, CSP, noindex, CSRF, rate limits e logs sem queixas/PII.
10. Monitorar memoria, CPU, p95, erros e impacto nos servicos existentes; meta de busca sem IA p95 inferior a 300ms na VPS e **criterio a medir**, nao medicao obtida.
11. Somente apos aceite do staging sem IA, testar o Qwen em consultas inteiramente ficticias, verificar `qwen2.5:3b` em `/api/tags`, medir latencias e carga. Habilitar `OLLAMA_ENABLED=true` apenas se testes forem satisfatorios; manter fallback e nao alterar paralelismo do Ollama global.

## Evidencia e bloqueio confirmado em 05/11/2026

- `staging_provision(project_id="vivaion-conecta")` -> `staging_project_disabled`.
- `release_workflow(action="catalog")` -> apenas `mcp`, `unyom`, `vivian-lab`.
- `ollama.service` -> ativo.
- `vivaion_root_status` -> sessao administrativa **inativa**.
- `vivaion_root_session_prepare` criou um desafio com `state=AWAITING_APPROVAL`, que **nao** representa autorizacao. Como expira, um desafio novo pode ser necessario no momento da assinatura.

## Revalidacao do MCP em 06/11/2026

- `vivaion_access_status(project_id="vivaion-conecta")` reportou o worker de engenharia saudavel, mas a publicacao continua bloqueada por `RAPID_ADMISSION_NOT_VERIFIED` e `PRODUCTION_AUTHORIZATION_NOT_VERIFIED`.
- `release_workflow(action="catalog")` continua sem `vivaion-conecta`: os unicos projetos configurados sao `mcp`, `unyom` e `vivian-lab`. Portanto nao existe candidato, workspace de release ou ambiente de staging oficial para este projeto.
- `release_session_catalog()` confirmou que a sessao de release isolada possui somente `unyom` como projeto admitido e nao oferece acoes para o Conecta.
- `autonomy_readiness(project_id="vivaion-conecta")` nao encontrou bloqueio de saude do worker, mas tambem nao prova homologacao nem admissao RAPID. Isto nao autoriza provisionamento, deploy, DNS, TLS, reinicio ou uso de rotinas de outro projeto.

**Dependencia objetiva:** um operador com autoridade de administracao da plataforma precisa admitir `selladev1/vivaion-conecta` como projeto isolado, criar/vincular seu workspace e contrato de release e habilitar o staging proprio no catalogo RAPID. Depois da admissao, o fluxo permitido comeca por `staging_provision` e pela preparacao de candidato; antes disso, chamadas de staging devem continuar falhando de forma segura com `staging_project_disabled`.

## Condicoes para afirmar "online"

Apenas quando houver provisionamento confirmado, release implantada, URL publica de staging HTTPS acessivel, verificacao da build servida, autorizacao do operador e teste real concluido. Antes disso, nao divulgar URL como operacional.

**Proibido nesta fase:** dados reais, diagnostico clinico, divulgacao de perfis nao verificados, integracao com login academico/checkout, deploy de producao, exposicao da porta Ollama na internet e uso de credenciais de outro projeto.

Referencias: [README](../README.md), [Operacao](../docs/OPERACAO.md), [Aceite](../docs/ACEITE.md), [service template](conecta-demo.service), [Apache template](apache-staging.conf.example), [Issue de provisionamento](https://github.com/selladev1/vivaion-conecta/issues/2).

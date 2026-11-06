# Criterios de aceite da primeira demonstracao

## Validados localmente

### Busca automática e animação dos resultados — 06/11/2026

- A rota `/api/search` agora usa regras determinísticas primeiro e, com o consentimento único da página, consulta a IA local somente para texto sem correspondência confiável. A sugestão validada é aplicada na própria resposta; não existe confirmação posterior no cliente.
- Temas originados pela IA são apresentados como filtros removíveis. Removê-los desativa a IA para aquela consulta e preserva a busca por filtros.
- Os resultados de uma pesquisa submetida entram uma única vez na grade e são animados com Web Animations API: começam como cartas sobrepostas e inclinadas na base da caixa de busca, depois chegam às células finais. A animação é cancelada em uma nova busca, torna os cards inertes enquanto ocultos e respeita `prefers-reduced-motion`.
- Suite local: 80 testes aprovados; `node --check public/assets/app.js` e `git diff --check` aprovados. Validação em navegador local confirmou a busca determinística “Meu filho de 4 anos fala poucas palavras” com cinco perfis e a mensagem de tema correspondente.
- A IA real/Qwen, CPU/RAM na VPS, DNS/TLS e publicação continuam pendentes de um projeto de staging autorizado no MCP.

- 40 usuarios e 40 perfis sinteticos; seed idempotente e preservacao de edicoes.
- Distribuicao: 16 fono, 12 psicologia, 4 terapia ocupacional, 4 nutricao, 4 fisioterapia.
- Busca por temas, modalidade, local e idade; paginacao sem duplicatas.
- Nenhum contato real, numero de conselho, CPF ou certificado real.
- Sessao demo, edicao persistente apenas do proprio perfil, CSRF e logout.
- Rejeicao de categorias inexistentes, payload excessivo, origem indevida e padroes de PII.
- Nenhum texto da busca persistido no banco.
- IA desligada por padrao; cache, schema, falhas, timeout, consentimento e ocupacao com mocks.
- 72 testes automatizados aprovados.
- 15 cenarios de navegador offline + API ASGI real aprovados, desktop 1440 e mobile 390 px.
- Sem erro JavaScript ou overflow horizontal observado nesses dois tamanhos.
- 120 chamadas HTTP locais com 10 simultaneas: 120 respostas 200 e zero chamadas Ollama.

Os valores exatos de tamanho e latencia estao em benchmark-local.json. O RSS reportado e
uma amostra apos carga, nao pico nem compromisso de consumo. Nao extrapolar para a VPS.

## Ainda nao validado / nao implementado

- Deploy online: MCP retornou staging_project_disabled; nao ha URL validada.
- DNS, TLS e proxy publico do novo subdominio.
- Inferencia e concorrencia reais do Qwen na VPS.
- Integracao da conta Vivaion, cadastro publico, uploads e revisao de documentos.
- Verificacao profissional, consentimentos reais, SSO e registro de titulos reais.
- Contatos/agenda/pagamentos reais e aptidao regulamentar de teleatendimento.
- Migracao de SQLite demo para PostgreSQL, multiprocessamento e Redis compartilhado.
- Auditoria clinica, juridica, acessibilidade completa e pentest independente.

Uma publicacao futura exige novo aceite do artefato servido. Testes locais ou um commit
no GitHub nao equivalem a homologacao da VPS, merge aprovado ou deploy.

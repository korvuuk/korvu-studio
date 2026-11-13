# Especificação — estudio-contexto (grafo + busca vetorial + servidor MCP)

> Documento de entrada para o agente construtor. Estado: **aprovada pelo autor em 12/11/2026**; a execução é
> delegada a um agente construtor no Claude Code. Escrito em 12/11/2026 a partir da leitura do estúdio (`Korvu Studio/`) e de `painel/`.

## 0. Resumo para quem assume

- **O que é:** um módulo de contexto para o estúdio Korvu Studio, com grafo de entidades, busca vetorial local e um servidor MCP somente leitura para os agentes.
- **Onde fica:** `Korvu Studio/estudio-contexto/` (este arquivo). O código ainda não existe; esta pasta é o ponto de partida.
- **O que está aprovado (12/11/2026):** modelo `intfloat/multilingual-e5-small`; pasta de trabalho; registro do servidor MCP no `.mcp.json` da raiz; agentes que consultam o contexto: `diretor`, `portao-dados` e `roteirista`.
- **Próximo passo:** seção 10, passo 1. Criar `projetos.yaml` e `corpus.yaml`, e parar para aprovação do mapa antes de qualquer indexação.
- **Restrições que não mudam:** tudo local; banco do painel nunca alterado; portas 553xx (nunca 543xx); nenhum segredo indexado; nenhuma escrita fora de `estudio-contexto/` sem aprovação.
- **Pendências que bloqueiam o projeto interno:** nenhuma.
- **Adiado (portfólio e publicação, só depois do projeto interno):** destino do histórico do repositório; retirar dados de conta e retratos do git; campo `email` em `pyproject.toml`. Detalhes na seção 14.
- **Onde estão os detalhes:** ontologia na seção 5, indexação na seção 6, segurança na seção 7, ferramentas do MCP na seção 8, avaliação na seção 9, handoff na seção 15.

## 1. Por que existe

Hoje os agentes **não usam grafo nem banco vetorial**. A memória e o estado são arquivos (`CLAUDE.md`, `status.json`,
`portoes.json`, `_controle/`, relatórios em `painel/portoes/`). O banco do painel (`painel/supabase/`) só é consultado
pelo `portao-dados`, e para auditar, não para trabalhar. O `HANDOFF.md` (linha 40) já registra
que o projeto não usa grafo nem banco vetorial.

Este módulo cria a camada de **contexto** que os agentes passam a consultar: um grafo de entidades do estúdio
(projetos, agentes, vídeos, portões, veredictos, decisões) e uma busca semântica sobre o texto do projeto, expostos
por um servidor MCP **somente leitura**.

Problema que resolve: o autor precisa repetir contexto toda vez ("o que já foi decidido sobre X?", "quem bloqueou
vídeos parecidos?", "esta mudança afeta qual projeto?"). O agente deve conseguir perguntar isso sozinho.

## 2. Escopo

**Dentro:**
- Mapa dos projetos do estúdio (`estudio-contexto/projetos.yaml`) com áreas e dependências.
- Grafo de entidades e relações, derivado de arquivos e das tabelas do painel.
- Indexação de texto: `CLAUDE.md` (raiz e de cada projeto), `README.md` do painel, `docs/`, `docs/decisoes.md`,
  `HANDOFF.md`, `_controle/backlog-portoes.md`, relatórios de `painel/portoes/`, roteiros e briefs de `videos/*`.
- Embeddings locais e busca híbrida (vetorial + texto).
- Servidor MCP somente leitura com ferramentas de contexto.
- Testes.

**Fora (não fazer):**
- Mídia: `videos/`, `07-publicados/`, `05-render-pronto/`, `BG VIDEO/`, `*.mp4`, `*.mov`, `*.wav`, `*.mp3`.
- Dependências e vendor: `node_modules/`, `.venv/`, `.git/`, `.next*/`, `.claude/skills/` (documentação de terceiros).
- **Segredos:** `.env`, `.env.*`, `painel/web/.env.local` e qualquer arquivo cujo conteúdo traga token ou chave. Ver §7.
- Escrita em qualquer projeto. O módulo só lê.
- Publicação no GitHub. Fica para depois, em etapa própria.

## 3. Restrições do projeto (obrigatórias)

- **Local.** Nada vai para a nuvem. O plano grátis do Supabase está ocupado; o banco é o Postgres local do painel
  (`127.0.0.1:55322`, projeto `korvu-studio-painel`). Não criar projeto na nuvem.
- **Portas:** 553xx, nunca 543xx (outro projeto local).
- **Escopo de escrita:** esta pasta (`estudio-contexto/`). Alterações em `painel/` exigem aprovação do autor e
  passam pelo GAUNTLET do painel (`uv run python scripts/portoes.py exigir painel`). Alterações em
  `Korvu Studio/.claude/agents/` e `Korvu Studio/.mcp.json` exigem aprovação explícita (são de outros projetos/agentes).
- **Fonte da verdade continua sendo os arquivos.** O índice e o grafo são derivados e reconstruíveis do zero.
- **O banco do painel nunca é alterado por este módulo.** Criar um schema próprio (`contexto`) no mesmo Postgres,
  sem tocar nas tabelas `public` do painel.
- **Custos:** nenhum custo de API. Modelo de embedding local.

## 4. Decisões

| Item | Decisão | Status |
|---|---|---|
| Modelo de embedding | `intfloat/multilingual-e5-small` (384 dimensões, ~470 MB), via `sentence-transformers`, rodando no MPS do M1 | aprovado pelo autor |
| Prefixos do e5 | `passage: ` ao indexar, `query: ` ao buscar | fixo (exigido pelo modelo) |
| Armazenamento vetorial | extensão `pgvector` no Postgres local, schema `contexto`, coluna `vector(384)`, índice HNSW | proposta |
| Grafo | tabelas `contexto.nos` e `contexto.arestas`, consulta recursiva (`WITH RECURSIVE`) | proposta |
| Busca textual | `tsvector` com configuração `portuguese` | proposta |
| Fusão de resultados | RRF (Reciprocal Rank Fusion) entre busca vetorial e textual | proposta |
| Interface com agentes | servidor MCP em Python (FastMCP), somente leitura | proposta |
| Localização do código | `Korvu Studio/estudio-contexto/` | aprovado pelo autor |
| Registro no `.mcp.json` da raiz | novo servidor ao lado do `davinci-resolve` | aprovado pelo autor |

Justificativa do modelo: o corpus de texto é da ordem de poucos megabytes (cerca de 1.000 a 3.000 trechos). Um
modelo pequeno é suficiente, roda leve e não exige a memória do M1. Se a qualidade ficar insuficiente na avaliação
(§9), a troca para `bge-m3` (1024 dimensões) é uma mudança de configuração e de migração do schema, não de arquitetura.

## 5. Ontologia do grafo

### Nós (`contexto.nos`)

| tipo | exemplo | origem |
|---|---|---|
| `projeto` | painel, criação de vídeo, agendador | `projetos.yaml` |
| `agente` | `portao-dados`, `roteirista` | `.claude/agents/*.md` e `painel/equipe.yaml` |
| `departamento` | tecnologia, pesquisa | `painel/equipe.yaml` |
| `video` | slug de `videos/` | pastas de `videos/` e `painel.videos` |
| `publicacao` | item de `07-publicados/` | `painel.publicacoes` |
| `portao` | `portao-dados`, `portao-pauta` | `painel.portoes_estado` |
| `veredicto` | resultado de uma passagem de portão | `painel.veredictos` |
| `decisao` | PD9, PD12, PD20, PD23… e entradas de `docs/decisoes.md` | README do painel, `docs/decisoes.md` |
| `documento` | um arquivo indexado | caminho do arquivo |
| `trecho` | um pedaço de documento (ligado ao documento) | chunking (§6) |

### Arestas (`contexto.arestas`)

| tipo | de → para | origem |
|---|---|---|
| `pertence_a` | projeto → projeto (sub-área); agente → projeto | `projetos.yaml`, `equipe.yaml` |
| `gerencia` | agente → departamento | `departamentos.gerente_id` |
| `fiscaliza` | portão → agente | `agentes.fiscalizado_por` (inversa) |
| `avalia` | portão → video | `portoes_estado` |
| `bloqueou` / `aprovou` | veredicto → video | `veredictos.resultado` |
| `publicado_como` | video → publicacao | `publicacoes.video_slug` |
| `medido_por` | publicacao → metrica (valor, não nó) | `metricas` |
| `decide_sobre` | decisao → projeto/video/agente | texto das decisões |
| `depende_de` | projeto → projeto | `projetos.yaml` |
| `menciona` | documento → entidade | busca por slug, PD, nome de agente |
| `contem` | documento → trecho | chunking |

Regra de derivação: a tabela `contexto.arestas` é **recalculada por completo** a cada passagem do sincronizador de
contexto (mesmo princípio do sincronizador do painel). Não há edição manual.

## 6. Indexação de texto

- **Corpus:** lista explícita de caminhos (§2), não um `**/*` que pegue tudo. A lista fica em
  `estudio-contexto/corpus.yaml`.
- **Chunking:** markdown por seção (`##`), com limite de tamanho; YAML e JSON por item de primeiro nível; trecho
  guarda: caminho, seção, tipo, data (se houver), PD (se houver), hash do conteúdo.
- **Reindexação incremental:** calcular o hash do texto de cada trecho. Reembedar só os trechos com hash novo ou
  alterado. Remover trechos que sumiram do arquivo. Nunca apagar a tabela inteira.
- **Prefixo:** `passage: ` antes de cada trecho na indexação.
- **Busca:** `query: ` antes da pergunta; busca vetorial (top-k) + busca textual (top-k); fusão RRF; depois expansão
  pelo grafo (vizinhos dos documentos encontrados, até profundidade 1).
- **Filtros:** por projeto, por tipo de nó, por agente, por intervalo de datas.

## 7. Segurança e privacidade

- **Lista de exclusão no código**, com `.env`, `.env.*` e `painel/web/.env.local`, além de padrões de token.
- **Teste obrigatório:** o índice não pode conter nenhum valor de variável do `.env` (o teste lê as chaves do `.env`,
  nunca imprime os valores, e confere que nenhum trecho contém esses valores).
- **Respostas do MCP:** nunca devolver conteúdo de arquivos excluídos, mesmo que estejam no disco.
- **Segredos no código:** nenhum. O MCP lê credenciais do ambiente, e o `.env` não é lido pelo módulo.
- **Repositório:** `korvuuk/korvu-studio-ai` é público (informado pelo autor; não verifiquei por conta própria). Ver §14 antes de qualquer outra exposição.
  foi verificada ainda (ver `HANDOFF`/pendência do autor). Tokens da Meta, R2 e LinkedIn são o principal risco.

## 8. Servidor MCP — ferramentas

Todas somente leitura. Nenhuma faz escrita, nenhuma chama API externa.

| Ferramenta | Entrada | Saída |
|---|---|---|
| `contexto_do_projeto(projeto)` | nome | área, dependências, agentes, documentos principais, decisões ligadas |
| `contexto_do_video(slug)` | slug | estado, portões e veredictos, decisões, publicação e métricas se houver |
| `buscar(consulta, projeto?, tipo?, limite?)` | texto | trechos com caminho, seção, trecho curto e nós ligados |
| `vizinhos(no, profundidade?)` | id ou nome do nó | nós e arestas ao redor |
| `decisoes_sobre(tema)` | texto | decisões (PD…) e trechos que as citam |
| `quem_fiscaliza(agente)` | nome | portão responsável e veredictos recentes |

Cada resposta traz o caminho da fonte. O agente deve citar o caminho ao usar a informação.

Registro: `Korvu Studio/.mcp.json`, depois de aprovação (⚠️).

## 9. Avaliação (critério de aceite)

Construir um conjunto de **30 perguntas com resposta conhecida**, tiradas do próprio estúdio (ex.: "qual foi a
decisão sobre o portão de publicação em 23/10?", "quais vídeos o portão-dados bloqueou?"). Medir:

- **Recall@5** da busca híbrida: alvo ≥ 0,8.
- **Respostas corretas com a fonte certa:** alvo ≥ 80%.
- **Vazamento:** zero trechos de `.env` e zero de mídia.

Se o recall ficar abaixo do alvo, a primeira ação é ajustar o chunking e o uso do grafo na expansão. Só depois
trocar o modelo.

## 10. Plano de execução (ordem)

1. **Mapa do estúdio**: criar `projetos.yaml` e `corpus.yaml` e submeter ao autor antes do passo 2.
2. **Schema `contexto`** no Postgres local: `nos`, `arestas`, `documentos`, `trechos` (com `vector(384)`, índice
   HNSW e `tsvector`). Migração versionada em `estudio-contexto/migrations/`.
3. **Grafo** derivado das tabelas do painel e dos arquivos. Consulta de vizinhança testada.
4. **Indexação** de texto com embeddings locais e reindexação incremental.
5. **Busca híbrida** com RRF e expansão pelo grafo.
6. **Servidor MCP** (ferramentas da §8), com testes.
7. **Avaliação** (§9) e ajustes.
8. **Integração**: registrar no `.mcp.json` e atualizar os agentes que devem consultar o contexto (aprovação).

Fora deste plano, e só depois da aprovação do autor: publicação no GitHub e documentação de uso para terceiros.

## 11. Testes

- Unitários: chunking, hash, derivação de arestas, RRF, filtros.
- Integração: banco temporário (`create database contexto_teste`), migrações do zero, indexação, consultas.
- Segurança: teste de vazamento de `.env` e de mídia (ver §7).
- Idempotência: rodar a indexação duas vezes não muda nada.
- Padrão: seguir `painel/tests/test_sincronizar.py` (banco temporário, nunca o banco de produção).

## 12. Critérios de pronto

- Plano de execução concluído até o passo 6.
- Avaliação (§9) com os alvos atingidos, ou com as lacunas registradas e aprovadas pelo autor.
- Testes passando.
- Portão aplicável aprovado (o `portao-dados` para o schema e o sincronizador, se tocar em `painel/`).
- `HANDOFF.md` atualizado com o que foi feito e o que não foi verificado.

## 13. Decisões tomadas em 12/11/2026

- Modelo `multilingual-e5-small`: aprovado.
- Pasta `Korvu Studio/estudio-contexto/` como local do código: aprovada.
- Registro do servidor MCP no `.mcp.json` da raiz: aprovado.
- Agentes que passam a consultar o contexto: `diretor`, `portao-dados` e `roteirista`.
- Repositório `korvuuk/korvu-studio-ai`: público, segundo o autor.
- Criação de `projetos.yaml` e `corpus.yaml`: delegada ao agente construtor. O mapa passa pela aprovação do autor antes do passo 2.

## 14. Achados de segurança no repositório público (verificados em 12/11/2026)

Verificação feita com `git ls-files`, `git grep` e `git show`. Nenhum valor foi copiado para este documento.

- **Tokens nos testes** (`tests/comentarios/test_responder.py`, `tests/metricas/test_metricas.py`, `tests/publicar/test_publicar.py`): são valores fictícios (contêm palavras como "SEGREDO" e sequências óbvias). Não são credenciais reais. Verificado.
- **Padrão `sk-`** em `01-ideias/`: falsos positivos, pegos dentro de palavras e URLs. Verificado.
- **Chaves e `.env`:** `.env` e `painel/web/.env.local` não estão versionados nem aparecem no histórico. Verificado.
- **Dado de contato pessoal no histórico (ação necessária):** o commit inicial (`67c894c`) contém um dado de contato pessoal que foi removido do arquivo atual no commit `71522e0`, mas continua no histórico público. Segundo o autor, o contato não está mais em uso. Removido de `linkedin/perfil-final-2026-10-23.md` e `00-marca/sobre-autor.md`. Ainda aparece em `pyproject.toml` (campo `email` de `authors`), que precisa de decisão antes da publicação.
- **Dados de conta versionados:** `07-publicados/*/metricas.json`, `_controle/perfil/*.json` e prints em `_controle/perfil/prints-2026-10-17/`. Não verificado se há dado pessoal além de métricas.
- **Retratos** em `painel/design/telas/img/retratos/` (10 arquivos). Não verificado se são fotos de pessoas reais.

Itens de publicação, **adiados** (não bloqueiam o projeto interno). Ordem quando retomar:

1. **[CONCLUÍDO pelo autor em 12/11/2026, 10:13]** Repositório privado. Não verificado por ferramenta: a leitura anônima da página falhou com erro de cliente, compatível com privado. Conferir no GitHub antes de confiar.
   Detalhe original: `korvuuk/korvu-studio-ai`: GitHub → Settings → Danger Zone → Change visibility → Private. É reversível e reduz a exposição imediatamente. Não remove cópias já feitas enquanto ele esteve público. Decisão do autor; quem executar confirma com ele antes.
2. **Decidir o destino do histórico.** Para o portfólio, criar um repositório novo com histórico limpo, começando só pelos arquivos do núcleo. Não reaproveitar o histórico atual. Enquanto o atual estiver privado, ele pode continuar como arquivo interno.
3. **Retirar do índice do git** os dados de conta (`07-publicados/*/metricas.json`, `_controle/perfil/*.json`, prints de perfil) e os retratos em `painel/design/telas/img/retratos/`, e incluí-los no `.gitignore`. Antes, verificar se os retratos são fotos de pessoas reais.
4. **Remover o campo `email` de `authors` em `pyproject.toml`**, se o autor confirmar. Ainda está no histórico, como os demais itens.
5. **Só depois dos itens 1 a 4**, publicar o núcleo em um repositório público novo.

Não há chaves reais expostas: os tokens em `tests/` são fictícios e os casos `sk-` são falsos positivos (verificado em 12/11/2026).

## 15. Handoff para o agente construtor

- **Onde executar:** a partir de `Korvu Studio/`, não de `painel/`, porque o `CLAUDE.md` de `painel/` restringe a escrita.
- **Primeiro:** ler esta especificação inteira e a seção 14 antes de alterar qualquer arquivo.
- **Passo 1 (seção 10):** criar `projetos.yaml` e `corpus.yaml` e parar para aprovação do autor.
- **Passos 2 em diante:** só depois da aprovação do mapa.
- **Não fazer:**
  - escrever em `videos/`, `07-publicados/`, `_controle/` ou `scripts/`;
  - alterar `painel/` sem passar pelo GAUNTLET;
  - ler o `.env` ou indexar mídia;
  - criar projeto na nuvem;
  - reescrever o histórico do git sem pedido explícito.
- **Ao concluir cada passo:** relatar o que foi verificado e o que não foi.

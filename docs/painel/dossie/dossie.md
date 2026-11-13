# Dossiê técnico — korvu. painel

> Levantado pelo `documentador-tecnico` em 12/11/2026, lendo o código. Cada afirmação cita o arquivo de onde saiu
> (caminhos relativos à raiz do projeto). O que não deu para confirmar está na seção 12. Material bruto para o
> `designer-de-documentacao` — não é a documentação final.
>
> **Capturas:** `capturas/` — fotos do **app rodando** em `http://localhost:3456` (respondeu HTTP 200 em 12/11, 16:15 UTC),
> tiradas com `bash painel/capturar.sh … --escala 2`, a 1440 px e a 375 px, página inteira. Medidas de cada foto em
> `capturas/medidas.txt` (nenhuma página com rolagem lateral). Não são maquetes.

---

## 1. O que é o painel

O painel é o "quadro de comando" do estúdio de Reels Korvu Studio: um site que roda no próprio Mac e mostra, numa olhada,
quem é quem na equipe de agentes de IA, em que fase está cada vídeo, se os portões de aprovação (o GAUNTLET) deixaram o
trabalho passar, o que vai ser publicado e quando, como os vídeos estão indo no Instagram e no Facebook, e quanto a
operação de IA consome em tokens e dólares. É feito para uma pessoa: o dono do estúdio (`painel/README.md`,
`painel/design/telas/*.md` — "O autor abre isto para…").

**O que ele NÃO faz:** não cria, não edita e não publica nada. Os arquivos do projeto são a fonte da verdade; o painel só
lê (`painel/CLAUDE.md`, `painel/README.md`). O sincronizador nunca escreve em `videos/`, `00-marca/`, `_controle/`,
`scripts/` nem nos registros do Claude Code (`painel/sync/sincronizar.py`, docstring). O único passo que grava arquivo é
`painel/sync/previas_looks.py`, que gera as prévias dos looks em `painel/previas/looks/`. Na tela, os botões que antes
"criavam" coisas saíram (decisão de 24/10, `painel/design/design-system.md`): no lugar, o painel mostra o comando para
copiar e colar no Claude Code (`painel/web/src/components/Pedido.tsx`; tela Contratar).

## 2. Arquitetura

```
arquivos do projeto ─┐
(.claude/agents, videos/*, 05-render-pronto, 06-publicar, 07-publicados, _controle/*, painel/*.yaml, 00-marca/cor)
registros do Claude Code (~/.claude/projects/<projeto>/**/*.jsonl, só leitura)
                     │
                     ▼
  painel/sync/sincronizar.py  (Python 3.12, psycopg; launchd a cada 15 min)
                     │  uma transação: truncate + insert (espelho) · arquivo de execuções (nunca truncado)
                     ▼
  Postgres 17 do Supabase local do painel  (127.0.0.1:55322; API PostgREST/Kong em 127.0.0.1:55321)
                     │  supabase-js com a chave service_role, só no servidor (import "server-only")
                     ▼
  painel/web — Next.js 15 App Router, React Server Components (127.0.0.1:3456)
                     │  HTML pronto + componentes de cliente só para busca, filtros, abas, dicas e cópia
                     ▼
  navegador (só no próprio Mac)
```
Fontes: `painel/README.md` (diagrama), `painel/sync/sincronizar.py` (`DB_URL`, `gravar`), `painel/supabase/config.toml`
(portas, `major_version = 17`), `painel/web/src/lib/db.ts` (`createClient` + `server-only`), `painel/web/package.json`
(`-p 3456 -H 127.0.0.1`).

**O caminho de um dado — o veredicto de um portão até a tela:**
1. Um agente-portão audita um vídeo e o `scripts/portoes.py` grava o veredicto no `portoes.json` do alvo
   (ex.: `videos/<slug>/portoes.json`) (`docs/gauntlet.md`).
2. A cada 15 min o launchd `uk.korvu.painel` roda `uv run python painel/sync/sincronizar.py`
   (`scripts/launchd/uk.korvu.painel.plist`, `StartInterval 900`, `RunAtLoad`).
3. O sincronizador importa o próprio `portoes.py` com `portoes.SO_LEITURA = True` (nem o cache de hashes é gravado) e
   `sys.dont_write_bytecode = True`; `portoes_e_veredictos()` devolve as linhas (`painel/sync/sincronizar.py`).
4. Numa transação só, `truncate` das tabelas-espelho e `insert` em `portoes_estado` (alvo × portão: status, motivos,
   volta) e `veredictos` (chave `alvo, ordem`) (`gravar`; migrações `20261022190000`, `20261023203320`).
5. No Next.js, `db.portoesEstado()` e `db.veredictos()` leem pela API do Supabase, página a página de 1.000 linhas,
   conferindo a contagem exata (`todos()` em `painel/web/src/lib/db.ts`).
6. A tela Produção (bloco "Portões" e "Precisam de atenção"), a ficha do agente (`/equipe/[id]`: "O que passa por aqui",
   "Veredictos recentes") e o sino de avisos da barra do topo mostram o resultado (`painel/web/src/app/producao/page.tsx`,
   `app/equipe/[id]/page.tsx`, `lib/casca.ts`).
7. O rodapé de toda página diz a hora da última passagem (`sincronizacoes.em`, `app/layout.tsx`).

## 3. Tecnologia

| Camada | Tecnologia | Versão | Por que (só o que está escrito) | Fonte |
|---|---|---|---|---|
| Framework web | Next.js (App Router) | 15.5.28 | — | `painel/web/package.json`, `package-lock.json` |
| UI | React / React DOM | 19.1.10 | — | `painel/web/package.json` |
| Linguagem (web) | TypeScript (`strict`) | 5.9.3 | — | `package.json`, `tsconfig.json` |
| Estilo | Tailwind CSS (+ `@tailwindcss/postcss`) | 4.3.3 | — | `package.json` |
| CSS do design system | CSS próprio "korvu. painel" (tokens, componentes, acréscimos, movimento) | — | cópia sem mudar de `painel/design/` | `painel/README.md`, `web/src/app/design/` |
| Cliente do banco | `@supabase/supabase-js` | 2.58.0 | lê do lado do servidor com a chave de serviço | `package.json`, `lib/db.ts` |
| Trava de servidor | `server-only` | 0.0.1 | impede importar o acesso ao banco em componente de cliente | `package.json`, `lib/db.ts` |
| Lint | ESLint + `eslint-config-next` | 9.39.5 / 15.5.28 | — | `package.json` |
| Banco | Supabase local (CLI), Postgres | Postgres 17 | banco próprio, isolado do outro projeto do Mac (portas 553xx) | `painel/supabase/config.toml`, `painel/CLAUDE.md` |
| Sincronizador | Python | ≥ 3.12 | — | `pyproject.toml` (`requires-python`) |
| Driver Postgres | psycopg (binary) | ≥ 3.2 | — | `pyproject.toml` |
| YAML | PyYAML | ≥ 6.0.3 | ler `equipe.yaml`, `cambio.yaml`, `biblioteca.yaml` | `pyproject.toml` |
| Gerenciador Python | uv | — | "rodar sempre com `uv run`" | `CLAUDE.md` raiz |
| Agendador | launchd (macOS) | — | sincronização a cada 15 min | `scripts/launchd/uk.korvu.painel.plist` |
| Docker | Colima | — | o encaminhador dele define o endereço publicado; daí a rede só-no-Mac | `painel/README.md`, `painel/so-no-mac.sh` |
| Prévias dos looks | ffmpeg | — (`FFMPEG_BIN` ou PATH) | aplica as LUTs num quadro de amostra | `painel/sync/previas_looks.py`, `README.md` |
| Capturas de tela | Chrome sem janela via CDP + Node | Node ≥ 22 | olhar a tela de verdade a 1440 e 375 px | `painel/capturar.sh` |
| Fontes | Geist e Geist Mono (variáveis, OFL 1.1) | — | locais, nada do Google | `painel/design/design-system.md` §3, `app/layout.tsx` |

## 4. Banco

Supabase local próprio: `project_id = "korvu-studio-painel"`, API 55321, Postgres 55322, shadow 55320, Studio 55323
(desligado, `[studio] enabled = false`), `max_rows = 1000`, Realtime desligado (`painel/supabase/config.toml`).
**32 tabelas e 10 views**, criadas por 18 migrações em `painel/supabase/migrations/` (o teste `test_sincronizar.py`
confere "as migrações criam as 32 tabelas").

### 4.1 Tabelas (colunas principais)

**Equipe e GAUNTLET**
| Tabela | Chave | Colunas principais | Relação |
|---|---|---|---|
| `departamentos` | `id` | nome, ordem, descricao, gerente_id | `gerente_id` → `agentes.id` (FK deferrable) |
| `agentes` | `id` (nome do arquivo em `.claude/agents/`; `diretor` = sessão principal) | nome, cargo, departamento_id, papel (`diretor·portao·construtor·analista`), resumo, personalidade, descricao, modelo, ferramentas[], skills[], comandos[], fiscalizado_por, fiscaliza[], retrato, arquivo | `departamento_id` → departamentos; `fiscalizado_por` → agentes (FK deferrable) |
| `portoes_estado` | (`alvo`, `portao`) | slug, agente, status (`aprovado·vencido·bloqueado·escalado·pendente·nao_se_aplica`), motivos jsonb, volta | lógica: alvo = `videos/<slug>`, `06-publicar/<slug>` ou `painel` |
| `veredictos` | (`alvo`, `ordem`) | slug, portao, agente, resultado, impressao, em, volta, s0, s1, s2, relatorio, nota, decisao_autor | `ordem` = posição no `portoes.json` |

**Vídeos, fila e publicação**
| Tabela | Chave | Colunas principais | Relação |
|---|---|---|---|
| `videos` | `slug` | tema, pilar, estrutura, cta, estado, atualizado, historico jsonb; gravado, gravacao_arquivos/bytes (+ `_no_mac`, `gravacao_arquivados`, `gravacao_arquivados_bytes`), gravacao_ultima, gravacao_chegou, gravacao_data_suspeita; pronto; tem_roteiro, roteiro_versao, cta_palavra, roteiro_extras, gravacao_prevista, nome_curto | base de biblioteca_* e animacoes |
| `prontos` | `slug` | video_slug, qa, duracao, criado_em, cta_palavra | vídeo de origem |
| `fila` | `slug` | publicar_em, plataformas[], estado, trial, palavra, legado, confirmar, origem, selado, erros_gauntlet jsonb, video_slug | vídeo de origem |
| `publicacoes` | `slug` | publicado_em, tema, pilar, palavra, duracao_s, trial, permalink_instagram, permalink_facebook, video_slug, plataformas[], estado | ← metricas |
| `metricas` | (`slug`, `lido_em`) | dias, views, alcance, tempo_medio_s, pct_assistido, curtidas, comentarios, salvamentos, compartilhamentos, plays_fb, tempo_medio_fb_s, palavra_comentarios, palavra_directs, suspeito | `slug` → publicacoes (cascade) |
| `nao_publicar` | `slug` | video_slug, motivo, desde | espelho de `_controle/nao-publicar.json` (proposta) |
| `calendario_vagas` | (`dia_semana`, `hora`) | dia, fuso | bloco `vagas_semanais` do `_controle/calendario.md` |

**Perfil (Instagram/Facebook)**
| Tabela | Chave | Colunas principais | Relação |
|---|---|---|---|
| `perfil_snapshots` | `lido_em` | seguidores, seguindo, posts, janela_dias, alcance, views, contas_engajadas, interacoes, visitas_perfil, alcance_seguidores, alcance_nao_seguidores, fb_seguidores, toques_links_perfil | ← perfil_demografia |
| `perfil_demografia` | (`lido_em`, `publico`, `dimensao`, `chave`) | valor (público = seguidores·alcancados; dimensão = country·city·age·gender) | `lido_em` → perfil_snapshots (cascade) |
| `perfil_diario` | (`dia`, `metrica`) | valor, lido_em | proposta: o `perfil.py` ainda não grava |

**Tokens e custos do Claude Code**
| Tabela | Chave | Colunas principais | Relação |
|---|---|---|---|
| `precos_modelo` | `modelo` | nome, entrada, cache_gravado_5m, cache_gravado_1h, cache_lido, saida (US$ por milhão) | usado pelas views de custo |
| `execucoes` | `arquivo` (o `.jsonl`) | tipo (principal·subagente), sessao, agente_id, workflow, agente_tipo, membro_id, departamento_id, descricao (≤ 200), profundidade, terminou, video_slug, inicio, fim, registro_presente, visto_em | ← uso_execucao |
| `uso_execucao` | (`arquivo`, `dia`, `modelo`) | respostas, entrada, cache_gravado_5m, cache_gravado_1h, cache_gravado_sem_ttl, cache_lido, saida, tokens (gerada) | `arquivo` → execucoes (cascade) |
| `cambio` | (`moeda`, `data`) | valor, fonte | espelho de `painel/cambio.yaml` (opcional) |

**Biblioteca (índice de material, 23/10, e acervo de estilos, 24/10)**
| Tabela | Chave | Colunas principais | Relação |
|---|---|---|---|
| `biblioteca_materiais` | `id` | video_slug, grupo (pdf·dossie·pasta·extras·soltos), nome, caminho, quem_adicionou_inferido, miniatura, obra_estudo | `video_slug` → videos |
| `biblioteca_arquivos` | `caminho` | material_id, video_slug, area, extensao, tipo, bytes, modificado_em, data_suspeita, obra_estudo | → biblioteca_materiais, videos |
| `biblioteca_referencias` | `pasta` | arquivos, bytes | — |
| `biblioteca_mais_utilizados` | `arquivo` | nome, usos, unidade, regra, arquivo_existe | — |
| `looks` | `id` (vlog·rec709·vN) | ordem, tipo, nome, descricao, papel (em_uso·alternativa·arquivado), chaves/linhas do cor.md, aprovada, criado_em, ficha jsonb, cube + cube_sha256, rosto_ire (+ data, amostra), previa, previa_esperada | índice único: um só `em_uso` |
| `capa_estilos` | `id` | ordem, nome, descricao, ficha, ficha_existe, em_uso | ← capa_estilos_exemplos |
| `capa_estilos_exemplos` | (`estilo_id`, `ordem`) | slug, pasta, caminho, video_slug | → capa_estilos |
| `legenda_estilos` | `id` | ordem, nome, descricao, ficha, ficha_existe, em_uso | — |
| `fontes` | `familia` | ordem, remotion, estilo, pesos[], uso, reserva, confere_brand_ts | — |
| `sistema_ferramentas` | `nome` | ordem, tipo, descricao, versao, versao_de | — |
| `modelos_descricao` | `modelo` | ordem, descricao, com_preco | — |
| `animacoes` | `id` (`<slug>/Exx`) | video_slug, codigo, titulo, linhas[], modo, duracao_s, video_do_brief, renderizada, mp4, brief | → videos |
| `sistema_contagens` | `unico` (uma linha) | agentes, habilidades, comandos | — |

**Operação:** `sincronizacoes` (`em`, `resumo` jsonb) — uma linha por passagem, guarda só 7 dias (`gravar`).

### 4.2 Views (todas `security_invoker = true`)
| View | O que é | Migração |
|---|---|---|
| `consumo` | execução × dia × modelo **com preço**, com membro, departamento, vídeo e `usd` calculado de `precos_modelo` | `20261023153330`, refeita em `20261023154146` |
| `consumo_diario` | dia × modelo × agente: somas e nº de execuções | idem |
| `execucoes_custo` | cada execução com totais, `tarefa`, `respostas_sem_preco` | idem |
| `biblioteca_materiais_resumo` | o cartão de cada material (arquivos, bytes, data, contagem por tipo) | `20261023203320` |
| `biblioteca_por_tipo` | os 6 tipos, também com zero | `20261023203320` |
| `biblioteca_por_video` | material + extras e a gravação no Mac / no HD | `20261023203320`, `20261024055255` |
| `videos_producao` | Roteiros: dados do roteiro + extras e PDF que a Biblioteca já conta | `20261024042911` |
| `modelo_por_agente` | o modelo que **rodou** por agente nos 30 dias UTC (todo agente aparece) | `20261024213122` |
| `armazenamento` | uma linha: bytes no Mac (gravações + material), no HD, última leitura | `20261024215907`, `20261025214021`, `20261025222838` |
| `sistema_modelos` | por modelo, 30 dias: tokens, %, US$, execuções, agentes, frase | `20261024215907` |

O custo **não é guardado** nas linhas: as views calculam a partir de `precos_modelo` (`painel/README.md`, migração
`20261023153330`).

### 4.3 Papéis, RLS e privilégios
- **RLS ligado em todas as tabelas, sem nenhuma política** (`alter table … enable row level security` em cada migração).
  Só passa quem ignora RLS: `postgres` (o sincronizador, dono das tabelas) e `service_role` (o app).
- `anon` e `authenticated`: **nenhum privilégio** em tabela, sequência ou função; `service_role`: **só SELECT**.
  Vale também para o que for criado depois, pelos *default privileges* do papel `postgres`, e o `EXECUTE` padrão de
  `PUBLIC` em funções novas foi revogado (`20261022225715_revogar_privilegios_da_api.sql`). Cada migração seguinte repete
  o `revoke all … grant select … to service_role` das suas tabelas/views.
- Fora do alcance (escrito na própria migração): os default privileges do papel `supabase_admin`.
- Não há login no app (comentário da migração `20261022225715`: "não há login; o app não usa a chave anon").

### 4.4 Linha do tempo das migrações
| Data (do nome) | Migração | O que mudou |
|---|---|---|
| 22/10 19:00 | `20261022190000_inicial` | 11 tabelas-espelho (equipe, vídeos, portões, veredictos, fila, publicações, métricas, perfil, sincronizações) com RLS |
| 22/10 20:00 | `20261022200000_leitura_do_app` | SELECT para `service_role` (o Supabase novo não dá mais por padrão) |
| 22/10 22:57 | `20261022225715_revogar_privilegios_da_api` | fecha `anon`/`authenticated`, `service_role` só SELECT, inclusive para objetos futuros |
| 23/10 15:33 | `20261023153330_tokens_e_custos_do_claude_code` | `precos_modelo`, `execucoes`, `uso_execucao` (arquivo, nunca truncado) e as views de consumo |
| 23/10 15:41 | `20261023154146_cache_gravado_por_ttl` | cache gravado dividido por TTL (5 min = 1,25×, 1 h = 2×); views refeitas |
| 23/10 15:41 | `20261023154151_cambio_do_custo_de_ia` | tabela `cambio` |
| 23/10 16:05 | `20261023160517_fila_origem_selo_e_conferencia` | fila: origem, selo e `erros_gauntlet` (a mesma conferência do `publicar.py`) |
| 23/10 16:09 | `20261023160956_fases_publicados_e_nao_publicar` | fases da Produção (`gravado`, `pronto`), `video_slug`, `nao_publicar` |
| 23/10 16:13 | `20261023161339_gravacao_chegada_e_data_suspeita` | data de chegada e data suspeita da gravação |
| 23/10 19:50 | `20261023195043_fk_gerente_e_fiscal_e_uso_pela_ultima_linha` | FKs deferrable de gerente e fiscal; regra do usage pela última linha |
| 23/10 20:33 | `20261023203320_biblioteca_e_ordem_dos_veredictos` | chave `(alvo, ordem)` nos veredictos; tabelas e views da Biblioteca (índice de material) |
| 24/10 04:29 | `20261024042911_producao_calendario_e_desempenho` | roteiro em `videos`, `prontos`, `calendario_vagas`, `perfil_diario`, view `videos_producao` |
| 24/10 05:52 | `20261024055255_gravacao_no_mac_e_no_hd` | gravação separada em "no Mac" e "no HD" |
| 24/10 21:31 | `20261024213122_modelo_por_agente` | view do modelo que rodou por agente |
| 24/10 21:59 | `20261024215907_biblioteca_acervo_de_estilos` | acervo de estilos (looks, capas, legendas, fontes, ferramentas, modelos, animações, contagens) + `armazenamento`, `sistema_modelos` |
| 24/10 23:36 | `20261024233631_rosto_do_look_pelo_biblioteca_yaml` | só comentários: o rosto em IRE passa a vir do `biblioteca.yaml` |
| 25/10 21:40 | `20261025214021_nome_e_frase_dos_looks_e_nota_do_hd` | frase de cada look; nota do HD |
| 25/10 22:28 | `20261025222838_hd_externo_fora_do_painel` | tira a nota do HD (decisão: o HD não aparece no painel) |

## 5. Back-end e sincronização

**O que o `sincronizar.py` lê** (`ler_projeto()` em `painel/sync/sincronizar.py`, `painel/README.md`):
| Origem | Vira |
|---|---|
| `.claude/agents/*.md` (frontmatter) + `painel/equipe.yaml` | `departamentos`, `agentes` (skills e comandos achados no texto) |
| `videos/*/portoes.json` e demais alvos, via `scripts/portoes.py` (só leitura) | `portoes_estado`, `veredictos` |
| `_controle/tracker.md`, `videos/<slug>/status.json`, `roteiro.json`, `brutos/principal/` (só listagem e `stat()`), `ARQUIVADO.json` | `videos` |
| `05-render-pronto/<slug>/pacote.json` | `prontos`, `videos.pronto` |
| `06-publicar/<slug>/` (pacote + post) + `portoes.conferir_pacote(...)` | `fila` |
| `07-publicados/<slug>/post.json` e `metricas.json` | `publicacoes`, `metricas` |
| `_controle/perfil/*.json` e `_controle/perfil/diario/*.json` (proposta) | `perfil_snapshots`, `perfil_demografia`, `perfil_diario` |
| `_controle/calendario.md` (1.º bloco ```yaml) | `calendario_vagas` |
| `_controle/nao-publicar.json` (proposta) | `nao_publicar` |
| `videos/*/material/**`, `videos/*/brutos/extras/**`, `00-marca/referencias`, `painel/referencias` | `biblioteca_*` |
| `00-marca/cor/luts/*`, `00-marca/cor/cor.md`, `painel/biblioteca.yaml`, `remotion/src/brand.ts` | `looks`, `capa_estilos(+_exemplos)`, `legenda_estilos`, `fontes`, `sistema_ferramentas`, `modelos_descricao` |
| `videos/*/animacoes/Exx/brief.md` | `animacoes` |
| `.claude/agents`, `.claude/skills`, `.claude/commands` | `sistema_contagens` |
| `painel/cambio.yaml` | `cambio` |
| `PRECOS` no próprio código | `precos_modelo` |
| registros do Claude Code `~/.claude/projects/<projeto>/**/*.jsonl` + `agent-<id>.meta.json` | `execucoes`, `uso_execucao` |

**Frequência:** launchd `uk.korvu.painel`, a cada 900 s e ao entrar na sessão do Mac; log em `_controle/logs/painel.log`,
uma linha por passagem (`scripts/launchd/uk.korvu.painel.plist`). Manual: `uv run python painel/sync/sincronizar.py`
(`--seco` lê sem gravar; `--ate` e `--regra-do-script` só para reconciliar, recusados no banco real sem `--seco`).

**Como evita escrever no projeto:** `portoes.SO_LEITURA = True`, `sys.dont_write_bytecode = True` antes do
`import portoes`, brutos e materiais só por listagem e `stat()` (nenhum vídeo é aberto), nada de texto de conversa do
Claude Code no banco (só números, ids, modelo, horário, slug e a descrição curta do `.meta.json`)
(`painel/sync/sincronizar.py`, migração `20261023153330`).

**Como grava:** uma transação só — `truncate` das 29 tabelas-espelho (`ORDEM`) e `insert`; as 2 tabelas de ARQUIVO
(`execucoes`, `uso_execucao`) nunca são truncadas: apaga e regrava só o que o `.jsonl` ainda mostra e marca o que sumiu
com `registro_presente = false` (o Claude Code apaga registros com mais de 30 dias) (`gravar()`).

**Como lida com erro:** arquivo ilegível → `✗ … nada gravado`, exit 1; banco fora do ar (`OperationalError`) →
`✗ banco do painel fora do ar — ligar com: bash painel/iniciar.sh`, exit 1; banco que recusa (FK, chave repetida) →
`✗` com o DETAIL do Postgres, transação desfeita; anomalia que não para → linha `⚠` (`main()`). Em todos os casos o painel
continua com a passagem anterior.

**Como roda tudo:** `bash painel/iniciar.sh` → `garantir_rede` (rede Docker publicando só em 127.0.0.1) → `supabase start`
→ `conferir_portas` (recusa se alguma 553xx escutar fora de 127.0.0.1) → uma passagem do sincronizador → `npm run dev`
em `painel/web` (`painel/iniciar.sh`, `painel/so-no-mac.sh`). Studio: `bash painel/studio.sh liga|desliga`.

**Prévias dos looks:** `uv run python painel/sync/previas_looks.py` gera um JPEG 640×800 por look a partir de um quadro de
amostra + a LUT de entrada + a LUT do look, com nome por hash; só refaz o que mudou (`painel/README.md`).

**No app (back-end do Next.js):** todas as páginas são Server Components com `dynamic = "force-dynamic"`
(`app/layout.tsx`); a leitura usa `todos()` — pagina por 1.000 linhas, confere `count: "exact"`, relê uma vez se a
tabela mudar no meio (sincronização rodando) e **lança erro** se vier menos linha do que o banco diz ter
(`lib/db.ts`). `cache()` do React faz cada leitura ir ao banco uma vez por pedido (`lib/leituras.ts`, `lib/acervo.ts`).
Duas rotas de arquivo, só leitura: `GET /capa/[pasta]/[slug]` (o `capa/capa.png` do pipeline, pasta numa lista fixa e
slug validado por regex) e `GET /look/[id]` (a prévia do look, caminho vindo do banco e preso a `painel/previas/looks/`)
(`app/capa/[pasta]/[slug]/route.ts`, `app/look/[id]/route.ts`, `lib/capas.ts`). Redirect 307 `/videos → /producao`
(`next.config.ts`).

## 6. APIs

| API | Quem chama | O que traz | Onde fica guardado | Fonte |
|---|---|---|---|---|
| **Supabase / PostgREST** (HTTP, 127.0.0.1:55321) | o app Next.js, só no servidor, com `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` | as 32 tabelas e 10 views, só SELECT | — (lê o banco) | `web/src/lib/db.ts` |
| **Postgres direto** (127.0.0.1:55322, psycopg) | o sincronizador (`PAINEL_DB_URL`, padrão o banco local) | — (escreve) | banco do painel | `sync/sincronizar.py` |
| **Meta Graph API** (`graph.facebook.com`, versão `META_GRAPH_VERSION`, padrão `v23.0`) — **indireta** | `scripts/metricas.py` (métricas de cada Reel aos 5 dias), `scripts/perfil.py` (conta: insights `period=day, metric_type=total_value`, quebras por país/cidade/idade), `scripts/publicar.py` (publica) — área Automação Meta, não o painel | métricas de Reels, perfil e demografia, permalinks | `07-publicados/<slug>/metricas.json` e `post.json`, `_controle/perfil/*.json` → o painel só lê esses arquivos | `scripts/publicar.py` (`GRAPH_VERSION`), `scripts/perfil.py`, `scripts/metricas.py`, `automacao-meta/CLAUDE.md` |
| **Registros do Claude Code** (arquivos locais `.jsonl`, não é API de rede) | o sincronizador | `message.usage`, `message.model`, `message.id`, `timestamp`; tipo do subagente no `.meta.json` | `execucoes`, `uso_execucao`; custo pelas views | `sync/sincronizar.py`, `README.md` "Tokens e custos" |
| **Preço de tabela da API da Anthropic** (não é chamada; tabela copiada no código) | — | US$/M: Opus 5.5 4/20, Sonnet 5.5 2/10, Fable 5.1 10/50, Opus 5 5/25; cache 5 min 1,25×, 1 h 2× | `PRECOS` → `precos_modelo` | `sync/sincronizar.py` |
| **`scripts/portoes.py`** (API Python interna) | o sincronizador, importado em modo só leitura | estado dos portões, veredictos, `conferir_pacote` da fila | `portoes_estado`, `veredictos`, `fila.erros_gauntlet` | `sync/sincronizar.py` |
| **Rotas do próprio app** | o navegador | `GET /capa/[pasta]/[slug]` (PNG), `GET /look/[id]` (JPEG) | — | `app/capa/…/route.ts`, `app/look/[id]/route.ts` |
| **Otimizador de imagens do Next** | `<Image>` das capas | versão reduzida da capa | cache em `.next*/cache/images` | `lib/capas.ts` (comentário) |

**Não usados pelo painel:** a chave `anon`, Supabase Auth, Storage e Realtime (Realtime desligado no `config.toml`; Auth e
Storage ligados por padrão no `config.toml`, mas nenhum código do app chama). **ElevenLabs** aparece só na lista da stack
da Biblioteca: o consumo dela não é medido ("ElevenLabs fora", `painel/README.md`).

## 7. Tela por tela

Casca comum (`components/Casca.tsx`, `app/layout.tsx`): barra lateral escura com o menu (Visão geral · Equipe · Produção
de conteúdo · Calendário · Desempenho · Biblioteca · Tokens e custos — `lib/navegacao.ts`), contagem da equipe, busca
global ⌘K (vídeos, agentes, portões — `components/Busca.tsx`), sino de avisos (portões que pedem ação —
`components/Avisos.tsx`, `lib/casca.ts`), "o autor · Proprietário", rodapé com a hora da última sincronização. Estados
globais: **carregando** = esqueleto dentro da casca (`app/loading.tsx`); **erro** = "Não deu para ler os dados" com os
passos para ligar o banco e sincronizar (`app/error.tsx`); **banco fora/nunca sincronizado** = nota de alerta no topo
(`AvisoDoBanco` em `layout.tsx`); **não encontrado** = `app/not-found.tsx`. Cada bloco de cada tela tem o próprio
`Suspense` com esqueleto, erro de bloco e vazio com frase. **Celular (375 px):** a barra lateral vira o botão "Menu" no
topo e os blocos empilham (visto em `capturas/inicio-375.png`; `design-system.md` §4.1). Das fotos a 375 px, só a da
Visão geral foi olhada uma a uma; as outras foram medidas pelo `capturar.sh` (sem rolagem lateral).

### 7.1 Visão geral — `/`
- **Pergunta:** como está o estúdio hoje: o perfil, o que sai nos próximos dias, os últimos 28 dias, quanto a IA consumiu
  e quem está na equipe (`design/telas/visao-geral.md`).
- **Blocos:** 4 números do perfil (seguidores, alcance 28 dias, alcance fora da bolha, melhor vídeo) · Próximas
  publicações · Desempenho 28 dias · Público top 10 países (quem segue × quem os vídeos alcançam) · Tokens e custos 30
  dias (rosca por modelo + custo estimado) · Equipe (filtro por departamento, 5 cartões com foto).
- **Dados:** `perfil_snapshots`, `perfil_demografia`, `metricas` + `publicacoes`, `fila`, `consumo_diario`,
  `execucoes_custo`, `agentes`, `departamentos`, `modelo_por_agente` (`app/page.tsx`, `app/_componentes/*`).
- **Vazio:** "Nada agendado" na fila (visto na captura).
- **Capturas:** `capturas/inicio-1440.png`, `capturas/inicio-375.png`.

### 7.2 Equipe — `/equipe`
- **Pergunta:** quem é quem por departamento, quem é portão, com que modelo cada um trabalha e quanto consumiu nos 30
  dias (`design/telas/equipe.md`).
- **Blocos:** busca de agente · filtros (Todos · Portões · Opus 5.5 · Sonnet 5.5 · Ainda não rodou) · 4 números (agentes,
  departamentos, portões, tokens 30 dias) · Direção (o Atlas) · um cartão por departamento com gerente primeiro (modelo
  que rodou, consumo, tarefas).
- **Dados:** `agentes`, `departamentos`, `consumo_diario`, `execucoes_custo`, `modelo_por_agente`; fotos de
  `web/public/equipe/<id>.jpg` (sem foto = iniciais) (`app/equipe/page.tsx`, `lib/consumo.ts`, `lib/retratos.ts`).
- **Vazio:** "Equipe ainda não sincronizada"; sem consumo, o número mostra "—".
- **Capturas:** `capturas/equipe-1440.png`, `capturas/equipe-375.png`.

### 7.3 Ficha do agente — `/equipe/[id]`
- **Pergunta:** o que essa pessoa da equipe faz e, se for portão, o que passou por ela (`app/equipe/[id]/page.tsx`).
- **Blocos:** cabeçalho com foto, departamento e cargo · A função (papel, o que faz, modelo, skills, comandos,
  ferramentas, quem fiscaliza, arquivo) · O que passa por aqui (estado do portão em cada alvo) · Veredictos recentes (os
  12 mais novos).
- **Dados:** `agentes`, `departamentos`, `portoes_estado`, `veredictos`, `videos`.
- **Vazio/erro:** "Nenhum alvo com este portão ainda", "Nenhum veredicto ainda"; id inexistente = 404; erro de banco
  nunca vira 404.
- **Capturas:** `capturas/equipe-portao-imagem-1440.png`, `capturas/equipe-portao-imagem-375.png`.

### 7.4 Contratar — `/equipe/contratar`
- **Pergunta:** como pedir um agente novo já ligado ao portão do departamento (texto da própria tela).
- **Blocos:** formulário (nome, cargo, departamento, o que faz, o que entrega, quando é chamado, modelo) · "Pedido de
  contratação" montado ao vivo · botão "Copiar pedido". O painel não cria arquivo: o pedido é colado numa conversa com o
  Claude Code.
- **Dados:** `departamentos`, `agentes` (`app/equipe/contratar/page.tsx`, `Formulario.tsx`, `components/Pedido.tsx`).
- **Capturas:** `capturas/equipe-contratar-1440.png`, `capturas/equipe-contratar-375.png`.

### 7.5 Produção de conteúdo — `/producao` (`/videos` redireciona)
- **Pergunta:** em que fase está cada conteúdo — roteiro, gravado, pronto, agendado ou publicado — e o que precisa de
  atenção (`design/telas/producao.md`).
- **Blocos:** busca · filtro de formato (Todos · Reels · Stories · Carrossel) e a fonte lida · 5 fases com os elos ("você
  grava", "pós e QA", "você agenda", "publica no horário") · tabela da fase escolhida · Precisam de atenção · Portões
  (resumo por área).
- **Dados:** `videos`, `videos_producao`, `prontos`, `fila`, `publicacoes`, `nao_publicar`, `portoes_estado`,
  `agentes` (`app/producao/page.tsx`, `lib/producao.ts`). Fase: Roteiros = sem gravação; Gravados = gravado sem pronto;
  Prontos = QA PASS; Agendados = `fila`; Publicados = `publicacoes` (`painel/README.md`).
- **Vazio:** "Nada em produção"; Stories e Carrossel mostram "Nenhum story/carrossel ainda"; "Nada pede atenção agora";
  "Nenhum portão no banco".
- **Capturas:** `capturas/producao-1440.png`, `capturas/producao-375.png`.

### 7.6 Calendário — `/calendario`
- **Pergunta:** o que sai em cada dia, onde, as vagas livres e se cada post da fila vai mesmo sair
  (`design/telas/calendario.md`).
- **Blocos:** navegação (Hoje, ‹ ›), legenda, Mês | Semana (`?vista=semana&dia=AAAA-MM-DD`) · eventos publicados e
  agendados com capa e canais · vagas livres · Fila (com a linha "Portões:") · Melhores horários (vazio: ainda sem dado).
- **Dados:** `publicacoes`, `fila`, `calendario_vagas`, capas pela rota `/capa`; hora do fuso de publicação (`app/calendario/page.tsx`).
- **Vazio:** "Nada programado neste mês", "Fila vazia", "Sem print de horários". Sem vagas, o calendário continua.
- **Capturas:** `capturas/calendario-1440.png`, `capturas/calendario-375.png`.

### 7.7 Desempenho — `/desempenho`
- **Pergunta:** o que cresce, quem os vídeos estão alcançando e qual conteúdo funciona (`design/telas/desempenho.md`).
- **Blocos:** período · 4 números (seguidores, visualizações, contas alcançadas, visitas ao perfil, com delta) ·
  crescimento (curva por dia; hoje vazio: a Meta só manda o total de 28 dias) · fora da bolha (rosca não seguidores ×
  seguidores) · de onde vem o público (quem segue × quem os vídeos alcançam) · conteúdo que funciona (ranking dos Reels:
  views, alcance, % assistido, engajamento).
- **Dados:** `perfil_snapshots`, `perfil_demografia`, `perfil_diario`, `metricas`, `publicacoes`. Leitura `suspeito`
  nunca entra em gráfico, ranking nem conta (`app/desempenho/page.tsx`, `lib/db.ts → leiturasConfiaveis`).
- **Vazio:** "Ainda não há dia a dia".
- **Capturas:** `capturas/desempenho-1440.png`, `capturas/desempenho-375.png`.

### 7.8 Biblioteca — `/biblioteca`
- **Pergunta:** escolher o estilo do próximo vídeo — look de cor, capa, legenda, fonte, animação — vendo cada um aplicado,
  e saber quanto espaço o estúdio ocupa e o que o faz rodar (`design/telas/biblioteca.md`).
- **Blocos:** abas (Tudo · Looks de cor · Capas · Legendas · Fontes · Animações · Sistema) · looks de cor (5 cartões com
  a prévia) · capas · legendas · fontes · animações (roteirizada × renderizada) · Armazenamento (GB no Mac) · Sistema
  (modelos de IA dos 30 dias, ferramentas, contagem de agentes/habilidades/comandos).
- **Dados:** `looks` (+ rota `/look/[id]`), `capa_estilos`, `capa_estilos_exemplos` (+ rota `/capa`), `legenda_estilos`,
  `fontes`, `animacoes`, `armazenamento`, `sistema_modelos`, `sistema_ferramentas`, `sistema_contagens`
  (`app/biblioteca/page.tsx`, `lib/acervo.ts`).
- **Capturas:** `capturas/biblioteca-1440.png`, `capturas/biblioteca-375.png`.

### 7.9 Tokens e custos — `/tokens`
- **Pergunta:** quanto a operação de IA consome, onde, quem e quanto custa em dólar, pelo preço de tabela da API
  (`design/telas/tokens-e-custos.md`).
- **Blocos:** período · 4 números (tokens, custo estimado, agentes, custo médio por agente) · consumo por dia (Tokens |
  Custo) · por modelo · por departamento · custo por vídeo · projeção mensal (média dos 30 dias × 30) · quem mais consome
  (Gerentes | Ranking geral).
- **Dados:** `consumo_diario`, `consumo`, `execucoes_custo`, `precos_modelo` (`app/tokens/page.tsx`). Custo = equivalente
  na API, não a fatura da assinatura (`painel/README.md`).
- **Capturas:** `capturas/tokens-1440.png`, `capturas/tokens-375.png`.

### 7.10 Rotas que não são telas
- `/sistema` — vitrine dos componentes para quem constrói e para o portão; **404 sem `PAINEL_VITRINE=1`**
  (`app/sistema/page.tsx`). Não fotografada (dá a página "não encontrada").
- `GET /capa/[pasta]/[slug]`, `GET /look/[id]` — imagens (seção 5).

## 8. Design system "korvu. painel"

Fonte: `painel/design/design-system.md` (922 linhas), `tokens.json`, `tokens.css`, `componentes.css`, `acrescimos.css`,
`movimento.css`, `handoff.md`; prévias de cada componente em `painel/design/previas/` (28 arquivos). Copiado sem
mudar para `painel/web/src/app/design/`.
- **Origem:** desenhado pelo dono no Claude Design em 23/10/2026 e importado em PT-BR com os valores exatos; conferência
  de fidelidade em `painel/design/verificacao/fidelidade.py`, contraste em `contraste.py`/`contraste.md`.
- **Fontes:** Geist (texto) e Geist Mono (modelos, IDs, HEX, tokens), arquivos variáveis locais, licença OFL 1.1.
  Escala: display 56/60 · h1 44/48 · h2 30/36 · h3 22/28 · body 15/22 · small 13/18 · caption 11/14 · metric-xl 40/44 ·
  metric-l 24/28 · mono 12/16. Números tabulares em tudo (§3).
- **Cores-token** (`tokens.css`): fundo marfim `--bg #f5f2e8`, superfície `#fbf9f4`, tinta `#111111`, tinta 2 `#6b6458`,
  barra lateral `#111111`, **acento `#ff4d00`** (hover `#e64500`, suave `#ffe8dc`, tinta `#b33600`), positivo `#1e7a45`,
  perigo `#c2271b`, gráficos `--chart-1…5` (acento, preto, `#a39b8b`, `#d6ccb5`, `#4f6475`).
- **Componentes** (`painel/web/src/components/`, 48 arquivos): Acervo, Alternador, Anel, Avatar, Avisos, BarraApp, Botao,
  Busca, Calendario, Campo, Canais, Capa, Card, CardPessoa, CartaoAgente, CartaoPublicacao, Casca, Chip, Contador,
  Destaque, Dica, Dicas, Equipe, ErroBloco, Escolha, Esqueleto, EstadoPagina, Evento, FiltroLista, GraficoLinha,
  Graficos (Barras, Legenda, Rosca, Sparkline), Icone, Kpi, LinhaPortoes, ListaKv, Logo, NavCalendario, Nota, Numeros,
  Pagina, Pedido, Portao, Progresso, Revelar, Selecao, Tabela, Texto, Vazio.
- **Gráficos:** seguem a skill `dataviz` — um eixo, tabela gêmea em todo gráfico, hover e foco (`design/telas/desempenho.md`).
- **Movimento:** v0 = 150 ms padrão, 120 ms na linha, 300 ms até a dica; v1 (03/11) toque, popovers e gaveta; v2
  (04/11) os dados entram com animação; tudo respeita `prefers-reduced-motion` (`design-system.md` §7, `movimento.css`).

## 9. Segurança e privacidade

- **Só no Mac:** app em `127.0.0.1:3456` (`-H 127.0.0.1` nos scripts `dev`/`start`); banco e API só em `127.0.0.1`
  (55321/55322) por uma rede Docker com `host_binding_ipv4=127.0.0.1`; `iniciar.sh`/`studio.sh` param com erro se uma porta
  ficar aberta para a rede; `/pg/*` responde 503 com o Studio desligado (`painel/README.md`, `so-no-mac.sh`).
- **Chaves só no servidor:** `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` em `painel/web/.env.local` (fora do git:
  `.env*` no `web/.gitignore`); `lib/db.ts` tem `import "server-only"`, e os comandos que as telas de erro mostram ficam em
  `lib/comandos.ts` para que componentes de cliente nunca importem o `db.ts`.
- **Banco fechado:** RLS em tudo, `anon`/`authenticated` sem nada, `service_role` só leitura (seção 4.3).
- **Rotas de arquivo endurecidas:** pasta numa lista fixa (`Object.hasOwn`), slug por regex, caminho da prévia vindo do
  banco e preso à pasta (PI58 nos comentários das rotas).
- **Sem texto de conversa** do Claude Code no banco.
- **Antes de expor na internet** (escrito em `painel/README.md`): trocar as chaves de demonstração do Supabase, criar um
  projeto Supabase na nuvem e `supabase db push`, trocar o `web/.env.local`, pôr login antes de abrir. O firewall do
  macOS está desligado (decisão "vejo depois"). Quem constrói ainda trabalha na mesma pasta do preview do dono (backlog D4,
  `docs/gauntlet.md`).

## 10. Qualidade

**GAUNTLET da área** (`docs/gauntlet.md`, `painel/CLAUDE.md`): quem faz não aprova. Dois portões, três áreas:
| Área | Portão | Fiscaliza | Confere |
|---|---|---|---|
| design | `portao-interface` | designer-de-produto | fidelidade ao design aprovado, telas olhadas a 1440 e 375 px |
| interface | `portao-interface` | engenheiro-frontend | código × design, dados honestos, gráficos, acessibilidade, chave nenhuma no navegador, tipos/lint/build |
| dados | `portao-dados` | engenheiro-backend | migrações versionadas, RLS e permissões, sincronizador que só lê, contagens, segredos, isolamento, testes |

A aprovação é por arquivo: mudou depois do APROVADO, vence. Estado em 12/11 (`uv run python scripts/portoes.py estado painel`):
design **aprovado** (04/11), interface **aprovado** (04/11), dados **vencido** (último APROVADO 25/10; mudou `equipe.yaml`).

**Testes** (`painel/tests/`, scripts Python, não pytest):
| Arquivo | Linhas | O que cobre | Resultado em 12/11 |
|---|---|---|---|
| `test_sincronizar.py` | 3.167 (≈ 327 checagens `ok`/`igual`) | raiz temporária + banco descartável `painel_teste_<pid>`: cada mapeamento arquivo → linha, `--seco`, porta morta, contrato com os produtores, permissões "do zero", reconciliação de tokens | **não rodado** (aplica as migrações num banco de teste; fora do limite deste levantamento) |
| `test_previas_looks.py` | 318 | o gerador de prévias numa raiz temporária, com amostra e `.cube` sintéticos | **44/44 PASS** |
| `test_biblioteca_yaml.py` | 149 | o `biblioteca.yaml` real contra a maquete, o `brand.ts` e o sincronizador (só leitura) | **19/22 PASS · 3 FAIL** |

As 3 falhas do `test_biblioteca_yaml.py`: a fonte "Inter Tight" do `biblioteca.yaml` não bate com o
`remotion/src/brand.ts` (`confere_brand_ts = false`); 4 briefs de animação de um vídeo (E24, E26, E27, E28) sem duração
no cabeçalho; e, por causa dessas duas, "nenhum aviso ⚠" falha.

`uv run pytest painel/tests -q` (pedido) **não roda**: `error: Failed to spawn: pytest` — o pytest não está nas dependências
do `pyproject.toml`; os testes são executados como `uv run python painel/tests/<arquivo>.py` (`painel/README.md`).

Outras conferências: `bash painel/capturar.sh` mede `innerWidth`/`scrollWidth` e falha se houver rolagem lateral (0
casos nas 18 fotos deste dossiê); `painel/design/verificacao/fidelidade.py` e `contraste.py`.

## 11. Como instalar e rodar do zero

Pré-requisitos (do que os scripts chamam): macOS (launchd), Docker (aqui o Colima), Supabase CLI, Node ≥ 22 e npm,
Python ≥ 3.12 com `uv`, Google Chrome (só para as capturas), ffmpeg (só para as prévias dos looks).

```bash
# 1. dependências
uv sync                                   # Python (pyproject.toml da raiz)
cd painel/web && npm ci && cd ../..       # Next.js (package-lock.json)

# 2. banco + primeira sincronização + app (http://localhost:3456)
bash painel/iniciar.sh

# 3. chaves do app: criar painel/web/.env.local com
#    SUPABASE_URL=<API URL local>  e  SUPABASE_SERVICE_ROLE_KEY=<service_role do supabase status>

# 4. sincronização automática a cada 15 min
bash scripts/launchd/instalar.sh uk.korvu.painel
launchctl kickstart -k gui/$(id -u)/uk.korvu.painel   # forçar agora

# testes
uv run python painel/tests/test_sincronizar.py
uv run python painel/tests/test_previas_looks.py
uv run python painel/tests/test_biblioteca_yaml.py
```
Fontes: `painel/iniciar.sh`, `painel/README.md` ("Rodar", "Sincronização automática"), `scripts/launchd/uk.korvu.painel.plist`.

**O que depende do Korvu Studio e alguém de fora teria de trocar para reusar:**
- **Toda a leitura do sincronizador** é presa à estrutura de pastas do estúdio (`videos/<slug>/…`, `05-render-pronto`,
  `06-publicar`, `07-publicados`, `_controle/…`, `00-marca/cor`, `remotion/src/brand.ts`) e aos contratos de
  `docs/contratos.md`. Para outro projeto: reescrever as funções de leitura de `sincronizar.py`.
- **`scripts/portoes.py`** é importado do projeto (o GAUNTLET). Sem ele, o sincronizador não abre.
- **Pessoas e nomes:** `painel/equipe.yaml`, `painel/biblioteca.yaml`, `painel/cambio.yaml`, os retratos em
  `web/public/equipe/` e os textos fixos ("o autor · Proprietário", `@korvu_oficial`).
- **Registros do Claude Code:** pasta derivada da raiz do projeto (`PAINEL_REGISTROS` troca); preços em `PRECOS`.
- **Ambiente:** raiz por `PAINEL_PROJETO`/`CONTENT_AI_ROOT`, banco por `PAINEL_DB_URL`, fuso de publicação no calendário,
  `so-no-mac.sh` pensado para o Colima, launchd (só macOS).
- **Reusável quase sem mudança:** o padrão "arquivos → sincronizador em transação → Postgres com RLS fechado →
  Server Components com paginação conferida", o design system, os componentes e o `capturar.sh`.

## 12. Não confirmado e divergências

**Não confirmado**
1. Versão do **Supabase CLI**: não está em arquivo de versão do projeto. No ambiente, `supabase --version` respondeu
   2.109.1 (e `painel/supabase/.temp/cli-latest` diz v2.122.0, a última disponível) — leitura do ambiente, não do código.
2. Que o primeiro `supabase start` aplica as 18 migrações sozinho (`[db.migrations] enabled = true` sugere que sim; não
   rodei, por limite).
3. Como o `web/.env.local` é preenchido pela primeira vez: nenhum script do painel o cria; o passo 3 da instalação é
   dedução a partir de `lib/db.ts` e do `README.md`. O arquivo não foi lido.
4. ~~Origem das fotos da equipe~~ — resolvido em 13/11: as 26 fotos de `web/public/equipe/` são imagens geradas por IA
   (não são pessoas reais), de uso livre no projeto por decisão do autor.
5. Resultado do `test_sincronizar.py` (não rodado).
6. Versões de uv, ffmpeg, Colima e Chrome: não há arquivo que as fixe.

**Divergências (o código vence)**
1. **Comando para ligar o banco:** `web/src/lib/comandos.ts` manda `cd painel && supabase start` na tela de erro e no
   aviso do topo; o `README.md` e o próprio sincronizador dizem para usar só `bash painel/iniciar.sh` ("nunca um
   `supabase start` solto", PD12), porque o comando solto pode recriar a rede Docker aberta para a rede local.
2. **Telas "em breve":** a seção "Páginas" do `painel/README.md` e o comentário de `web/src/lib/navegacao.ts` dizem que
   Calendário, Biblioteca e Tokens e custos mostram "Esta tela chega em breve"; o código e as capturas mostram as três
   telas completas.
3. **Seed:** `config.toml` aponta `sql_paths = ["./seed.sql"]`, mas não existe `painel/supabase/seed.sql`.
4. **Auth e Storage** ligados no `config.toml` (`[auth] enabled = true`, `enable_signup = true`, `[storage] enabled =
   true`), embora o painel não use login nem arquivos no Supabase.
5. **GAUNTLET × `equipe.yaml`:** `docs/gauntlet.md` diz que `painel/equipe.yaml` fica fora das áreas de propósito, mas o
   `portoes.py estado painel` marca a área **dados** como vencida porque o `equipe.yaml` mudou.
6. **Comentário antigo na migração `20261023153330`** ("ficando com a primeira ocorrência"): a regra vigente é a última
   linha (`20261023195043`); a própria migração nova registra isso.
7. **Tela Equipe:** a spec (`design/telas/equipe.md`) lista o filtro "Ativos" e a coluna Status; o código os deixa de
   fora até existir dado de presença (comentário em `app/equipe/page.tsx`).
8. **Biblioteca, aba Animações:** a spec fala em 3; o app mostra 7 (é dado vivo, não erro de código).
9. O pedido de rodar `uv run pytest painel/tests -q` não corresponde ao jeito de rodar os testes do projeto (seção 10).

## Revisar antes de publicar

Os PNG mostram dados reais da operação. Nada foi editado nas imagens.
- **Rosto do dono** (pessoa real) em todos os cartões de looks: `capturas/biblioteca-1440.png`, `biblioteca-375.png`;
  e nas capas de vídeo em miniatura: `inicio-*.png`, `calendario-*.png`, `desempenho-*.png`, `tokens-*.png`,
  `biblioteca-*.png`.
- **Fotos realistas da equipe** (origem a confirmar, ver "Não confirmado" 4): `inicio-*.png`, `equipe-*.png`,
  `equipe-portao-imagem-*.png`, `tokens-*.png`.
- **Métricas reais da conta** (seguidores, alcance, visualizações, ranking dos Reels) e **público por país** (de onde vêm
  os seguidores): `inicio-*.png`, `desempenho-*.png`. Decidir se vão a público.
- **Custos reais de IA** (US$ por agente, departamento e vídeo): `inicio-*.png`, `equipe-*.png`, `tokens-*.png`.
- **Títulos e slugs de vídeos ainda não publicados** (roteiros com palavra-chave do CTA): `producao-*.png`,
  `equipe-portao-imagem-*.png`, `calendario-*.png`.
- **Nome do dono** ("o autor · Proprietário") e o perfil `@korvu_oficial` aparecem em toda captura (é a marca pública; só
  confirmar).
- Nenhum e-mail, telefone, chave ou caminho de usuário apareceu nas capturas olhadas.

# Dossiê técnico — Volume 1 · Estúdio (produção, integrações e automação local)

> Levantado pelo `documentador-tecnico` em 12/11/2026, lendo o código. Cada afirmação cita o arquivo de onde saiu
> (caminhos relativos à raiz do projeto). O que não deu para confirmar está na seção 12. Material bruto para o
> `designer-de-documentacao` — não é a documentação final. O Volume 2 (o painel web) está em
> `docs/painel/dossie/dossie.md`.
>
> Sem capturas neste volume: é um volume de fluxos e diagramas (os dados estruturados estão em `dados.json`).
> Nenhum valor de `.env`, ID de conta/app/página, token, nome de bucket ou URL privada aparece aqui — só **nomes**
> de variáveis, permissões e endpoints.

---

## 1. O que é o estúdio

O Korvu Studio é um estúdio de Reels sobre Inteligência Artificial que roda **inteiro num Mac**: do tema à publicação
no Instagram e no Facebook, e depois a leitura das métricas, que volta para o roteirista. Quem trabalha são **agentes
do Claude Code** (`.claude/agents/*.md`), cada um com um papel (roteirista, editor, colorista, publicador…), mais
scripts Python rodados com `uv` (`CLAUDE.md`, seção Pipeline). O apresentador grava; o resto — transcrição, corte,
cor, legendas, música, capa, QA, pacote, agendamento, publicação, resposta aos comentários e métricas — é automático,
com dois pontos de parada humanos: a **aprovação da EDL** (o corte) e a **ida para a fila** (`06-publicar/`).

Não há servidor nem ferramenta de automação de terceiros. O "orquestrador" é o próprio macOS: cinco agendadores
`launchd` chamam scripts locais em intervalos fixos (`scripts/launchd/instalar.sh`), e um sexto sincroniza o índice de
contexto (`estudio-contexto/launchd/uk.korvu.contexto.plist`). A comunicação com a Meta é por HTTP direto na Graph
API (`scripts/publicar.py`, biblioteca `requests`); comentários são lidos por **consulta periódica** (a cada 2 min), em
vez de webhook (`automacao-meta/ARQUITETURA.md` §1).

**O que ele NÃO faz:** não usa n8n, Zapier, Make nem ManyChat (`automacao-meta/ARQUITETURA.md` §4 — ManyChat
"descartado em 15/09", n8n "não é usado"); não conversa no direct nem é CRM (decisão de 09/10, `automacao-meta/README.md`);
não publica nada que não esteja em `06-publicar/` com pacote aprovado (`CLAUDE.md` regra 2; `scripts/publicar.py`
docstring); não recebe webhooks (não precisa de endereço público).

---

## 2. Arquitetura — o sistema inteiro numa página

```
 PRODUÇÃO (agentes Claude Code + scripts uv)          DISTRIBUIÇÃO (launchd + Graph API)            LEITURA
 ───────────────────────────────────────────          ──────────────────────────────────            ───────
 tema → roteiro → [PORTÃO] → gravação →               06-publicar/<slug>/ (fila = autorização)
 edição (Scribe, EDL) → ⏸ o autor aprova →             │  publicar.py --due (15 min)
 cor → Remotion → música/áudio → capa →               ├─▶ R2 (vídeo, capa, slides, PDF — link público)
 [PORTÕES] → 05-render-pronto/<slug>/  ──/publicar──▶ ├─▶ Instagram (Graph: /media → /media_publish)
                                                      ├─▶ Facebook (rupload / graph-video / photos+feed)
                                                      └─▶ 07-publicados/<slug>/ + dm-material.json
                                                            │
                                                            ├─ responder_comentarios.py (2 min):
                                                            │    /ordered_comments → /{page}/messages (direct com PDF)
                                                            │    → /{comment}/replies (resposta pública)
                                                            └─ metricas.py (09:30, ≥ 5 dias): /insights
                                                                 → metricas.json → analista-de-metricas
                                                                 → _controle/aprendizados.md → roteirista
 painel/sync/sincronizar.py (15 min) lê tudo isso → Postgres local → painel web (Volume 2)
```

Fontes: `CLAUDE.md` (Pipeline), `scripts/publicar.py`, `scripts/responder_comentarios.py`, `scripts/metricas.py`,
`scripts/launchd/*.plist`, `automacao-meta/ARQUITETURA.md`.

### Exemplo real do caminho de um dado: a palavra-chave até o direct
1. O roteirista escreve `cta_palavra` no frontmatter do `roteiro.md`; o `produtor-de-material` gera o PDF em
   `videos/<slug>/material/<arquivo>.pdf` (`scripts/gerar_material_pdf.py`, Chrome headless).
2. O `montar_pacote.py` leva **só esse PDF** para `05-render-pronto/<slug>/material/` (`scripts/montar_pacote.py`).
3. O `publicador` escreve `post.json` com `material = {palavra, arquivo, titulo, url: null}` (`.claude/commands/publicar.md`).
4. Na hora, o `publicar.py` sobe o PDF para o R2 público e grava a URL em `post.material.url`; recusa qualquer arquivo
   fora de `material/` e avisa sobre sobras que **não** sobem (`publicar_slug`).
5. Publicado o Reel no Instagram, grava `dm-material.json` = `{palavra, media_id_instagram, material_url[, formato]}`
   na pasta, que vai para `07-publicados/<slug>/`.
6. A cada 2 min, `responder_comentarios.py` lê esse arquivo (Reels com menos de 7 dias), busca os comentários, acha a
   palavra, manda o direct com o link e depois responde em público (`passagem`).

---

## 3. Tecnologia

| Camada | Tecnologia | Versão | Por quê (só se escrito) | Fonte |
|---|---|---|---|---|
| Linguagem dos scripts | Python | ≥ 3.12 | — | `pyproject.toml` (`requires-python`) |
| Gerenciador / executor | uv | 0.12.14 (no Mac) | "rodar sempre com `uv run`" | `CLAUDE.md` (Ferramentas); `uv --version` |
| HTTP para Meta | requests | 2.34.2 | — | `uv.lock`; `scripts/publicar.py` |
| Upload para o R2 (API S3) | boto3 | 1.43.94 | — | `uv.lock`; classe `R2` em `scripts/publicar.py` |
| Transcrição (API) | SDK `elevenlabs` (Scribe) | 2.68.0 | Scribe é "mais literal" que o Whisper | `uv.lock`; `corte-por-roteiro/SKILL.md` (Troubleshooting) |
| Transcrição (local, alternativa) | mlx-whisper (`whisper-large-v3-turbo`) | 0.4.3 | sem API, Apple Silicon | `uv.lock`; `transcribe.py` |
| Imagem / rosto para o zoom | Pillow · OpenCV headless | 12.3.0 · 4.14.0.94 | — | `uv.lock`; `edl.py` (`CascadeClassifier` Haar frontal) |
| Áudio / sinais | numpy · scipy · soundfile | 2.5.3 · 1.18.1 · — | — | `uv.lock` |
| Alinhamento de texto | rapidfuzz | 3.14.6 | — | `uv.lock` |
| Config | PyYAML · python-dotenv | 6.0.3 · 1.2.3 | — | `uv.lock` |
| Vídeo/áudio | ffmpeg estático + ffprobe | não fixada | ffmpeg "com libass/zimg" | `.env.example` (`FFMPEG_BIN`, `FFPROBE_BIN`) |
| Gráficos, legendas, animações | Remotion · React · TypeScript | 4.0.525 · 19.2.3 · 5.9.3 | — | `remotion/package.json` |
| Download do YouTube | yt-dlp (Homebrew) | 2026.08.19 (no Mac) | — | `scripts/buscar_youtube.py`, `scripts/baixar_obra.py`; `yt-dlp --version` |
| PDF do material | Chrome headless | — | "não há reportlab/weasyprint no projeto, e o Chrome já está na máquina" | `scripts/gerar_material_pdf.py` |
| Agendamento | launchd (macOS) | — | sem servidor: o script pergunta em vez de receber webhook | `automacao-meta/ARQUITETURA.md` §1 |
| Agentes | Claude Code (subagentes `opus`) | — | — | `.claude/agents/*.md` (campo `model`) |
| Ajuste fino manual | DaVinci Resolve (FCPXML + MCP) | — | "reserva do autor para ajuste fino à mão" | `corte-por-roteiro/SKILL.md` (Timeline no DaVinci Resolve); `.mcp.json` |
| Banco do painel e do índice | Postgres local (Supabase) | ver Volume 2 | — | `docs/painel/dossie/dossie.md` |

---

## 4. Integração com a Meta (Graph API) — passo a passo

### 4.1 O que o código espera (pré-requisitos)
Fonte: `automacao-meta/CONFIGURAR-APP-META.md` §3.
- Caminho **Facebook Login**: host `https://graph.facebook.com/v23.0` (versão por `META_GRAPH_VERSION`, padrão
  `v23.0` — `scripts/publicar.py`), com o Instagram **ligado a uma Página do Facebook**.
- Conta do Instagram **profissional** (Criador ou Empresa) e **pública** ("comentário de conta privada não chega à API").
- Um app na Meta for Developers; quem configura é **administrador** do app.
- O caminho "API do Instagram com login do Instagram" (host `graph.instagram.com`, tokens `IGAA…`) **não** é o que o
  código usa.

### 4.2 Permissões (nomes exatos) e quem as usa
| Permissão | Para quê | Conferida por |
|---|---|---|
| `instagram_basic` | ler conta, mídia, comentários | `publicar.py` (`ESCOPOS_IG`), `responder_comentarios.py` (`ESCOPOS`), `metricas.py` |
| `instagram_content_publish` | criar contêiner e publicar Reel/carrossel | `publicar.py` (`ESCOPOS_IG`) |
| `instagram_manage_comments` | ler e responder comentários | `responder_comentarios.py` |
| `instagram_manage_messages` | resposta privada (direct) ao comentário | `responder_comentarios.py` |
| `instagram_manage_insights` | `GET /{media}/insights`, insights da conta | `metricas.py`, `perfil.py` |
| `pages_show_list` | listar a Página (`/me/accounts`) | `publicar.py` (`ESCOPOS_PAGINA`) |
| `pages_read_engagement` | ler a Página e o engajamento | `publicar.py`, `responder_comentarios.py`, `metricas.py` |
| `pages_manage_posts` | publicar Reel, vídeo e fotos na Página | `publicar.py` (`ESCOPOS_PAGINA`) |
| `read_insights` | `GET /{video}/video_insights` no Facebook | `metricas.py`, `perfil.py` |
| `pages_manage_engagement` | a Página comentar o próprio post (1.º comentário no FB) | só um aviso no log de `publicar.py` (`comentar_primeiro`) |
| `pages_manage_metadata`, `business_management` | "se a tela pedir" | `CONFIGURAR-APP-META.md` §3 |

### 4.3 Tokens: tipo, como obter, renovação
Fonte: `automacao-meta/CONFIGURAR-APP-META.md` §3 e §5; `scripts/publicar.py` (`cmd_verificar`).
1. Graph API Explorer → escolher o app → gerar token com as permissões → escolher a Página e a conta do Instagram.
2. Access Token Debugger → "Estender token de acesso" → token de **usuário de longa duração (~60 dias)**.
3. Com esse token, `GET me/accounts` → `id` da Página (`META_PAGE_ID`) e `access_token` da Página — tirado de um
   token longo, "normalmente **não expira**".
4. `GET {page-id}?fields=instagram_business_account` → `id` = `INSTAGRAM_USER_ID`.
5. `INSTAGRAM_ACCESS_TOKEN` "pode ser o **mesmo** token da Página".
6. Conferir: `uv run python scripts/publicar.py verificar-tokens` — chama `GET /{ig-user-id}?fields=id,username,name`,
   `GET /me`, `GET /{page-id}?fields=id,name` e `GET /debug_token` (com `app_id|app_secret`) e mostra validade, tipo,
   expiração e **escopos em falta**; avisa se o token **expira em menos de 7 dias**. Também faz `HEAD` no bucket do R2.
   Os valores aparecem mascarados (`mascarar_valor`: 4 primeiros caracteres + tamanho).

**Renovação:** não há renovação automática no código (nenhuma chamada a `oauth/access_token` /
`fb_exchange_token` em `scripts/`). O aviso dos 7 dias e o erro 190 ("token inválido ou expirado — gere um novo e
rode `verificar-tokens`", `DICAS` em `publicar.py`) são os sinais; a renovação é manual pelo passo 1–3.

Variáveis (só nomes): `INSTAGRAM_USER_ID`, `INSTAGRAM_ACCESS_TOKEN`, `META_PAGE_ID`, `META_PAGE_ACCESS_TOKEN`,
`META_APP_ID`, `META_APP_SECRET`, `META_GRAPH_VERSION` (opcional), `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`,
`R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL`, `TZ_PUBLICACAO` (`.env.example`; `publicar.py` docstring).

### 4.4 De onde a Meta busca o arquivo (R2 × upload direto)
Fonte: `scripts/publicar.py` (`R2`, `publicar_slug`, `publicar_facebook*`).
- **Instagram busca por URL pública.** O script sobe para o Cloudflare R2 (API S3 via boto3, `CacheControl: public,
  max-age=31536000`) e passa a URL: `video_url` + `cover_url` (capa convertida PNG → JPEG) no Reel; `image_url` (JPEG
  qualidade 95) em cada slide do carrossel. Chaves no bucket: `reels/<slug>/…` e `carrosseis/<slug>/…`.
  Antes de chamar a Meta, faz `HEAD` na URL e exige HTTP 200 (`conferir_publico`).
- **Facebook recebe o arquivo do disco**, não por URL: "o robô do Facebook leva 403 da Cloudflare" no domínio público
  do R2, "embora o do Instagram baixe normalmente (13/10)".
- **O PDF do material** também vai para o R2 (`<base>/material/<arquivo>.pdf`) — é o link do direct.

### 4.5 Publicar um Reel — endpoints na ordem
**Instagram** (`publicar_instagram`):
1. `POST /{ig-user-id}/media` com `media_type=REELS`, `video_url`, `caption`, `share_to_feed`, `cover_url` e, se
   Trial, `trial_params` (JSON `{"graduation_strategy": "MANUAL" | "SS_PERFORMANCE"}`) → `container_id` (gravado no
   `post.json` com a impressão do portão).
2. `GET /{container-id}?fields=status_code,status` a cada 5 s, até 10 min, até `FINISHED` (`ERROR`/`EXPIRED` = falha).
3. `POST /{ig-user-id}/media_publish` com `creation_id` → `media_id`. **Não é idempotente**: antes de repetir, o script
   confere se o contêiner já está `PUBLISHED` e procura o post pela legenda em `GET /{ig-user-id}/media` (evita duplicado).
4. `GET /{media-id}?fields=permalink`.
5. `POST /{media-id}/comments` com o texto de `primeiro-comentario.txt` (a própria conta comenta; decisão de 09/11).

**Facebook, vídeo ≤ 90 s → Reel da Página** (`publicar_facebook`; "API de Reels da Página só aceita 3–90 s"):
1. `POST /{page-id}/video_reels` `upload_phase=start` → `video_id`, `upload_url`.
2. `POST https://rupload.facebook.com/video-upload/{v}/{video-id}` com os bytes do arquivo (`Authorization: OAuth …`,
   `offset`, `file_size`).
3. `GET /{video-id}?fields=status` até `uploading_phase = complete` (até ~5 min).
4. `POST /{page-id}/video_reels` `upload_phase=finish`, `video_state=PUBLISHED`, `description`.
5. `GET /{video-id}?fields=status,permalink_url` até pronto; depois `POST /{video-id}/comments` (1.º comentário).

**Facebook, vídeo > 90 s → Vídeo da Página** (`_upload_video_retomavel`, `publicar_facebook_video`), upload retomável
em `https://graph-video.facebook.com/{v}/{page-id}/videos`: `upload_phase=start` (`file_size`) → `transfer` em pedaços
(`video_file_chunk`, `start_offset`) → `finish` (`description`, `published=true`). O envio num pedido só "deu 413 com
171 MB (Hinton, 15/10)".

### 4.6 Publicar um carrossel (desde 09/11)
Fonte: `scripts/publicar.py` (`publicar_instagram_carrossel`, `publicar_facebook_fotos`); `docs/contratos.md` §9c.
- 3–10 slides (`SLIDES_MIN, SLIDES_MAX`); PNG vira JPEG ("a API do IG só aceita JPEG em `image_url`").
- **Instagram:** um `POST /{ig-user-id}/media` por slide com `image_url` + `is_carousel_item=true` → espera cada filho
  `FINISHED` → `POST /{ig-user-id}/media` com `media_type=CAROUSEL`, `children`, `caption` → `media_publish`.
- **Facebook:** cada slide sobe do disco em `POST /{page-id}/photos` com `published=false` (multipart `source`) → um
  `POST /{page-id}/feed` com `message` e `attached_media[i]={"media_fbid": …}`. O `/feed` "não é idempotente: uma
  tentativa só".
- Sem Trial e sem capa separada (a capa é o 1.º slide) — `post_padrao`.

### 4.7 Agendamento — como a hora é respeitada
Fontes: `scripts/publicar.py` (`cmd_agendar`, `cmd_due`, `proximas_vagas`), `_controle/calendario.md` (bloco YAML),
`scripts/launchd/uk.korvu.publicar.plist`.
- **A Meta não guarda o agendamento.** A hora mora no `post.json` (`publicar_em`, ISO com fuso) da pasta em
  `06-publicar/<slug>/`. Mover a pasta para lá = autorização (`.claude/commands/publicar.md`).
- `publicar.py agendar <slug> [--em "AAAA-MM-DD HH:MM"]` valida o pacote e reserva a **próxima vaga livre** das
  `vagas_semanais` do calendário (ex.: domingo 19:00, terça 21:00; fuso configurável
  em `fuso` ou `TZ_PUBLICACAO`), pulando vagas já ocupadas na agenda e em outros `post.json`; procura até 8 semanas.
- O launchd `uk.korvu.publicar` roda `publicar.py --due` a cada **900 s**. Para cada `post.json` com
  `estado = agendado` e `publicar_em ≤ agora`, publica. Precisão = até 15 min depois da hora.
- **Mac desligado/dormindo:** se o atraso passar de `PUBLICAR_ATRASO_MAX_H` (padrão **6 h**), não publica sozinho:
  muda para `aguardando_confirmacao` e manda notificação do macOS; confirma-se com `publicar <slug> --sim`.
- `modo_confirmar_restantes` (> 0 = os primeiros N posts pedem confirmação; hoje 0).
- Trava de arquivo (`_controle/.publicar.lock`, `fcntl`) impede duas execuções ao mesmo tempo.
- Depois de publicar em todas as plataformas: move a pasta para `07-publicados/<slug>/`, atualiza agenda do
  calendário, `_controle/tracker.md` e `status.json` do vídeo, e notifica com os links.

### 4.8 Trial Reel
Fontes: `scripts/publicar.py` (`post_padrao`, `publicar_instagram`), `docs/contratos.md` §10, `docs/decisoes.md`.
- Campo `instagram.trial` no `post.json`: `null` ou `{"graduation_strategy": "MANUAL|SS_PERFORMANCE"}`; enviado como
  `trial_params` no `POST /media`. Só no Instagram ("lá [no FB] não existe modo teste pela API: sai normal").
- Padrão vem de `trial_padrao` do calendário — hoje **vazio** ("Trial suspenso em 22/10"). Regra do par A/B em
  `docs/decisoes.md`: versão A normal na página (IG + FB), versão B em Trial com graduação MANUAL (só IG).
- `metricas.py` lê de volta `GET /{media}?fields=trial_params`.

### 4.9 Comentário → resposta pública + direct com o PDF
Fontes: `scripts/responder_comentarios.py`, `automacao-meta/respostas.yaml`, `automacao-meta/ARQUITETURA.md` §2–3.
1. A cada **120 s** (launchd `uk.korvu.comentarios`), lê `07-publicados/*/dm-material.json` dos posts publicados há
   menos de `janela_dias` (7).
2. Para cada post: `GET /{media-id}/ordered_comments` **e** `GET /{media-id}/comments` (campos
   `id,text,timestamp,username,from,replies{id,from}`, 50 por página, até 40 páginas), juntando sem repetir.
3. Filtra: ignora a própria conta; casa a palavra sem acento/maiúscula/pontuação; aceita plural (`S`/`ES`) se
   `aceitar_plural`; palavra dentro de outra não conta; ignora comentário que já tem resposta da conta (feita à mão) e
   quem já recebeu o material naquele post.
4. **Direct primeiro:** `POST /{page-id}/messages` com `recipient={"comment_id": …}` e `message={"text": …}`, token
   da Página (resposta privada). Texto: `mensagem_direct` ou `mensagem_direct_carrossel` do yaml, com `{usuario}`,
   `{material}`, `{link}`.
5. **Só se o direct saiu**, resposta pública: `POST /{comment-id}/replies` com uma das 5 frases sorteadas.
6. Estado em `_controle/comentarios/estado.json` (quem recebeu, quando, tentativas).

Limites do yaml: `max_envios_por_execucao: 25`, `max_envios_por_hora: 150`, `intervalo_entre_envios_s: 4`;
`ativo: false` desliga tudo. Erros: subcódigos de "esta pessoa não pode receber" (`2018001`, `2018108`, `2018278`,
`2534014`, `2534022`, `1545041`, código `551`) desistem só daquela pessoa; códigos de configuração (`3, 10, 102, 190,
200`) **param a passagem sem descartar ninguém** e notificam no máximo 1×/hora; o resto tenta de novo até 5 vezes.

### 4.10 Métricas aos 5 dias
Fonte: `scripts/metricas.py`, `scripts/launchd/uk.korvu.metricas.plist`.
- launchd `uk.korvu.metricas` 1×/dia às **09:30**; lê posts com **≥ 5 dias** (`DIAS_PADRAO`) ainda sem leitura completa.
- Instagram: `GET /{media}?fields=like_count,comments_count,permalink,timestamp,media_product_type,media_type,is_shared_to_feed`
  e `GET /{media}/insights?metric=views,reach,likes,comments,saved,shares,total_interactions,ig_reels_avg_watch_time,ig_reels_video_view_total_time,follows,profile_visits`.
- Facebook: `GET /{video}/video_insights` com `blue_reels_play_count`, `fb_reels_total_plays`, `fb_reels_replay_count`,
  `post_video_avg_time_watched`, `post_video_view_time`, `post_impressions_unique`, `post_video_followers`,
  `post_video_social_actions`, `post_video_likes_by_reaction_type` — "pede-se tudo e fica o que responder".
- Calcula `% médio assistido = tempo médio / duração` e taxas sobre o alcance; junta os comentários da palavra do
  `estado.json`. **Limite:** "a Meta NÃO dá a curva de retenção segundo a segundo" pela API.
- Grava `07-publicados/<slug>/metricas.json` e reescreve `_controle/metricas.md`. Saída 3 = permissão de insights em falta.
- Depois chama `acertos.py` (`avisar_acertos`): vídeo muito acima da mediana → aviso para `/multiplicar`.
- Hoje **carrossel não é lido** ("o metricas.py só lê Reel por enquanto").

### 4.11 Perfil
Fonte: `scripts/perfil.py`. Manual (não é job). Só `GET`: conta (`username,name,biography,website,followers_count,…`),
insights diários da conta (`metric_type=total_value`, janela ≤ 30 dias), alcance por `breakdown`, demografia,
últimos 30 posts e seus insights; Página, posts e vídeos da Página. Grava `_controle/perfil/AAAA-MM-DD.json` para o
agente `auditor-de-perfil`. Saída 2 = leu com pedidos recusados.

### 4.12 Erros conhecidos e limites
| Situação | O que o código faz | Fonte |
|---|---|---|
| `/comments` deixou de devolver comentários novos de quem não tem papel no app (~03/11) | lê também `/ordered_comments` | `responder_comentarios.py` (`comentarios`) |
| Robô do FB leva 403 da Cloudflare no R2 | FB sobe do disco (rupload, graph-video, photos) | `publicar.py` (13/10) |
| Upload de 171 MB num pedido só → 413 | upload retomável em pedaços | `publicar.py` (15/10) |
| `/{ig-user-id}/messages` → "(#3) Application does not have the capability" | direct sai por `/{page-id}/messages` | `responder_comentarios.py` (13/10) |
| `media_publish` e `/feed` não idempotentes | confere estado antes de repetir; 1 tentativa no `/feed` | `publicar.py` |
| Códigos transitórios `1, 2, 4, 17, 32, 341, 613, 80001, 80002`, HTTP 5xx/429 | até 5 tentativas, espera exponencial (máx. 60 s) | `publicar.py` (`Http.req`) |
| 9004 | "a Meta não conseguiu baixar a mídia do URL (o R2 está público?)" | `publicar.py` (`DICAS`) |
| 2207026 | formato de vídeo não suportado (H.264/AAC, 9:16, 3 s–15 min) | idem |
| 36003 / 2207009 | proporção fora de 4:5 a 1,91:1 — "o 3:4 do modelo pode não passar" | idem |
| Legenda > 2.200 caracteres, > 5 hashtags | pacote inválido | `validar_pacote` |
| Vídeo fora de 3–900 s | pacote inválido; > 300 MB só aviso | idem |
| 1 direct por comentário, até 7 dias; quem não segue recebe em "Solicitações" | material vai como link já na 1.ª mensagem | `ARQUITETURA.md` §3 |
| App em "Acesso Padrão" pode só falar com quem tem papel no app | se falhar, pedir App Review de `instagram_manage_messages`/`instagram_manage_comments` | `CONFIGURAR-APP-META.md` §3 |

Segurança do log: `mascarar` e um filtro de logging tiram os valores de `INSTAGRAM_ACCESS_TOKEN`,
`META_PAGE_ACCESS_TOKEN`, `META_APP_SECRET`, `R2_SECRET_ACCESS_KEY`, `R2_ACCESS_KEY_ID` de qualquer mensagem
(`publicar.py`). `--dry-run` percorre o fluxo inteiro e só imprime os pedidos.

---

## 5. Automação local sem terceiros

### 5.1 Os jobs
| Job (label) | Script | Intervalo | Lê | Escreve | Log |
|---|---|---|---|---|---|
| `uk.korvu.publicar` | `scripts/publicar.py --due` | 900 s | `06-publicar/*/post.json`, pacote, `_controle/calendario.md` | R2, Meta, `post.json`, `dm-material.json`, move para `07-publicados/`, calendário, tracker, `status.json` | `_controle/logs/publicar.log` |
| `uk.korvu.comentarios` | `scripts/responder_comentarios.py` | 120 s | `07-publicados/*/dm-material.json`, `post.json`, `automacao-meta/respostas.yaml`, comentários na Meta | direct + resposta na Meta, `_controle/comentarios/estado.json` | `_controle/logs/comentarios.log` |
| `uk.korvu.metricas` | `scripts/metricas.py` | todo dia 09:30 | `07-publicados/*/post.json`, insights na Meta, `estado.json` | `07-publicados/<slug>/metricas.json`, `_controle/metricas.md`, `_controle/acertos.json` | `_controle/logs/metricas.log` |
| `uk.korvu.painel` | `painel/sync/sincronizar.py` | 900 s + ao entrar na sessão | arquivos do projeto (só leitura) | Postgres local do painel | `_controle/logs/painel.log` |
| `uk.korvu.contexto` | `python -m contexto.sincronizar` (em `estudio-contexto/`) | 1800 s + ao entrar, IO baixa prioridade | documentos do projeto | schema `contexto` no Postgres local | `estudio-contexto/logs/contexto.log` |

Fontes: `scripts/launchd/*.plist`, `scripts/launchd/instalar.sh`, `estudio-contexto/launchd/uk.korvu.contexto.plist`.

### 5.2 Como é montado
- Os `.plist` são **modelos**: `instalar.sh` troca `__UV__`, `__PROJETO__` e `__HOME__`, valida com `plutil -lint`,
  copia para `~/Library/LaunchAgents/` e carrega com `launchctl bootstrap` + `enable`. Forçar uma execução:
  `launchctl kickstart -k gui/$(id -u)/<label>`. Desinstalar: `scripts/launchd/desinstalar.sh [label]`.
- Cada job roda `uv run --quiet python <script>` com `WorkingDirectory` na raiz, `ProcessType=Background`, `PATH` com
  Homebrew e `~/bin`, `LANG=pt_BR.UTF-8`, `PYTHONUNBUFFERED=1`; saída e erro no mesmo log.
- Os scripts carregam o `.env` da raiz com python-dotenv (`publicar.py`); os outros reaproveitam `publicar.py` (Http,
  máscara de segredos, log, notificação).
- Notificações: `osascript -e 'display notification …'` (som "Glass") — só no macOS (`notificar`).
- macOS protege `~/Documents` (TCC): se o log mostrar "Operation not permitted", dar acesso a Pastas/Documentos ao
  binário do uv/python (`instalar.sh`, nota).

### 5.3 Por que não precisa de servidor nem de n8n/Zapier
- "Em vez de a Meta avisar (webhook, que exige um endereço na internet ligado 24 h), o script **pergunta** ao
  Instagram a cada 2 minutos" (`ARQUITETURA.md` §1).
- "Com o Mac desligado, nada se perde: a Meta deixa responder até 7 dias depois do comentário" (idem).
- A fila é uma pasta (`06-publicar/`), o estado é JSON no disco (`post.json`, `estado.json`), a agenda é o `launchd`.
- "Se um dia o atraso incomodar, o mesmo script pode ir para um servidor sem mudar nada" (idem).

### 5.4 Custo (só o que está escrito)
| Item | Custo | Fonte |
|---|---|---|
| API da Meta + scripts próprios | "Grátis, sem limite de contatos" | `ARQUITETURA.md` §4 |
| ManyChat | descartado — "pago por contato" | idem |
| ElevenLabs Music | "Exige plano pago (uso comercial)" | `docs/decisoes.md` (linha de 01/10) |
| ElevenLabs Scribe / Sound Effects | mesma chave; valor não documentado | `transcribe.py`, `gerar_sfx.py` |
| Cloudflare R2 | não documentado | — (seção 12) |
| Geração de imagem (OpenRouter / OpenAI) | "Gerar custa dinheiro"; valor não documentado; o `uso` de cada chamada fica no `imagens-geradas.jsonl` | `gerar-imagem/SKILL.md`, `gerar_imagem.py` |
| Claude Code | o painel estima custo a preço de tabela da API (ver Volume 2, tela Tokens) | `painel/sync/sincronizar.py` (`PRECOS`) |

---

## 6. Metodologia de edição

Fonte: **os scripts** (`.claude/skills/corte-por-roteiro/scripts/*.py`, `color-grading/scripts/aplicar_cor.py`,
`audio-polish/scripts/audio.py`, `qa-video/scripts/qa_check.py`, `legendas-animadas/scripts/render_reel.py`). O
`SKILL.md` da skill de corte serve só para a ordem dos passos e tem números antigos (seção 12). Contratos:
`docs/contratos.md` §0–§7.
Fluxo: **ingest → transcribe → locutores → align → edl → PARA (aprovação) → render → filmstrip → verify**, depois cor,
Remotion, música/áudio, capa, QA, pacote (`.claude/commands/renderizar.md`).

### 6.1 Antes de gravar
- O roteiro vira `roteiro.json` (`parse_roteiro.py`), com linhas `L01…` e cenas extras `E01…`.
- **Método "ChatGPT monitor":** o ChatGPT Voz, no alto-falante do celular, lê cada linha e o apresentador repete; o áudio
  tem **duas vozes com o mesmo texto**, e o corte usa só a dele (`SKILL.md`, introdução). Formatos de leitura:
  `teleprompter.txt`, `monitor-chatgpt.txt` (`.claude/commands/novo-video.md` passo 6).
- Câmera Lumix S5IIX em **V-Log**, 4K 25p 4:2:2 10-bit; o projeto inteiro roda a **25 fps** (`FPS_PROJETO`).

### 6.2 Os passos
| # | Passo | Script | Entra | Sai | Detalhe |
|---|---|---|---|---|---|
| 1 | Ingestão | `ingest.py` | `brutos/principal/`, `brutos/extras/` | `edicao/fontes/*.mp4` (1440×2560 — `LARGURA_INTER, ALTURA_INTER` em `common.py`; H.264 high422 `yuv422p10le` CRF 12; ainda V-Log), `edicao/audio48k/*.wav` (48 kHz 24-bit mono, `highpass=f=60:poles=2`, **sem redução de ruído** salvo `--limpar-ruido`), `edicao/extras/`, `fontes.json` | escala `lanczos+accurate_rnd+full_chroma_int`; celular/tela 30/60 → 25 fps; HDR → SDR (`zscale`) |
| 2 | Transcrição | `transcribe.py` | áudio do principal | `edicao/transcricao.json` (palavra com tempo) | **ElevenLabs Scribe v2** (`scribe_v2`, `language_code=por`, `timestamps_granularity=word`, `diarize=True`, `num_speakers=2`, `tag_audio_events=True`, até 100 `keyterms`) — `transcribe.py` — se houver `ELEVENLABS_API_KEY`; senão **mlx-whisper local**. Resposta bruta em cache `edicao/raw/<fonte>.scribe.json` |
| 3 | Locutores | `locutores.py` | transcrição + áudio | `locutor` por palavra + `edicao/locutores.json` (`zonas_ia`) | Camada A: diarização do Scribe; Camada B (local): graves, nível, centróide, pitch → k-means 2 classes → HMM. Qual é a IA: assinatura de celular, ordem (IA lê primeiro), frases de monitor, perfil da voz. Confiança baixa → `null` → [REVISAR] |
| 4 | Alinhamento + escolha do take | `align.py` | transcrição + `roteiro.json` | `edicao/alinhamento.json` | takes só com a voz dele, separados por silêncio ≥ 1,5 s (`GAP_TAKE`); **escolhido = o ÚLTIMO take limpo** (`sim` ≥ 0,80 = `SIM_OK`, sem `false_start`/`recomeco`/`final_cortado`/`sobreposicao_ia`) → [OK]; confiança < 0,60 ou locutor incerto → [REVISAR]; `sim` ≥ 0,45 (`SIM_PARAFRASE`) ou improviso que cobre ≥ 55 % da linha → [PARAFRASE]; abaixo → [FALTANDO]. Pontuação: `sim` 0,55 · cobertura 0,15 · fluência 0,10 · recência 0,10 · confiança 0,10 (`PESOS`). Flag `pausa_interna` = pausa > 0,7 s (`align.PAUSA_INTERNA`, só marca) |
| 5 | EDL | `edl.py` | alinhamento | `edicao/edl.json`, `edl.md`, `preview.mp4` (540×960 — `render_corte.py`), `edicao/resolve/<slug>.fcpxml` | regras de corte abaixo (números do `edl.py`); **zoom alternado 1.00 ↔ 1.12 nos cortes, com origem no rosto (Haar frontal do OpenCV)** |
| 6 | **PARA — aprovação** | — | `edl.md` + `preview.mp4` | `edl.json.aprovado = true` | regra rígida 1 do `CLAUDE.md`; pedidos ("L05 usa T1") editam a EDL e `edl.py --recalcular` |
| 7 | Render do corte | `render_corte.py` | EDL aprovada | `edicao/corte.mp4` (1080×1920, 10-bit, V-Log, zoom aplicado: recorte no 1440×2560 + lanczos) + `corte-audio.wav` (24-bit) | peças na grade de frames (40 ms a 25 fps); áudio com alças de 15 ms (`ALCA`) e cruzamento linear de 30 ms (`XFADE`), montado fora do ffmpeg |
| 8 | Ver os cortes | `filmstrip.py` | corte | `edicao/frames/corte-NN.png`, `contato.png` | 5 quadros em −0,2/−0,1/0/+0,1/+0,2 s (`OFFS`) + forma de onda de ±0,5 s (`ONDA_S`) em cada corte |
| 9 | Verificação | `verify.py` | corte | `qa/diff.md`, `qa/verificacao.json` | falha se faltar linha, WER > 8 % (`WER_MAX`), A/V ou duração fora de 1 frame, fps errado ou **voz da IA no corte > 0,2 s** (`VOZ_IA_MAX`) |

Regras de corte — valores de `.claude/skills/corte-por-roteiro/scripts/edl.py`, linhas 30–51 (alterados em 01/10;
o `SKILL.md` ainda mostra os antigos):
| Constante | Valor | O que faz |
|---|---|---|
| `PRE` | **0,06 s** | `in` = 1.ª palavra − 0,06 s (era 0,15) |
| `POS` | 0,08 s | sobra mínima depois da última palavra (era 0,18) |
| `PAUSA_ALVO` | **0,08 / 0,45 / 0,75 s** | `out` = última palavra + max(`POS`, pausa da linha): `normal` / `pausa` / `pausa_longa` (era 0,20/0,60/0,90) |
| `SNAP` | ±0,06 s | a borda procura o ponto mais silencioso nessa janela |
| `GUARDA_ENERGIA` | 0,04 s | o corte fica pelo menos isso fora do ataque/cauda medidos no áudio — **nunca entra na energia de uma palavra** |
| `PAUSA_INTERNA` → `PAUSA_RESTA` | **> 0,25 s fica 0,12 s** | pausa dentro da linha é encurtada (era > 0,7 s → 0,25 s) |
| `GAP_MULETA` | 0,15 s | silêncio que sobra no lugar de uma muleta cortada ("é", "hum", "tipo", "né", "então"… — `MULETAS` em `common.py`) |
| `MARGEM_IA` | 0,08 s | distância mínima entre ponto de corte e voz da IA (zona proibida); `MARGEM_IA_CORTE` 0,06 s |
| `MIN_PECA` | 0,8 s | peça menor que isso é fundida |
| `ZOOM_ESCALA` / `ZOOM_MAX` | 1,12 / 1,33 | escala do enquadramento fechado / máximo sem ampliar o 1440 (`common.py`) |
| `ZOOM_ORIGEM` | `50% 38%` | origem do zoom quando não acha rosto (`common.py`) |
| `ZOOM_SEGURA_MIN` | 1,0 s | um enquadramento segura pelo menos isso antes de trocar (função `alternar`) |

Zoom (`alternar`, `planejar_zoom` no `edl.py`): peças de câmera seguidas alternam 1.00 ↔ 1.12; a divisão de arquivo da
câmera não conta como corte; linha com `ZOOM` na TELA começa fechada; o que foi editado à mão é respeitado.

### 6.3 Do corte ao pacote
| Etapa | Quem / script | Saída | Fonte |
|---|---|---|---|
| Legendas | `gerar_props.py` | `edicao/legendas.json/.srt`, `reel-props.json` — **texto do roteiro**, não da transcrição; sem pontuação na tela | `docs/contratos.md` §6–7 |
| Revisão 1 | `revisor-de-video` (passagem 1) | corte + legendas | `renderizar.md` passo 3 |
| Cor | `colorista` (`aplicar_cor.py`) | `edicao/cor/corte-cor.mp4` (H.264 CRF 16, yuv420p bt709) | `color-grading/scripts/aplicar_cor.py` |
| Gráficos | Remotion (`render_reel.py`) | `edicao/render-remotion.mp4` (`--codec=h264 --crf=18 --pixel-format=yuv420p --color-space=bt709`) | `legendas-animadas/scripts/render_reel.py` |
| Música | `produtor-musical` (`gerar_musica.py`, ElevenLabs Music) | `videos/<slug>/musica/opcao-N.mp3` | `scripts/gerar_musica.py` |
| Áudio | `audio.py` | `edicao/final.mp4` | `audio-polish/scripts/audio.py` |
| Capa | `designer-de-capas` (`frame_candidates.py`, `render_capa.py`) | `capa/capa*.png` | `capa-reels/` |
| QA final | `revisor-de-video` (PORTÃO-CORTE) + `qa_check.py` | `qa/relatorio.md` | `qa-video/scripts/qa_check.py` (`SPEC`) |
| Pacote | `montar_pacote.py` | `05-render-pronto/<slug>/` com selo GAUNTLET | `scripts/montar_pacote.py` |
| Limpeza | `limpar_video.py --apagar` | só a revisão atual | `renderizar.md` passo 11 |

**Cor** (`color-grading/scripts/aplicar_cor.py`): por segmento, sempre a 16 bits por canal (`gbrp16le`):
`yuv → [LUT de entrada V-Log→Rec.709, só câmera com perfil vlog] → primária (curves por canal) → LUT da marca (lut3d
tetraédrica) → concat → yuv420p bt709 (+ grão)`. A primária mede cada take **depois** da entrada (luminância média e
gray-world nos meios-tons) e leva todos ao mesmo `alvo_primaria` do JSON da LUT, com limites de **±0,5 stop**
(`MAX_STOPS`, `--limite-ev`) e **±8 % por canal** (`MAX_CANAL`, `--limite-wb`). Grão: padrão **0** (`--grao`, 0–1).
LUT padrão = a versão mais alta com `"aprovada": true`. Nunca recebem cor: segmentos `tela-*` e extras de tipo
tela/print/imagem/video/animacao. Saída H.264 CRF 16, mesmos frames da fonte; áudio copiado.

**Áudio** (`audio-polish/scripts/audio.py`): mede o RMS da fala → `acompressor` **1,5:1** (`RAZAO`), limiar = RMS da
fala **+ 9 dB** (`LIMIAR_REL`), ataque 30 ms, release 300 ms, joelho ≈ 9 dB → ganho linear até **−14 LUFS** (`--lufs`)
→ `aresample` 192 kHz + `alimiter` com teto = alvo de true peak **− 0,3 dB** (`MARGEM_TP`; alvo `--tp` −1,5 dBTP) →
AAC 256k (`BITRATE`) a 48 kHz. Até 4 passadas corrigindo ganho/teto (tolerância ±0,3 LU, `TOL_LUFS`). Nenhum EQ.
Música (`--musica`): em loop, `--musica-db` padrão **−22 dB**, `sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300`
pela voz, `afade` de saída de 1,5 s. O vídeo não é recodificado; o script completa as tags bt709.

**QA automático** (`qa-video/scripts/qa_check.py`, dicionário `SPEC`): FAIL em resolução 1080×1920, fps =
`FPS_PROJETO` ±0,01 (padrão 25), codec h264 perfil High, `yuv420p`, AAC 48 kHz, duração **3–900 s** (limite de Reels da Meta, igual ao `publicar.py`; era 180 s até 12/11), faststart,
≤ 300 MB, ≤ 25 Mbps, loudness −14 ±1 LUFS, true peak ≤ −1,5 dBTP, cena extra faltando. Aviso: tags de cor, pretos
≥ 0,5 s, congelados ≥ 2 s, duração ±0,2 s da EDL, legendas × roteiro.

---

## 7. ElevenLabs — o que é usado de fato

A ElevenLabs **não baixa vídeo**. São três APIs dela, com uma chave só (`ELEVENLABS_API_KEY`):

| API | Para quê | Etapa | Script | Como chama | Saída |
|---|---|---|---|---|---|
| **Speech-to-Text (Scribe v2)** | transcrever a fala com tempo por palavra e separar as 2 vozes (diarização) | edição, passo 2 (`/editar`); também `/calibrar-voz` | `.claude/skills/corte-por-roteiro/scripts/transcribe.py` | SDK `elevenlabs` → `client.speech_to_text.convert(...)` | `edicao/raw/<fonte>.scribe.json`, `edicao/transcricao.json` |
| **Music** | trilha original por vídeo (instrumental, 2 opções) | `/musica`, passo de áudio do `/renderizar` | `scripts/gerar_musica.py` | `POST https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192`, cabeçalho `xi-api-key`, `model_id` padrão `music_v2_5`, `force_instrumental`, `composition_plan` opcional | `videos/<slug>/musica/opcao-N.mp3`, `musica.json` |
| **Sound Effects** | biblioteca de efeitos do sound design (whoosh, pop…) | uma vez / quando falta efeito | `scripts/gerar_sfx.py` (catálogo `00-marca/som/sfx.json`) | `POST https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_192` | `remotion/public/_marca/sfx/<nome>.mp3` |

- Sem a chave: a transcrição cai para **mlx-whisper local** (`--engine mlx`); efeitos têm reserva sintética sem API
  (`scripts/sfx_sintetico.py`, WAV); a música para e avisa (`.claude/commands/musica.md`).
- Por que Music: "A Meta Sound Collection não tem API (só abre logado no Facebook)" e a faixa é original, "sem gravação
  pré-existente para o Rights Manager casar" (`scripts/gerar_musica.py`; `.claude/agents/produtor-musical.md`).
- **Quem baixa vídeo é o yt-dlp** (seção 8).

---

## 8. Outras integrações

**14 integrações** no total, contando a Meta (seção 4), as três APIs da ElevenLabs (seção 7, uma linha cada no
`dados.json`) e as desta tabela. **Geração de vídeo por IA não está integrada** (`.claude/skills/gerar-imagem/SKILL.md`,
"Ainda não existe").

| Integração | Para quê | Como | Credencial | Script / quem | Quando |
|---|---|---|---|---|---|
| **YouTube (yt-dlp)** | baixar vídeos sobre a pessoa/assunto (material de comentário) e cortar trechos | `yt-dlp` CLI: `ytsearchN:` para buscar, `--dump-json` para metadados/crédito, `-f "bv*+ba/b" --merge-output-format mp4` | nenhuma | `scripts/buscar_youtube.py` (agente `buscador-de-videos`), `scripts/baixar_obra.py` (`curador-de-obra`); skill `watch` | `/novo-video` passo 4b, `/buscar-videos`, `/obra` |
| **archive.org + Wikimedia Commons** | B-roll com licença legível por máquina | APIs públicas de metadados (`advancedsearch.php`, `w/api.php`) | nenhuma | `scripts/buscar_video.py` | `/material` |
| **Cloudflare R2** | hospedar vídeo, capa, slides e PDF com link público para a Meta | API S3 (boto3), endpoint `https://<conta>.r2.cloudflarestorage.com` | `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL` | `scripts/publicar.py` | na publicação |
| **Anthropic / Claude Code** | todos os agentes (roteiro, edição, portões…) rodam como subagentes do Claude Code | `.claude/agents/*.md` (modelo `opus`), `.claude/commands/*.md`, `.claude/skills/*` | a do Claude Code (fora do projeto) | sessão do Claude Code | sob demanda; nenhum script chama a API da Anthropic direto (busca em `scripts/` e skills) |
| **Claude Design (claude.ai)** | desenhar animações explicativas | manual: o `animador` escreve o brief, o export HTML vai para `videos/<slug>/animacoes/<ID>/export/` e é portado para Remotion | — | `.claude/agents/animador.md` | `/animar` |
| **DaVinci Resolve** | ajuste fino manual do corte | `edl.py` gera `edicao/resolve/<slug>.fcpxml`; `resolve.py importar` lê de volta; MCP local em `.mcp.json` | — | `corte-por-roteiro/SKILL.md` | opcional |
| **Google Fonts** | fontes do PDF e do carrossel | CSS `fonts.googleapis.com` no HTML impresso | nenhuma | `scripts/gerar_material_pdf.py`, `scripts/gerar_carrossel.py` | ao gerar PDF/slides |
| **Groq / OpenAI Whisper** (opcional) | transcrição de reserva da skill `watch` quando o vídeo não tem legenda | `api.groq.com/.../audio/transcriptions`, `api.openai.com/v1/audio/transcriptions` | ver seção 12 | `.claude/skills/watch/scripts/whisper.py` | só na skill `watch` |
| **Geração de imagem** (OpenRouter · OpenAI) ⚠ não verificado com chamada real | imagem que não existe e não tem material livre: cena extra, animação, capa, carrossel, PDF | `POST https://openrouter.ai/api/v1/chat/completions` (`modalities: ["image","text"]`) · `POST https://api.openai.com/v1/images/generations` · `POST https://api.openai.com/v1/images/edits` (com `--ref`) | `OPENROUTER_API_KEY` (motores `teste` e `gemini`) · `OPENAI_API_KEY` (motor `openai`) | `.claude/skills/gerar-imagem/scripts/gerar_imagem.py`; chamada pelo `animador`, `produtor-de-extras` e `designer-de-capas` | sob demanda (desde 12/11) |
| **Hugging Face** | modelo de embedding `intfloat/multilingual-e5-small` do índice de contexto | baixado uma vez para o cache; o MCP roda com `HF_HUB_OFFLINE=1` | nenhuma | `estudio-contexto/` | sincronização a cada 30 min, sem rede |
| **Postgres/Supabase local** | banco do painel e do índice | `127.0.0.1` (ver Volume 2) | ver Volume 2 | `painel/sync/sincronizar.py`, `estudio-contexto/` | 15 / 30 min |

### 8.1 Geração de imagem (skill `gerar-imagem`, 12/11) — ⚠ não verificado com chamada real
Fonte: `.claude/skills/gerar-imagem/SKILL.md`, `.claude/skills/gerar-imagem/scripts/gerar_imagem.py`, `.env.example`.
Une duas integrações que o autor já usava em outros projetos (OpenRouter + Gemini e OpenAI `gpt-image-2`).

| `--motor` | Modelo | Endpoint | Chave | Papel |
|---|---|---|---|---|
| `teste` (**padrão**) | `sourceful/riverflow-v2-fast` | OpenRouter `chat/completions` | `OPENROUTER_API_KEY` | barato, para validar composição |
| `gemini` | `google/gemini-3.1-flash-image-preview` (Gemini 3.1 Flash Image) | OpenRouter `chat/completions`, `modalities: ["image","text"]`; referências como imagem em data URL base64 | `OPENROUTER_API_KEY` | final; "bom com referência de marca" |
| `openai` | `gpt-image-2` | `images/generations`; com `--ref` vira `images/edits` (multipart `image[]`) | `OPENAI_API_KEY` | final; tamanho padrão `1024x1536`, qualidade padrão `high` |

- **Quem chama:** os agentes `animador`, `produtor-de-extras` e `designer-de-capas`. As fichas deles mandam usar a
  skill "quando faltar uma imagem que não existe e não há material livre que sirva" (`.claude/agents/*.md`).
- **Como:** `uv run python .claude/skills/gerar-imagem/scripts/gerar_imagem.py --saida <arquivo.png> --prompt "…"
  [--motor teste|gemini|openai] [--ref <imagem>]… [--tamanho] [--qualidade] [--seco]`. Usa `urllib`, timeout de
  600 s, e lê a chave do ambiente ou do `.env` sem imprimi-la. A resposta vem em base64 e é gravada em PNG.
- **`--seco`:** mostra o pedido (URL, modelo, nº de referências, nome da chave usada) sem chave, sem rede e sem custo.
- **Onde salva:** o caminho de `--saida`. A skill indica `videos/<slug>/material/gerado/` (cena extra; depois vai para
  `brutos/extras/` pelo `produtor-de-extras`), `videos/<slug>/animacoes/<ID>/` e `carrosseis/<pasta>/`.
- **Registro:** cada imagem acrescenta uma linha em `imagens-geradas.jsonl` **na mesma pasta da saída**, com
  `data` (UTC), `motor`, `modelo`, `prompt`, `referencias` (nomes), `saida`, `bytes` e `uso` (o `usage` que a API
  devolve). O objetivo é "saber o que foi gerado, com quê, e conferir o gasto".
- **Regras:** nunca imagem realista de pessoa real além do autor (regra 3); texto dentro da imagem não (o texto
  de tela é do Remotion/Claude Design); imagem gerada que entra no vídeo passa pelo PORTÃO-IMAGEM; "gere **uma** e
  valide; nada de lote".
- **Estado (12/11):** as chaves ainda não estão no `.env` do Korvu Studio (informação do coordenador; eu não li o
  `.env`). O único teste foi em modo `--seco`. Nenhuma chamada real foi feita.
- **Não integrado:** geração de **vídeo** por IA ("Quando for, entra como skill própria").

---

## 9. Pipeline completo com agentes e portões GAUNTLET

Regra: **quem faz não aprova** (`CLAUDE.md` regra 13; `docs/gauntlet.md`). Cada departamento tem um portão que
audita e não constrói; o veredicto fica preso ao **sha256 dos arquivos** que ele viu (`scripts/portoes.py` →
`portoes.json`): arquivo mudado depois do APROVADO vence o veredicto e o portão roda de novo. S0/S1 bloqueiam, S2 vai
para o backlog; teto de 3 voltas, na 3.ª vira ESCALADO (decisão humana). O `montar_pacote.py` recusa sem portões e
sela o pacote; o `publicar.py` recusa pacote sem selo, arquivo diferente do aprovado e post sem PORTÃO-PUBLICACAO.

| # | Etapa | Quem constrói | Entra | Sai | Portão |
|---|---|---|---|---|---|
| 1 | Pauta | `estrategista` (`/ideias`) | notícias, `_controle/aprendizados.md` | `01-ideias/` | PAUTA (`portao-pauta`) |
| 2 | Roteiro | `roteirista` → `dramaturgo` | tema | `roteiro.md` narrativo | ROTEIRO (`revisor-de-roteiro`) |
| 3 | PDF da palavra-chave | `produtor-de-material` | roteiro + fontes | `material/<arquivo>.pdf` | ROTEIRO |
| 4 | Material em vídeo | `buscador-de-videos`, `curador-de-obra`, `pesquisador-de-material` | roteiro | `material/youtube/catalogo.*`, trechos em `brutos/extras/` | PAUTA |
| 5 | Leitura | scripts da skill `roteiro-reels` | roteiro | `teleprompter.txt`, `monitor-chatgpt.txt`, `historia-completa.txt` | — |
| 6 | Cenas extras e animação | `produtor-de-extras`, `animador` | roteiro | `brutos/extras/`, composições Remotion | IMAGEM (`portao-imagem`) |
| 7 | Gravação | o apresentador | — | `brutos/principal/` | — |
| 8 | Edição | `editor-de-video` (`/editar`) | brutos | EDL + preview | ⏸ **aprovação humana da EDL** |
| 9 | Corte + legendas | `editor-de-video`, `gerar_props.py` | EDL aprovada | `corte.mp4`, legendas | revisão 1 (`revisor-de-video`) |
| 10 | Cor | `colorista` (`/cor`) | `corte.mp4` | `corte-cor.mp4` | IMAGEM |
| 11 | Gráficos | Remotion (`render_reel.py`) | `reel-props.json` | `render-remotion.mp4` | — |
| 12 | Música + áudio | `produtor-musical`, `audio.py` | render | `final.mp4` | CORTE |
| 13 | Capa | `designer-de-capas` | corte com cor | `capa/capa*.png` | IMAGEM |
| 14 | QA final | `revisor-de-video` passagem 2 | `final.mp4` | `qa/relatorio.md` | **CORTE** |
| 15 | Pacote | `montar_pacote.py` | tudo aprovado | `05-render-pronto/<slug>/` + selo | exige pauta?/roteiro/imagem/corte |
| 16 | Fila e agenda | `publicador` (`/publicar`) + `publicar.py agendar` | pacote | `06-publicar/<slug>/`, legendas do post, `post.json` | PUBLICACAO (`portao-publicacao`) |
| 17 | Publicação | `publicar.py --due` (launchd) | fila | IG + FB, `07-publicados/` | confere selo + PUBLICACAO |
| 18 | Material no direct | `responder_comentarios.py` (launchd) | `dm-material.json` | direct + resposta | — |
| 19 | Métricas | `metricas.py` (launchd) → `analista-de-metricas` | insights | `metricas.json` → `_controle/aprendizados.md` | — |
| 20 | Acertos | `acertos.py` → `multiplicador-de-acertos` (`/multiplicar`) | métricas | série de ideias | PAUTA |

Agentes do estúdio (descrições em `.claude/agents/*.md`, todos `model: opus`): estrategista, pesquisador-de-material,
curador-de-obra, buscador-de-videos, roteirista, dramaturgo, revisor-de-roteiro, produtor-de-material,
produtor-de-extras, animador, editor-de-video, revisor-de-video, colorista, designer-de-capas, produtor-musical,
publicador, analista-de-metricas, multiplicador-de-acertos, auditor-de-perfil, portao-pauta, portao-imagem,
portao-publicacao. Do painel (Volume 2): designer-de-produto, engenheiro-frontend, engenheiro-backend,
portao-interface, portao-dados. Da documentação: documentador-tecnico, designer-de-documentacao.

---

## 10. Qualidade — testes rodados em 12/11/2026

Os testes da automação são scripts autônomos, sem rede (proxy morto `127.0.0.1:9`, Meta e R2 simulados —
`tests/publicar/test_publicar.py`). Rodados agora, da raiz:

| Teste | Comando | Resultado real | O que cobre (`tests/README.md`) |
|---|---|---|---|
| Publicação | `uv run python tests/publicar/test_publicar.py` | **112/116** (saída 1) | agendar, `--due`, confirmação, dry-run, launchd, selo GAUNTLET, carrossel, 1.º comentário, dm-material |
| Comentários | `uv run python tests/comentarios/test_responder.py` | **33/33** | palavra, plural, janela, limites, erros por pessoa × configuração, `ativo=false` |
| Métricas | `uv run python tests/metricas/test_metricas.py` | **32/32** | ≥ 5 dias, `--forcar`, taxas, métrica não suportada, permissão em falta (exit 3), só GET, plist 09:30 |
| Portões | `uv run python tests/portoes/test_portoes.py` | **64/64** | impressão congelada, S0/S1/S2, teto de 3 voltas, selo, legado, carrossel |

As 4 falhas da publicação: "próxima vaga = quarta 19:00 BST", "linha na Agenda do calendário", "segundo pacote salta
a vaga ocupada → sexta 19:00", "reagendar sem --reagendar mantém a vaga". O `tests/README.md` já registra "112/116 —
as 4 falhas são as vagas antigas do calendário (D1 em `_controle/backlog-portoes.md`)": o teste espera as vagas antigas,
o calendário mudou em 17/10. Não foram rodados (pedem mídia/ffmpeg): `tests/check_synthetic.py` (edição, README: 47/47
e 28/28 no modo monitor), `tests/cor/test_cor.py` (65/65 no README), `tests/test_cta_props.py` (11/11 no README).

Estado em produção (contado nas pastas, sem IDs): **16 publicações** em `07-publicados/` entre 13/10 e 11/11/2026 —
15 Reels e 1 carrossel; 9 saíram com `trial` no Instagram; no Facebook, 3 como Reel, 2 como vídeo da Página e 1 como
post de fotos; o 1.º comentário automático aparece nas 4 mais recentes. `launchctl list` mostra os 5 jobs carregados.

---

## 11. Como instalar e rodar do zero

Pré-requisitos (fontes: `CLAUDE.md` › Ferramentas, `.env.example`, `pyproject.toml`): macOS (launchd, `osascript`,
`sips`), Homebrew, `uv`, Python 3.12, ffmpeg + ffprobe, `yt-dlp`, Google Chrome (PDF), Node.js (Remotion), Claude Code.

```bash
# 1. dependências Python (na raiz)
uv sync                      # + `uv sync --extra local` para transcrever sem API (mlx-whisper, Apple Silicon)
cd remotion && npm install && cd ..
# 2. chaves: copiar .env.example → .env e preencher (nunca versionar o .env)
#    ELEVENLABS_API_KEY · INSTAGRAM_* · META_* · R2_* · TZ_PUBLICACAO · FFMPEG_BIN · FFPROBE_BIN
uv run python scripts/verificar_setup.py
# 3. conferir a Meta e o R2 (não publica nada)
uv run python scripts/publicar.py verificar-tokens
uv run python scripts/responder_comentarios.py verificar
uv run python scripts/metricas.py verificar
# 4. ensaio sem rede
uv run python scripts/publicar.py --due --dry-run
# 5. ligar os agendadores
bash scripts/launchd/instalar.sh            # os cinco; ou: instalar.sh uk.korvu.comentarios
bash estudio-contexto/launchd/instalar.sh   # o índice de contexto (precisa do Postgres do painel)
# 6. primeiro post real só com confirmação
uv run python scripts/publicar.py publicar <slug> --sim
```
Desligar: `ativo: false` em `automacao-meta/respostas.yaml`, ou `bash scripts/launchd/desinstalar.sh <label>`.

**Para reusar fora do Korvu Studio — o que trocar:**
| Depende da estrutura do projeto | Onde mudar |
|---|---|
| Pastas `06-publicar/`, `07-publicados/`, `_controle/` e o contrato do `post.json`/`pacote.json` | `docs/contratos.md` §9–10; constantes no topo de `publicar.py` |
| Selo GAUNTLET obrigatório para publicar | `portoes.conferir_pacote` em `validar_pacote` (ou a lista `_controle/gauntlet-legado.json`) |
| Vagas, fuso e Trial | bloco YAML de `_controle/calendario.md` |
| Textos do direct e da resposta pública, nome da conta | `automacao-meta/respostas.yaml` |
| Labels `uk.korvu.*` e caminhos dos logs | `scripts/launchd/*.plist`, `instalar.sh` |
| Câmera V-Log, 25 fps, LUT da marca | `FPS_PROJETO`, `CAMERA_PERFIL`, `00-marca/cor/luts/` |
| Método de 2 vozes (ChatGPT monitor) | funciona com 1 voz sem mudança (`SKILL.md`) |
| Transcrição em português | `language_code="por"` em `transcribe.py` |

Genérico e reaproveitável como está: o cliente HTTP com retentativa e máscara (`Http`), o upload R2 + `HEAD`, os fluxos
de endpoints da Meta, o upload retomável do FB, a leitura dupla `/ordered_comments` + `/comments`, o padrão "plist
modelo + instalar.sh".

---

## 12. Não confirmado / divergências

**Não confirmado**
1. Custo do Cloudflare R2 e do plano da ElevenLabs em uso — nenhum documento traz valor.
2. Plano/custo real do Claude Code — o painel só estima a preço de tabela da API.
3. Se as chaves da skill `watch` (Groq/OpenAI) estão configuradas. O `whisper.py` lê do ambiente ou de um `.env`
   próprio da skill. O `OPENAI_API_KEY` do `.env.example` é o da geração de imagem. Não li o `.env`.
4. Se o app da Meta passou por App Review: o código e `CONFIGURAR-APP-META.md` deixam como "o teste real decide";
   há 16 publicações e direct implementado, mas não confirmei no código se directs para contas de fora já saíram (só o
   `estado.json` diria, e não li conteúdo pessoal dele).
5. Se o token da Página atual "expira: nunca" — só `verificar-tokens` mostra, e eu não rodei chamadas reais.
6. Versão do ffmpeg e do Node.js — não fixadas em arquivo.
7. Se `pages_manage_engagement` está no token — o código só avisa quando o comentário no FB falha com 10/200.
8. **Geração de imagem:** não verificada com chamada real. As chaves `OPENROUTER_API_KEY`/`OPENAI_API_KEY` ainda não
   estão no `.env` (segundo o coordenador) e o teste foi só `--seco`. Não se sabe se os modelos respondem com esses
   nomes, nem o custo por imagem.

**Divergências (o código vence)**
1. `automacao-meta/ARQUITETURA.md` §1 diz "nunca publicou de verdade", "nunca rodou de verdade" e launchd "não
   instalado"; há 16 posts em `07-publicados/` e os 5 jobs carregados. Também diz "dois agendadores"; `instalar.sh`
   instala cinco (+ o do contexto).
2. `ARQUITETURA.md` cita "25/25 no teste offline" dos comentários; hoje são 33/33. E "62/62" da publicação; hoje 112/116.
3. A lista de permissões de `ARQUITETURA.md` §5 (7) não inclui `instagram_manage_insights` e `read_insights`, que o
   `metricas.py` e o `perfil.py` exigem, nem `pages_manage_engagement` (1.º comentário no FB).
4. `.claude/agents/publicador.md` diz que "por padrão todo Reel sai como Trial (`trial_padrao: SS_PERFORMANCE`)";
   o `_controle/calendario.md` tem `trial_padrao` **vazio** ("Trial suspenso em 22/10"). O código usa o calendário.
5. `qa-video/SKILL.md`: a descrição fala em "30 fps"; a tabela e o script usam `FPS_PROJETO` (25). O `qa_check.py`
   reprovava duração acima de 180 s, contra a decisão de 02/11 (sem teto); **corrigido em 12/11**: `dur_max` = 900 s,
   o mesmo limite do `publicar.py`.
6. `scripts/buscar_youtube.py` (docstring de 01/10) fala em "trecho curto, mudo por padrão, teto de citação"; a decisão
   de 14/10 tirou o teto (`CLAUDE.md` regra 4); `baixar_obra.py` já usa teto infinito por padrão (`TETO_TRECHO_S`).
7. `scripts/perfil.py` (docstring de 16/10) descreve o objetivo antigo de público por país/língua, superado pela decisão
   de 21/10 (`CLAUDE.md` › Identidade). O código só lê dados; a divergência é de texto.
8. **`corte-por-roteiro/SKILL.md` está com os números antigos das regras de corte** (o código mudou em 16/09 e
   01/10, `edl.py` linhas 30–37): diz `in` = − 0,15 s (código: `PRE` 0,06), `out` + 0,20/0,60/0,90 s (código:
   `PAUSA_ALVO` 0,08/0,45/0,75) e pausa interna > 0,7 s → 0,25 s (código: `PAUSA_INTERNA` 0,25 → `PAUSA_RESTA` 0,12).
   Também diz [PARAFRASE] para `sim` 0,60–0,80 e [FALTANDO] abaixo de 0,60; o `align.py` usa `SIM_PARAFRASE` = 0,45.
   A 1.ª versão deste dossiê copiou esses números do SKILL.md (bloqueio S0 do PORTÃO-INTERFACE,
   `painel/portoes/documentacao-estudio-2026-11-12-v1.md`); a seção 6 agora sai dos scripts.
9. `audio-polish/SKILL.md` e a docstring do `audio.py` dizem teto do limitador = alvo − 0,5 dB; a constante usada é
   `MARGEM_TP` = 0,3 dB (`audio.py` linha 49).
10. `corte-por-roteiro/SKILL.md` cita `scripts/resolve.py importar`; o arquivo está em
   `.claude/skills/corte-por-roteiro/scripts/resolve.py`.
11. `publicar.py` tem `registrar_material_dm` como "TODO(dm-bot): registrar … no Supabase"; não faz nada — o direct
   usa só o `dm-material.json`.

## Revisar antes de publicar
- Não há capturas neste volume.
- Alguns arquivos de origem citados contêm dados que **não** foram copiados aqui e não devem ir para o repositório
  público sem limpeza: `pyproject.toml` (e-mail no campo `authors`), `automacao-meta/CONFIGURAR-APP-META.md` (URL de
  webhook antigo e caminho absoluto do Mac), um comentário em `scripts/publicar.py` (domínio público do R2),
  `corte-por-roteiro/SKILL.md` e `audio-polish/SKILL.md` (caminho absoluto com o nome de usuário), `.mcp.json`
  (caminhos locais), `07-publicados/*/post.json`, `dm-material.json` e `_controle/comentarios/estado.json` (IDs de
  mídia/Página e nomes de quem comentou).
- `_controle/calendario.md` expõe o fuso e os horários de postagem — dado operacional, decidir se fica público.

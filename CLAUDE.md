# Korvu Studio — instruções para o Claude Code

> **Começando uma sessão?** Leia antes: `docs/decisoes.md` (as decisões de método, com o motivo), `HANDOFF.md` (o
> diário das sessões; modelo em `docs/handoff-modelo.md`) e `_controle/CONTINUAR.md` (o estado de cada vídeo; `_controle/`
> nasce no primeiro uso — calendário e tracker de exemplo em `exemplos/estudio-demo/_controle/`). **Não pergunte ao autor o que já está decidido.**

Produção de Reels sobre Inteligência Artificial para uma conta do Instagram + Página do Facebook, do tema até a
publicação. **Autor** = a pessoa que grava, decide e aprova (nos documentos, "o autor"); a conta vem de
`CONTA_INSTAGRAM` no `.env`.

## Áreas do projeto
Cada área tem o seu `CLAUDE.md`, que também carrega as regras daqui (o Claude Code sobe os `CLAUDE.md` da pasta onde
a sessão abre até a raiz). Regras transversais (identidade, legal, segredos) ficam só aqui.

| Área | Pasta | Instruções |
|---|---|---|
| **Estúdio de conteúdo** (roteiro → gravação → edição → publicação) | raiz (`.claude/`, `scripts/`, `remotion/`, `00-marca/`, `docs/`) | este arquivo |
| **Painel web** | `painel/` | `painel/CLAUDE.md` |
| **Automação Meta** (publicação, comentário→direct, métricas) | `automacao-meta/` (scripts em `scripts/`) | `automacao-meta/CLAUDE.md` |
| **Contexto do estúdio** (grafo + busca + MCP só leitura) | `estudio-contexto/` | `estudio-contexto/README.md` |

## Identidade (sempre)
- Todo conteúdo em **português do Brasil**: "você", "a gente", "tá", "pra". Nunca "tu"/"teu".
- Público padrão: **iniciantes absolutos em IA + donos de pequenos negócios**, em qualquer lugar do mundo. **Nunca**
  definir o público por país ou por língua ("lusófono", "imigrante", uma cidade).
- **Roteiro NARRATIVO** (`00-marca/modelo-roteiro-narrativo.md`): primeiro o texto corrido, depois as linhas; sem
  contagem de palavras; a duração é a que a história pedir (acima de 90 s o Facebook recebe como vídeo da Página). Um
  vídeo só, igual no IG e no FB. CTA de palavra-chave sempre FALADO, **só no fim**, palavra curta (até ~6 letras).
- Antes de escrever qualquer coisa falada, ler `00-marca/tom-de-voz.md` e `00-marca/voz-autor.md` (este tem
  prioridade quando calibrado — `/calibrar-voz`).

## Captação
- Câmera padrão: **V-Log (V-Gamut)**, 4K, **25 fps**, 4:2:2 **10-bit**, vertical (`00-marca/captura.md`). Celular e
  gravações de tela também entram.
- Todo o projeto roda a **25 fps** (`FPS_PROJETO`) — nunca converter para 30 (causa judder). Celular/tela a 30/60 são
  convertidos para 25 na ingestão.
- Intermediários (`fontes/` 1440×2560, `corte.mp4` 1080×1920 com o zoom alternado por corte) ficam em **10-bit 4:2:2
  e ainda em V-Log**; a conversão V-Log → Rec.709 (`00-marca/cor/luts/entrada-camera.cube`) e o look são aplicados só
  pelo colorista.
- Áudio sem perdas até o master: `edicao/audio48k/*.wav` (24-bit, só passa-altas, sem redução de ruído) →
  `edicao/corte-audio.wav` → `audio.py` (compressão suave, −14 LUFS, TP −1,5) → AAC só no final.
- Saída final: 1080×1920, 25 fps, H.264 8-bit 4:2:0 bt709.

## Pipeline
```
tema → /novo-video (roteirista → dramaturgo → revisor-de-roteiro → produtor-de-material: PDF do CTA
       → buscador-de-videos → leitura: teleprompter + monitor) → /extras (produtor-de-extras + animador)
     → o autor grava o PRINCIPAL (brutos/principal/) e as CENAS EXTRAS (brutos/extras/)
     → /editar (editor-de-video: alinhamento ao roteiro + EDL)  ⟶ PARA: o autor aprova a EDL
     (GAUNTLET: depois de cada etapa, o PORTÃO da área aprova ANTES de chegar ao autor; docs/gauntlet.md)
     → /renderizar: corte → revisor-de-video → colorista (/cor) → Remotion → /musica → áudio → QA final
     → pacote em 05-render-pronto/<slug>/
     → /publicar (move p/ 06-publicar/) → publicador escreve legendas e agenda
     → scripts/publicar.py (launchd) publica IG + FB na hora → 07-publicados/
     → (5 dias) scripts/metricas.py → analista-de-metricas → _controle/aprendizados.md → roteirista
     → vídeo muito acima da média (scripts/acertos.py) → /multiplicar → série de ideias no mesmo ângulo
```

## Onde fica cada coisa
| Pasta | Conteúdo |
|---|---|
| `00-marca/` | método: modelo de roteiro, tom de voz, hooks, CTA, layouts, design system, cor/LUT, som, regras legais |
| `videos/<slug>/` | área de trabalho de um vídeo (criada pelo `/novo-video`; fora do git) |
| `05-render-pronto/`, `06-publicar/`, `07-publicados/` | pacote final · fila (**mover para cá = autorização para publicar**) · arquivo |
| `_controle/` | tracker, calendário, métricas, aprendizados (fora do git — dados do seu estúdio) |
| `remotion/` | composições Remotion (Reel, Capa, Legendas, Títulos, Animações) |
| `painel/` | painel web (Next.js + Supabase local) |
| `docs/` | contratos, GAUNTLET, decisões e os dois volumes da documentação |
| `exemplos/` | estúdio de demonstração fictício (para o painel e os testes) |
| `.claude/skills/*/scripts/` | scripts Python (rodar sempre com `uv run`) |

## Convenções
- **Slug:** `AAAA-MM-DD-palavra-chave` (data prevista de gravação).
- **Linhas do roteiro:** `L01`, `L02`… (hooks alternativos `L01B`, `L01C`). **Takes:** `L03-T2`.
- **Coluna FALA = exatamente o que será dito.** Tudo o que não é fala vai na coluna TELA ou na tabela de cenas extras.
- **Pausa da capa:** toda gravação começa com o autor **parado 3 s olhando para a câmera, em silêncio**, antes da L01.
  Esse trecho fica fora do corte; é de lá que o `frame_candidates.py` tira o frame da capa.
- **Todo roteiro sai em formato de leitura**: `teleprompter.txt` + `monitor-chatgpt.txt` (texto para um assistente de
  voz ler linha a linha e corrigir o autor durante a gravação).
- **Gravação com monitor de voz:** o áudio tem DUAS vozes — a IA (lê primeiro) e o autor (repete). O editor identifica
  os locutores e corta **só a voz do apresentador**.
- `status.json` em cada vídeo + linha no `_controle/tracker.md` — todo comando atualiza os dois.
- **Uma revisão por vez:** cada render novo apaga o anterior (`uv run python scripts/limpar_video.py videos/<slug> --apagar`).
- Estados: `roteiro → gravacao → edicao → edl_aprovada → revisao → cor → legendas → capa → qa → pronto → agendado → publicado`.

## Regras rígidas
1. **Nunca renderizar o vídeo final sem `edl.json.aprovado = true`** (exceto se o autor pedir `--auto`).
2. **Nunca publicar fora do fluxo**: só publica o que estiver em `06-publicar/` com `pacote.json` QA PASS. Os primeiros
   posts pedem confirmação (`modo_confirmar_restantes` no `_controle/calendario.md`).
3. Nenhuma imagem realista de pessoas reais além do autor. Nada de logos de terceiros **como se fossem parceria**.
   **Mostrar a ferramenta de que o vídeo fala é permitido** (interface, nome e logo, para o público reconhecer); o
   limite é não sugerir parceria, patrocínio ou aval.
4. **Material de terceiros tem dois caminhos, e não se misturam:**
   - **B-roll** (o trecho ilustra outra coisa) → precisa de **licença de reuso**: `/material`, `scripts/buscar_video.py`.
   - **Comentário/reação** (o Reel fala **sobre** a obra/pessoa e o autor narra por cima) → `/obra`,
     `scripts/baixar_obra.py`, `/buscar-videos`, com crédito. Confira o direito aplicável no seu país antes de usar.
     A cópia inteira fica em `material/obra/` só para estudo e **nunca é publicada**.
5. Máximo **5 hashtags**; palavra-chave principal na 1.ª linha da legenda do post.
6. CTA sempre de `00-marca/cta.md`. **Nunca prometer material que não exista** em `videos/<slug>/material/`.
   **Palavra-chave = sempre um PDF** (`scripts/gerar_material_pdf.py`), de no máximo 2 páginas. Só esse PDF vai para o
   pacote e para o bucket público — dossiê, `fontes.json` e obra nunca.
7. Afirmações de notícias precisam de fonte (link no roteiro).
8. Gravações de tela **não** recebem LUT. Cor só na imagem da câmera/celular, antes dos gráficos.
9. Não ler nem imprimir `.env`. Segredos só via variáveis de ambiente.
10. **Conferir o resultado no ponto do defeito, e pelo meio certo.** Compilar não prova que roda; `cmd | tail`
    esconde o erro; conferir "perto" do problema não conta. Antes de dizer que está corrigido, **olhe o quadro ou o
    número onde ele reclamou**.
11. **Gravação em várias partes** (a câmera divide em N arquivos): cor, preto e nível de voz variam ENTRE arquivos.
    Toda correção é **por fonte**, nunca global, e **corrige o mínimo**, com alvo na mediana dos arquivos bons
    (`scripts/cor_pele_casada.py`).
12. Antes de um tema novo, checar `_controle/tracker.md` e `_controle/temas-ja-feitos.md` (anti-repetição).
13. **GAUNTLET — quem faz não aprova** (`docs/gauntlet.md`). Cada departamento tem um **portão** que audita e não
    constrói: **PAUTA** `portao-pauta` · **ROTEIRO** `revisor-de-roteiro` · **IMAGEM** `portao-imagem` · **CORTE**
    `revisor-de-video` · **PUBLICACAO** `portao-publicacao` · painel: `portao-interface` + `portao-dados`. O portão
    roda sozinho quando o construtor termina; BLOQUEADO → o construtor corrige os S0/S1 e volta (até 3 voltas; na 3.ª,
    ESCALADO = decisão do autor). O veredicto fica preso aos arquivos (`scripts/portoes.py`): arquivo mudado depois do
    APROVADO vence o veredicto. `montar_pacote.py` e `publicar.py` recusam o que os portões não aprovaram.

## Contratos de dados
Formatos de `roteiro.json`, `transcricao.json`, `alinhamento.json`, `edl.json`, legendas, `reel-props.json`,
`status.json`, `pacote.json` e `post.json`: **`docs/contratos.md`** (fonte única — não inventar campos).

## Agentes, skills e comandos
- Agentes em `.claude/agents/` (29), comandos em `.claude/commands/` (20), skills próprias em `.claude/skills/` (10).
- Skills externas (Remotion, Supabase, `watch`, `apple-design`) **não estão copiadas**: instale pelo `skills-lock.json`.
- **Estrutura de todo vídeo:** vídeo principal (o autor falando) + cenas extras por cima em `split` / `full` / `card`
  (`docs/contratos.md` §0, medidas em `00-marca/layouts.md`).
- Comandos: /ideias · /material · /obra · /buscar-videos · /musica · /novo-video · /roteiro · /extras · /editar ·
  /renderizar · /cor · /criar-lut · /capa · /animar · /pacote · /publicar · /fila · /calibrar-voz · /multiplicar · /status.

## Ferramentas
- `FFMPEG_BIN` / `FFPROBE_BIN` vêm do `.env` (padrão: `ffmpeg`/`ffprobe` do PATH; recomendado um build com libass e zimg).
- Python: `uv run python <script>` (Python 3.12, `pyproject.toml` na raiz).
- Transcrição: ElevenLabs Scribe (`ELEVENLABS_API_KEY`); alternativa local `--engine mlx` (mlx-whisper, Apple Silicon).
- Remotion: `cd remotion && npx remotion studio` / `npx remotion render`.
- Contexto do estúdio: MCP `estudio-contexto` (só leitura; `.mcp.json`) — consulte antes de perguntar ao autor o que já
  foi decidido; cite a `fonte`; se divergir, **o arquivo vence o índice**.

## Antes de commitar
`python3 -I scripts/varrer_privacidade.py` — nenhum token, caminho pessoal, e-mail ou ID real. Dados do seu estúdio
(`videos/`, `_controle/`, `06-publicar/`…) ficam fora do git pelo `.gitignore`.

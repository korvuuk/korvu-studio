# Contratos de dados (formato único entre agentes, scripts e Remotion)

Todos os tempos em **segundos (float)** salvo indicação `Ms`. Caminhos relativos à pasta do vídeo `videos/<slug>/`, exceto quando indicado.

---

## 0. Estrutura de um vídeo — PRINCIPAL + CENAS EXTRAS

Todo Reel tem **sempre** duas camadas de material bruto:

| Camada | Pasta | O que é | Cor |
|---|---|---|---|
| **Principal** (A-roll) | `videos/<slug>/brutos/principal/` | o autor falando para a câmera: `camera-01.mov`, `camera-02.mov`… (+ `camera-00-cor.mov`, amostra de cor, ignorada na edição) | V-Log → LUT |
| **Cenas extras** (B-roll) | `videos/<slug>/brutos/extras/` | tudo que ilustra a fala, **nomeado pelo ID da cena**: `E01-chatgpt.mov`, `E02.png`, `E03-noticia.mp4`… | só tipo `camera` recebe LUT |
| Animações | `videos/<slug>/animacoes/<Exx>/` | brief + export do Claude Design de cada extra tipo `animacao` | nunca |

- **Animação capturada:** quando o export do Claude Design é grande demais para portar para Remotion, ele é capturado quadro a quadro (`scripts/capturar_animacao.mjs`, que usa o `window.seek(t)` do próprio export) e o vídeo resultante entra como mídia normal em `brutos/extras/<ID>.mp4` → `ingest.py` → `edicao/extras/<ID>.mp4`. O extra continua do tipo `animacao` (nunca recebe LUT) e o modo sai do formato do arquivo, como qualquer outro extra.

- A **voz é sempre a do vídeo principal**; os extras entram por cima dela (som do extra desligado, salvo `som: sim`).
- **Tipos de extra:** `tela` (gravação de ecrã) · `print` (captura de página/app) · `imagem` (imagem gerada ou fornecida) · `video` (vídeo de terceiros: demo oficial, notícia — **sempre com crédito**) · `animacao` (Claude Design → Remotion) · `camera` (plano de apoio gravado com a Lumix, V-Log).
- **Modos de entrada na tela — quem manda é o FORMATO do arquivo** (regra do autor, 2026-09-17):
  - mídia **deitada** (largura/altura ≥ 1,2 — "formato YouTube", 16:9) → `split`: **o extra ocupa a metade de cima e o autor a metade de baixo**;
  - mídia **em pé** (vertical) → `full`: ocupa a tela toda e o autor volta quando a cena sai;
  - `card` (extra num cartão sobre o autor) é escolha explícita e não é trocada pelo formato.
  O `modo` do roteiro é só uma sugestão: o `gerar_props.py` mede o arquivo e corrige (avisa quando troca). Medidas em `00-marca/layouts.md`.
- **Original arquivado fora do Mac — `brutos/principal/ARQUIVADO.json`** (limpeza de 23/10, `_controle/limpeza-2026-10-23.md`).
  Vídeo já publicado cujo original 4K foi copiado para um HD externo, conferido por SHA-256 e apagado do Mac. O arquivo
  fica no lugar dos `.MOV` e diz o que existia e onde está:
  ```json
  {"arquivado_em": "2026-10-23T23:10:00+01:00",
   "motivo": "vídeo publicado; original 4K fora do Mac (limpeza 23/10)",
   "destino": {"volume": "KORVU V01", "volume_uuid": "D4CCA486-…", "formato": "exFAT",
               "pasta": "Korvu Studio - originais 4K/<slug>/brutos/principal"},
   "conferencia": "sha256 da origem (lido na cópia) = sha256 relido do HD sem cache, arquivo por arquivo",
   "intermediarios": "edicao/fontes/ (1440×2560 10-bit 4:2:2 V-Log, duração igual à do original) + edicao/audio48k/",
   "arquivos": [{"nome": "PRAQ0978.MOV", "bytes": 4153821771, "sha256": "<64 hex>",
                 "mtime": "2024-08-14T12:05:00+00:00", "ctime": "2026-10-14T22:48:00+00:00"}]}
  ```
  `mtime` = data do próprio arquivo (relógio da câmera); `ctime` = quando ele entrou no disco do projeto — as mesmas
  duas datas que o painel mostra da gravação. **Quem lê:** o sincronizador do painel conta esses arquivos como gravação
  (o vídeo continua "gravado"); o `ingest.py` não reingere o principal e mantém as fontes do `fontes.json` como estão.
  **O HD é só cópia de segurança (Autor, 24/10):** nenhum script, agente ou o painel lê o HD — ele fica desligado/guardado.
  **Para reeditar em 4K:** copiar os `.MOV` do HD de volta para `brutos/principal/` (conferir o `sha256`) e apagar o
  `ARQUIVADO.json`. Para reeditar em 1080×1920 não é preciso: `edicao/fontes/` basta.
- **A troca é fluida**: a câmera desliza entre tela cheia e o painel de baixo (`LAYOUTS.split.transicaoFrames`, 10 frames), e o extra entra deslizando — nunca um corte seco.
- Extras que faltam **não travam a edição** e **nunca aparecem em vídeo nenhum** que vá para o autor (regra dele, 2026-09-17: "o vídeo não pode ter essas informações"): o extra que falta simplesmente não entra (`reel-props.json.mostrarFaltando: false`, padrão). A etiqueta "EXTRA Exx FALTANDO" só existe no `preview.mp4` de aprovação da EDL e nos relatórios em texto. O QA continua reprovando até o arquivo chegar — quem avisa o que falta é o relatório, não o vídeo.

## 0b. `material/obra.json` — a obra comentada (vídeo de comentário/reação)

Existe só quando o Reel **fala sobre** uma obra (documentário, palestra, demo, entrevista) e cita trechos dela.
Escrito por `scripts/baixar_obra.py` (agente `curador-de-obra`, comando `/obra`).

**Não confundir com B-roll.** B-roll ilustra outra coisa e precisa de licença de reuso (`fontes.json`,
`buscar_video.py`). Aqui o trecho **é** o objeto do comentário — citação para crítica (decisão do autor,
2026-09-18; condições em `docs/decisoes.md` §5).

```json
{
  "url": "https://www.youtube.com/watch?v=d95J8yzvjbQ",
  "titulo": "The Thinking Game | Full documentary | Tribeca Film Festival official selection",
  "autor": "Google DeepMind",
  "plataforma": "Youtube",
  "publicado_em": "2025-11-25",
  "duracao_s": 5047.174,
  "licenca_declarada": "não declarada (obra comercial)",
  "uso": "comentario",
  "credito": "The Thinking Game (Google DeepMind / Greg Kohs)",
  "arquivo": "videos/<slug>/material/obra/the-thinking-game.mp4",
  "proxy": "videos/<slug>/material/obra/the-thinking-game-VER.mp4",
  "baixado_em": "2026-09-18",
  "trechos": [
    {"id": "E02", "inicio_s": 750.0, "fim_s": 758.0, "duracao_s": 8.0,
     "inicio": "12:30", "fim": "12:38", "o_que": "Hassabis explica o AlphaFold",
     "som": false, "arquivo": "videos/<slug>/brutos/extras/E02-hassabis.mp4"}
  ]
}
```

| Campo | Regra |
|---|---|
| `autor` / `credito` | **obrigatórios.** O crédito aparece na tela no momento do trecho. Sem crédito o extra não entra no roteiro |
| `uso` | sempre `"comentario"`. É o que distingue este material de B-roll em `fontes.json` |
| `arquivo` | cópia **de estudo**, inteira, em `material/obra/`. **Nunca publicada**: não entra em `edicao/`, nem no pacote, nem em `05-render-pronto/` |
| `proxy` | cópia H.264/AAC para assistir, quando o original vem em VP9/Opus (o QuickTime do macOS não toca). Os cortes saem sempre do `arquivo`, não do proxy |
| `trechos[]` | o que **de facto** entra no Reel. Cada um vira `brutos/extras/<ID>-*.mp4` + uma linha em `fontes.json` com `uso: "comentario"` |
| Tetos | **12 s por trecho, 30 s no total** num Reel de 60 s (elevado de 20 s pelo autor em 19/09). `baixar_obra.py` recusa acima disso sem `--forcar`; o teto só muda por decisão escrita, que diz de onde veio o número |
| `som` | `false` por padrão — a voz é a do autor. `true` só quando a fala depende de ouvir a obra |

Daí para a frente o trecho é uma cena extra normal: `ingest.py` normaliza (1080 de largura, `FPS_PROJETO`),
o modo sai do formato do arquivo (deitado → `split`, em pé → `full`, §0).

## 1. `roteiro.md` → `roteiro.json` (gerado por `parse_roteiro.py`)

Template do `.md`: `.claude/skills/roteiro-reels/references/template-roteiro.md`.

Marcas permitidas na coluna FALA (removidas em `fala`, preservadas em `fala_original`):
- `**palavra**` → destaque (legenda sobe para nível "impacto"; candidata a rabisco)
- `[pausa]` / `[pausa longa]` → **só no fim da linha**

```json
{
  "slug": "2026-09-20-chatgpt-errado",
  "versao": 1,
  "tema": "Você tá pedindo errado pro ChatGPT",
  "pilar": "mitos-e-erros",
  "estrutura": "1-ruptura",
  "duracao_alvo": 60,
  "wps_ref": 2.3,
  "hook_escolhido": "A",
  "cta_tipo": "palavra-material",
  "cta_palavra": "PROMPT",
  "material": "Prompt mestre em PDF",
  "material_titulo": "o prompt mestre",
  "linhas": [
    {
      "id": "L01",
      "secao": "hook",
      "fala": "Você tá pedindo errado pro ChatGPT",
      "fala_original": "Você tá pedindo **errado** pro **ChatGPT** [pausa]",
      "palavras": ["você", "tá", "pedindo", "errado", "pro", "chatgpt"],
      "destaques": ["errado", "ChatGPT"],
      "pausa_depois": "pausa",
      "tela": "TEXTO: \"CHATGPT ERRADO?\" | ZOOM",
      "animacao": null,
      "alternativa_de": null,
      "tempo_estimado": [0.0, 2.6]
    }
  ]
}
```
- `secao` ∈ `hook | promessa | corpo | payoff | cta` (e `hook-alt`).
- `bloco` (desde 14/10, roteiro narrativo — `00-marca/modelo-roteiro-narrativo.md`): o nome escrito na coluna Seção, sem acento. Os blocos do arco são aceitos e mapeados para a `secao` canônica, que é o que capa/legendas/CTA leem: `gancho`→hook · `contexto`/`historia`/`desafio`/`virada`/`revolucao`→corpo · `climax`/`reflexao`→payoff · `cta`→cta · `gancho-alt`→hook-alt. Roteiro com seções antigas: `bloco` = `secao`.
- `pausa_depois` ∈ `normal | pausa | pausa_longa`.
- `animacao`: `null` ou `{"modo": "full|split|card", "descricao": "..."}` (vem de `ANIMACAO[modo]: ...` na coluna TELA).
- Hooks alternativos: `L01B`, `L01C` com `"alternativa_de": "L01"` (gravados para Trial Reels; fora da montagem principal).

- `cta_tipo` ∈ `palavra-material | envio | salvar | seguir` (`00-marca/cta.md`). Com `palavra-material`, os três
  campos seguintes são obrigatórios (o `parse_roteiro.py` recusa sem eles):
  `cta_palavra` (MAIÚSCULAS, sem acento, nunca KORVU/CORVO), `material` (o que o PDF entrega, uma frase) e
  `material_titulo` (com artigo — é o `{material}` do direct: "Aqui está **o prompt mestre** que você pediu").

### 1a. Material do CTA — sempre um PDF (decisão do autor, 13/10)
Todo vídeo com palavra-chave entrega **um PDF**, gerado pelo agente `produtor-de-material` a partir do roteiro,
sem o autor pedir. Arquivos em `videos/<slug>/material/`:

| Arquivo | O que é | Vai para o pacote / R2? |
|---|---|---|
| `_fonte/material.md` | conteúdo do PDF: Markdown + frontmatter `titulo`, `destaque`, `rotulo`, `palavra`, `arquivo`, `creditos` (formato no topo de `scripts/gerar_material_pdf.py`) | **não** |
| `_fonte/<arquivo>-previa.png` | 1.ª página, para conferir olhando | **não** |
| **`<arquivo>.pdf`** | o material (1–3 páginas, links clicáveis) | **sim — é o único** |
| `dossie.md`, `fontes.json`, `obra.json`, `obra*.md`, `obra/`, `youtube/` | estudo e pesquisa | **nunca** |

`<arquivo>` = nome em minúsculas com hífens (`prompt-mestre-atendimento`). Só pode haver **um** `.pdf` na raiz de
`material/`. O `publicar.py` sobe para o R2 **público** só o arquivo de `post.json → material.arquivo`;
por isso estudo, rascunho e cópia de obra nunca podem ser o material.

### 1b. Cenas extras no roteiro
Seção `## Cenas extras` do `roteiro.md`:

| ID | Tipo | O que mostrar | Como obter / fonte | Crédito | Som | Linhas |
|---|---|---|---|---|---|---|
| E01 | tela | ChatGPT: prompt fraco → resposta genérica | Autor grava o ecrã (Chat temporário, zoom 150%) | — | não | L03–L04 |
| E02 | animacao | 4 caixas Contexto → Público → Objetivo → Formato | Claude Design (brief do animador) | — | não | L08 |
| E03 | print | Manchete da notícia | print automático: https://… | TechCrunch | — | L02 |

Na coluna TELA de cada linha: `EXTRA: E01 split` · `EXTRA: E01 full 00:02–00:09` (trecho do próprio extra, opcional) · `EXTRA: E03 card`. Vários itens separados por ` · `. Compatibilidade: `tela-01 a–b modo` e `ANIMACAO[modo]: …` antigos continuam aceitos.

No `roteiro.json`:
```json
"extras": [
  {"id": "E01", "tipo": "tela", "descricao": "ChatGPT: prompt fraco → resposta genérica",
   "fonte": "o autor grava o ecrã", "credito": null, "som": false, "linhas": ["L03", "L04"]}
],
"linhas": [ {"id": "L03", "…": "…",
  "extras_ref": [{"id": "E01", "modo": "split", "in": 0.0, "out": 8.0}] } ]
```
`in`/`out` (segundos no tempo do próprio extra) são opcionais; um mesmo extra em linhas seguidas vira **um overlay contínuo**.

## 2. `edicao/transcricao.json` (normalizado, qualquer engine)
```json
{
  "engine": "scribe",
  "idioma": "pt",
  "fontes": {"camera-01": {"arquivo": "edicao/fontes/camera-01.mp4", "duracao": 312.4}},
  "palavras": [
    {"i": 0, "fonte": "camera-01", "texto": "Você", "inicio": 0.52, "fim": 0.80, "conf": 0.98,
     "locutor": "apresentador", "locutor_conf": 0.97, "locutor_bruto": "speaker_0"}
  ],
  "eventos": [
    {"fonte": "camera-01", "tipo": "respiracao", "inicio": 3.10, "fim": 3.45}
  ]
}
```
- `palavras` ordenadas por (fonte, inicio). `i` é global e sequencial.
- `eventos.tipo` ∈ `respiracao | riso | tosse | ruido | musica | outro`.
- **Locutor** (gravado pelo `locutores.py`, que roda entre o transcribe e o align — método ChatGPT-monitor: o ChatGPT
  Voice lê cada linha pelo alto-falante do celular e o autor repete para a câmera, as duas vozes no mesmo áudio):
  `locutor` ∈ `apresentador | ia | null` e `locutor_conf` (0–1). `null` = confiança < 0,75 (palavra ambígua, sobreposição
  ou evidências em conflito) → a linha que usar essa palavra vai para [REVISAR]; nunca se chuta. Sem o campo
  (transcrição antiga) = `apresentador`.
- `locutor_bruto` (opcional): `speaker_id` da diarização do Scribe (`diarize=True`, `num_speakers=2`).
- `borda_asr` (opcional): `[inicio, fim]` originais do ASR quando o `locutores.py` aparou uma palavra que o ASR esticou
  por cima da outra voz (ex.: 1.ª palavra do autor começando na cauda da leitura da IA).
- `mlx` re-transcreve sozinho cada trecho com fala e sem palavra (o Whisper "engole" a repetição idêntica de uma frase
  dita logo antes — a IA lê, o autor repete); o cache `edicao/raw/<fonte>.mlx.json` guarda `"lacunas": n`.

### 2b. `edicao/locutores.json` (gerado por `locutores.py`)
```json
{
  "versao": 1, "gerado_em": "2026-09-20T18:03:00+01:00", "fontes": ["camera-01"],
  "metodo": "local",
  "n_locutores": 2,
  "protocolo_ia_primeiro": false,
  "separacao": {"distancia": 10.3, "limiar": 3.0, "silhueta": 0.77, "fracao_minoria": 0.44, "enunciados": 23},
  "classes": {
    "A": {"papel": "ia", "graves_db": -19.9, "nivel_db": -43.3, "centroide_oct": -1.21, "rolloff_oct": 0.4, "pitch_st": 13.1},
    "B": {"papel": "apresentador", "graves_db": -1.4, "nivel_db": -19.7, "centroide_oct": -1.79, "rolloff_oct": -0.2, "pitch_st": 3.2}
  },
  "papel": {"ia": "A", "apresentador": "B", "confianca": 0.94, "conflito": [],
            "evidencias": [{"nome": "assinatura", "valor": -1.0, "peso": 2.0, "aponta_ia": "A",
                            "detalhe": "classe B tem -18.7 dB de graves e -23.7 dB de nível a menos que A"}]},
  "segmentos": [{"fonte": "camera-01", "inicio": 0.92, "fim": 3.9, "locutor": "ia", "classe": "A", "conf": 0.94,
                 "tipo": "leitura", "linha": "L01", "cobertura": 1.0, "monitor": [], "i_ini": 0, "i_fim": 7,
                 "texto": "Você tá pedindo errado pro chat GPT.", "graves_db": -21.0, "nivel_db": -43.0,
                 "pitch_hz": 212.0}],
  "zonas_ia": {"camera-01": [[0.816, 4.086], [8.566, 13.406]]},
  "sobreposicoes": [{"fonte": "camera-01", "tipo": "ia_depois_do_apresentador", "inicio": 58.2, "fim": 58.22, "gap": 0.02,
                     "apresentador_i": 120, "ia_i": 121, "texto": "muito. | Perfeito."}],
  "incertos": [{"fonte": "camera-01", "i": 57, "texto": "O", "inicio": 23.2, "conf": 0.6}],
  "estatisticas": {"segundos_ia": 45.7, "segundos_apresentador": 28.6, "segundos_incerto": 0.0, "segundos_zonas_ia": 50.0,
                   "palavras_ia": 116, "palavras_apresentador": 83, "palavras_incertas": 0, "sobreposicoes": 1},
  "bordas_ajustadas": 2,
  "modelo": {"dims": ["graves_db", "centroide_oct", "pitch_st"], "limiar_llr": 3.0, "min_quadros": 5,
             "ia": {"media": [-24.1, -1.1, 12.9], "desvio": [4.0, 0.3, 2.1], "quadros": 2100},
             "apresentador": {"media": [-1.0, -1.8, 3.0], "desvio": [3.1, 0.3, 1.5], "quadros": 1500}}
}
```
- `metodo` ∈ `scribe | local` (`scribe` = diarização do Scribe confirmada palavra a palavra pela acústica local;
  `local` = só a acústica: graves < 250 Hz, nível, centróide/rolloff, pitch → k-means de 2 classes + HMM por palavra).
- `n_locutores: 1` = gravação sem IA (separação acústica < `limiar`): tudo `apresentador`, `zonas_ia` vazias, `modelo: null`.
- `papel.evidencias[].nome` ∈ `assinatura` (celular: menos graves e menos nível) `| ordem` (a 1.ª leitura de uma linha é
  seguida pela repetição do outro locutor) `| monitor` ("de novo", "repete", "próxima", "faltou"…) `| inscricao`
  (`00-marca/voz-autor.json` → `"perfil_locutor": {"pitch_hz", "centroide_hz", "graves_db"}` ou o 1.º áudio de
  `02-calibracao/amostras/`). `valor` > 0 aponta a classe B como IA; `conflito` = evidências que discordam do resultado.
- `segmentos[].tipo` ∈ `leitura | monitor` (IA) `| take | fala` (Autor); `locutor` pode ser `misto` (segmento com
  palavras de confiança diferente).
- `zonas_ia` = fala da IA **+ cauda da reverb** (+ voz de IA sem palavra transcrita): **proibidas** para pontos de corte.
- `sobreposicoes[].tipo` ∈ `ia_depois_do_apresentador | apresentador_depois_da_ia` — vozes diferentes a < 0,10 s ou sem silêncio
  entre si; o take do autor que tem `apresentador_i` recebe a flag `sobreposicao_ia`.
- `modelo` = gaussianas por quadro vozeado (sem nível, invariante a ganho) usadas pelo `verify.py` para medir voz de IA
  residual no corte.

## 3. `edicao/alinhamento.json` (gerado por `align.py`)
```json
{
  "linhas": [
    {
      "id": "L03",
      "status": "ok",
      "escolhido": "L03-T3",
      "motivo": "último take limpo (sim 0.96)",
      "takes": [
        {"take_id": "L03-T1", "fonte": "camera-01", "i_ini": 40, "i_fim": 52,
         "inicio": 12.30, "fim": 15.10, "sim": 0.72, "cobertura": 0.90,
         "flags": ["recomeco"], "score": 0.61, "texto": "..."}
      ],
      "leituras_ia": [{"fonte": "camera-01", "inicio": 9.10, "fim": 11.80, "sim": 1.0, "texto": "..."}]
    }
  ],
  "nao_mapeado": [{"fonte": "camera-01", "inicio": 40.1, "fim": 42.0, "texto": "..."}],
  "separadores": [{"fonte": "camera-01", "inicio": 67.7, "fim": 68.3, "texto": "de novo."}],
  "fala_ia": [{"fonte": "camera-01", "inicio": 27.6, "fim": 29.9, "texto": "De novo, faltou a palavra contexto. Repete,",
               "i_ini": 60, "i_fim": 66}],
  "locutores": {"metodo": "local", "n_locutores": 2, "confianca_papel": 0.94, "sobreposicoes": 1, "segundos_ia": 45.7},
  "resumo": {"ok": 7, "revisar": 1, "parafrase": 0, "faltando": 1, "nao_mapeado": 0,
             "leituras_ia": 9, "fala_ia": 6, "palavras_locutor_incerto": 0}
}
```
- `status` ∈ `ok | revisar | parafrase | faltando`.
- `flags` ∈ `false_start | recomeco | muleta | pausa_interna | final_cortado | baixa_confianca | sobreposicao_ia |
  fala_ia_interna | locutor_incerto`.
- **Takes só com palavras `locutor: apresentador`** (e `null`, que marca `locutor_incerto` → status `revisar`). Palavras da IA
  dividem blocos como um separador e **nunca** viram take.
- `leituras_ia` = leituras da linha pela IA (sim ≥ 0,60; para depuração — nunca entram no corte). Linha que só a IA leu
  fica `faltando` ("a IA leu a linha (1×), mas não há take do autor").
- `fala_ia` = o resto da fala da IA (monitor: "de novo", "repete", "próxima", "faltou a palavra X"…) — não vai para
  `nao_mapeado`. `separadores` = só os ditos pelo autor ("de novo", "corta"…).
- `sobreposicao_ia` (impede take limpo): a IA fala colada/por cima do take (`locutores.json.sobreposicoes` ou zona da
  IA encostando numa palavra do take) → escolhe outro take limpo; sem alternativa, `revisar`. `fala_ia_interna`
  (não impede): a IA fala dentro de um silêncio entre duas palavras do take → a EDL corta.
- `locutores` = resumo do `locutores.json` (`null` se não existir).

## 4. `edicao/edl.json` (gerado por `edl.py`; editável; `edl.md` é a versão legível)
```json
{
  "versao": 1,
  "slug": "2026-09-20-chatgpt-errado",
  "fps": 25, "sr": 48000, "largura": 1080, "altura": 1920,
  "aprovado": false, "aprovado_em": null,
  "fontes": {"camera-01": "edicao/fontes/camera-01.mp4", "tela-01": "edicao/fontes/tela-01.mp4"},
  "zoom_no_corte": true,
  "segmentos": [
    {"n": 1, "linha": "L01", "take": "L01-T2", "fonte": "camera-01",
     "in": 12.32, "out": 15.04, "cortes_internos": [[13.12, 13.60]],
     "saida_inicio": 0.0, "saida_fim": 2.24, "layout": "full", "zoom": {"tipo": "punch", "escala": 1.12},
     "zoom_origem": "43.1% 35.9%", "zoom_pecas": [1.12, 1.0], "voz_ia": 0.0}
  ],
  "overlays": [
    {"linhas": ["L03", "L04"], "tipo": "extra", "extra": "E01", "extra_tipo": "tela",
     "arquivo": "edicao/extras/E01.mp4", "modo": "split", "in": 0.0, "out": 8.0, "som": false,
     "credito": null, "faltando": false, "saida_inicio": 7.9, "saida_fim": 15.2},
    {"linhas": ["L08"], "tipo": "extra", "extra": "E02", "extra_tipo": "animacao", "componente": "<slug>/E02",
     "modo": "split", "faltando": false, "saida_inicio": 38.2, "saida_fim": 43.9},
    {"linhas": ["L02"], "tipo": "extra", "extra": "E03", "extra_tipo": "print",
     "arquivo": "edicao/extras/E03.png", "modo": "card", "credito": "TechCrunch", "faltando": true,
     "saida_inicio": 3.8, "saida_fim": 7.9},
    {"linha": "L01", "tipo": "texto", "texto": "CHATGPT ERRADO?", "saida_inicio": 0.0, "saida_fim": 2.1}
  ],
  "palavras_saida": [
    {"texto": "Você", "inicio": 0.05, "fim": 0.30, "linha": "L01", "destaque": false}
  ],
  "duracao_saida": 58.70,
  "audio": {"loudnorm_lufs": -14, "true_peak": -1.5, "musica": null, "ducking": true}
}
```
Regras:
- `in`/`out` em tempo da fonte. **A pausa depois da linha já está incluída no `out`** (silêncio real do take, nunca frame congelado). `cortes_internos` são intervalos removidos dentro de [in, out].
- `saida_inicio/fim` = posição na timeline final (calculada; não editar à mão — rodar `edl.py --recalcular`).
- `palavras_saida` = **as palavras do roteiro**, não as da transcrição (regra do autor, 2026-09-16: ele come sílabas e
  o ASR escreveu "pronto" onde o roteiro diz "PROMPT"). A linha inteira sai na ordem do roteiro; o tempo vem da fala
  (a união das palavras do ASR casadas com cada palavra do roteiro) e as palavras que ele comeu recebem tempo
  **interpolado** entre as vizinhas casadas (mínimo 0,06 s). O que o ASR ouviu a mais é descartado.
  **Exceção — improviso de verdade** (2026-09-17): só quando a linha é `parafrase` **e** o take escolhido tem
  `sim < 0,55` — aí ele reescreveu a frase e a legenda segue a **fala**, senão contradiria o que se ouve.
  **Atenção:** o status `parafrase` sozinho **não** serve como critério — ele cobre tudo abaixo de 0,80, e as
  linhas do autor caem nessa faixa só por ele comer o fim das palavras (1.º vídeo real: L01 sim 0,64, L02 0,78,
  L06 0,75 — todas ditas como no roteiro). Usar o status fez a legenda da L01 virar "Para depender post parou".
  Se **nada** da linha casou, sai o texto do ASR.
  **`segmentos[].legenda_texto`** (opcional, 26/10 — Jensen): o editor escreve o que o autor **disse** na linha, em
  grafia limpa ("Denny's", "uma IA", "5"). Vence as duas regras acima: as palavras da legenda são esse texto, e os
  tempos vêm das palavras faladas que sobraram no corte (igual → o tempo dela; trecho trocado → o vão dividido por
  igual; palavra só da legenda → interpolada). Usar quando ele reescreveu a linha (outra ordem, outra palavra, aparte
  cortado) e o take ficou com `sim ≥ 0,55`, ou seja, a legenda pelo roteiro mostraria palavras que não se ouvem.
  Sobrevive ao `--recalcular` e à troca de take (aí reescreva-o). Sem o campo, nada muda.
  Base das legendas e das animações.
- **Enquadramento (zoom) — aplicado UMA vez, no corte.** Técnica de talking head: a cada corte entre peças da mesma
  câmera (troca de segmento **e** corte interno) o enquadramento alterna 1.00 ↔ 1.12, com a origem no rosto; nunca
  duas peças seguidas com o mesmo enquadramento (as trocas só acontecem nos cortes, que ficam no silêncio — nunca no
  meio de uma palavra). Campos:
  - `zoom_pecas`: uma escala por peça do segmento (peças = [in, out] − `cortes_internos`, na ordem), 1.0–1.33
    (1.33 = 1440/1080: acima disso ampliaria o intermediário). Plano automático do `edl.py` (alternância na timeline
    inteira); editável — valor diferente do automático anterior (`edl.auto.json`) é preservado no `--recalcular` e o
    resto do plano se adapta em volta. Tamanho errado (mudou `cortes_internos`) → volta ao automático (aviso).
  - `zoom_origem`: `"x% y%"` = ponto fixo do punch-in (semântica do CSS `transform-origin`: o rosto fica parado e
    cresce; o recorte nunca sai do quadro). Automático = centro do rosto (OpenCV Haar frontal em 3–5 quadros do
    segmento, mediana, limitado a x 30–70 % / y 25–55 %); sem rosto → `"50% 38%"`. Editável. `null` em tela.
  - `zoom`: `null` ou `{"tipo": "punch", "escala": 1.12}` (coluna TELA `ZOOM [1.2]` ou à mão) = escala do punch do
    segmento **e** o segmento começa fechado (1.ª peça = escala; ex.: hook).
  - `zoom_no_corte: true` (raiz): o `render_corte.py` aplica `zoom_pecas`/`zoom_origem` (crop do intermediário
    1440×2560 + lanczos 10-bit → 1080×1920) e o `gerar_props.py`/Reel **não** aplicam o zoom dos segmentos
    (`reel-props.json` → `zoomNoCorte: true`, `segmentos[].zoom: null`; título/animações continuam). EDL antiga sem o
    campo: o corte sai sem zoom e o Remotion aplica o `zoom` do segmento, como antes.
- Pontos de corte: `in` = 1.ª palavra − 0,15 s, `out` = última palavra + max(0,18 s, pausa do roteiro), no ponto mais
  silencioso, **nunca dentro da energia de uma palavra** (ataque suave/cauda + 0,04 s, nem da vizinha) e já na grade
  de frames (arredondados "para fora"); detalhes em `.claude/skills/corte-por-roteiro/references/algoritmo.md` §7.
- `layout` ∈ `full | split` (split = câmera em cima, tela/animação embaixo).
- **Overlays `tipo: extra`**: `arquivo` aponta para a versão ingerida em `edicao/extras/` (vídeos → `<ID>.mp4` 1080 de largura, 25 fps; imagens → `<ID>.png`; tipo `camera` → `<ID>-cor.mp4` depois do colorista). Imagens ganham movimento lento (Ken Burns) no Remotion. `credito` aparece discreto na tela e vai para a legenda do post. `faltando: true` → placeholder visível + QA FAIL.
- `fontes.json` ganha `"extras": {"E01": {"arquivo_bruto": "brutos/extras/E01-chatgpt.mov", "arquivo": "edicao/extras/E01.mp4", "tipo": "tela", "perfil": "sdr", "duracao": 42.1, "fps": 25, "avisos": []}}`.
- **`enquadrar` (opcional, só `modo: "full"`; Hinton v2, 15/10)**: `{"x": 0.5, "y": 0.5, "zoom": 1.0, "xFim": …, "yFim": …,
  "kenBurns": 1.10, "area": {"x", "y", "largura", "altura"}}`. A mídia (foto OU vídeo, deitada ou em pé) **preenche**
  1080×1920 (cover da `area`, px da fonte; padrão = fonte inteira) — sem caixa, sem `FundoGrade`, sem blur; `x/y` = foco
  (fração da área) no centro do quadro; `zoom` inicial ≥ 1; Ken Burns em tudo (1,00 → `kenBurns`, padrão
  `LAYOUTS.enquadrado.kenBurns`); pan se houver `xFim/yFim`. A janela fica presa dentro da `area` (é assim que saem
  barras pretas, legenda queimada, tarja de TV e logo de canto). Entrada/saída em **corte seco**; degradê leve atrás da
  legenda e do crédito ("Fonte: …" no topo da zona segura). Sem `enquadrar`, `full` continua como antes. O `gerar_props.py`
  não troca o modo de um overlay com `enquadrar` pela regra do formato.
- **`modo: "pilha"` (Fei-Fei v2, 17/10 — pedido do autor: "empilhar em camada, uma no topo, uma no meio, uma embaixo")**:
  `"pilha": [{"id", "arquivo", "extra_tipo", "in", "out", "enquadrar", "credito"}, …]` com 2–3 faixas; cada faixa é uma janela
  1080×(1920/n) (fresta `LAYOUTS.pilha.vao`) com o mesmo `enquadrar` do `full` (cover da `area`, foco, zoom, pan, Ken Burns).
  Imagem deitada aparece quase inteira (faixa ≈ 1,69:1). Corte seco; crédito único no topo = os créditos das faixas unidos por
  " · ". O `arquivo` do overlay é o da 1.ª faixa (só para o contrato); `gerar_props.py` resolve `src`/dimensões de cada faixa.
- **`modo: "solo"` (Fei-Fei v3, 17/10)**: a mídia deitada INTEIRA (contain) sozinha, legenda embaixo; `enquadrar.area`
  recorta a fonte; Ken Burns `LAYOUTS.solo.kenBurns` (a caixa cresce de verdade, por layout, nunca via `transform`
  — um `scale()` sobre a caixa já no tamanho máximo passa da composição e corta a borda da mídia). **27/10
  (Autor, achado no Jensen)**: nunca mais sobre preto liso — o espaço que sobra fica sobre o fundo de marca
  `FUNDO_MARCA.isometrico` (`00-marca/assets/fundos/grade-isometrica-escura.png`) com a `MOLDURA_ISOLADA` (borda
  fina) ao redor da mídia (`solo` sempre; `full` sem `enquadrar` quando a mídia não cobre, `h/w <
  LAYOUTS.full.proporcaoCobre`). A caixa centraliza **dentro da área útil** (`AREA_SEGURA.y`=270 até
  `AREA_SEGURA.limiteY − LAYOUTS.solo.legendaReservada`), nunca na tela inteira — reserva espaço pra legenda
  ficar sempre ABAIXO da caixa, nunca sobre a mídia (2 voltas no mesmo dia: 1.ª enviesado pro topo, 2.ª
  centralizar na tela toda estourava a zona segura de baixo) — ver `00-marca/layouts.md` § "Imagem/vídeo
  retangular isolado".
- **`denso: true` (overlay `extra`, 27/10 — achado no E23 "Serial×Parallel")**: o extra tem texto/número/diagrama
  denso na tela (print de slide, infográfico, tabela) — informação que a legenda não pode cobrir. A legenda **some
  por completo** enquanto este overlay está ativo (mesmo mecanismo do `cartela`/CTA/card: a janela entra no
  `ocultar` de `legendasVisiveis`) — testado com o próprio E23: reposicionar não bastou, porque o `enquadrar`
  (cover) desse extra preenche o quadro de ponta a ponta e o diagrama tem rótulos espalhados por toda a altura,
  sem faixa livre sobrando. "Segurar a legenda até o extra sair" (`00-marca/layouts.md`) é a opção que garante
  nunca sobrepor. Quem decide marcar `denso` é quem monta os overlays (`produtor-de-extras`/`montar_v2.py`),
  olhando o frame.
- **`legendaTopo: true` (overlay `extra`, 27/10 — achado no V20/E13, fecho emocional do Jensen)**: diferente do
  `denso`, a mídia **não** tem texto próprio — mas o enquadramento necessário (close de rosto) deixa a boca na
  faixa normal da legenda (y≈1150), e apertar o corte pra fugir dela deforma a imagem (zoom alto demais, corta
  testa/cabeça). Com `legendaTopo: true` a legenda sobe pra `LEGENDA.centroYTopo` (logo abaixo da zona segura de
  cima) enquanto o overlay está ativo, em vez de ficar embaixo brigando com o rosto. Vale pra `full` e `pilha`
  (a faixa inteira, mesmo que só uma das faixas tenha o problema). Quem decide marcar `legendaTopo` é quem monta
  os overlays, olhando o frame — ver `00-marca/layouts.md` § full "legendas por cima, se a mídia não tiver texto".
  **O véu escuro troca de lado junto** (achado do portão-imagem, mesmo dia): `full`/`pilha` desenham `veuBaixo`
  atrás da legenda normal; com `legendaTopo: true` isso escureceria o rosto à toa (sem legenda ali pra
  justificar) — o motor troca por `veuTopo` (atrás da legenda que subiu) automaticamente.
- **Padrão 19/10 (Autor)**: `credito` continua no JSON (o publicador o leva para a DESCRIÇÃO do post), mas **não é
  desenhado** (`LAYOUTS.credito.mostrar: false`). **Toda imagem em movimento**: Ken Burns em `full`/`pilha` (1,00 → 1,10),
  `solo` (1,08), faixas da pilha inclusive; imagem com detalhe ganha `zoom`/`xFim,yFim` para revelar o detalhe. Nada estático.
- **`gerar_props.py --overlays <json>`**: `{"overlays": [...]}` (formato acima, caminhos relativos à pasta do vídeo, mídia
  dentro de `edicao/`) **substitui** os overlays `extra` da EDL — refaz a camada de extras sem tocar em `edl.json`,
  corte, legendas ou CTA. Ex.: `videos/2026-10-20-geoffrey-hinton/edicao/extras-v2/overlays.json` (gerado por `montar_v2.py`).
- Overlays `extra` também trazem `descricao` (da tabela do roteiro). Animações: `componente` = **`<slug>/Exx`** (chave no `remotion/src/animacoes/registry.ts`).
- Render final **bloqueado** enquanto `aprovado != true`.
- **Voz da IA (método ChatGPT-monitor):** as `zonas_ia` do `locutores.json` são proibidas — `in` fica ≥ fim da zona
  anterior + 0,08 s e o `out` (com a pausa) ≤ início da próxima zona − 0,08 s (a margem cobre a quantização em frames e
  a alça de 15 ms do áudio; se a IA começa a falar, a pausa encolhe). Zona dentro de um silêncio do take →
  `cortes_internos`. `voz_ia` = segundos de zona da IA dentro das peças do segmento (com a alça) — **tem que ser 0**;
  > 0 só por edição manual ou take com `sobreposicao_ia` sem alternativa (⚠ no `edl.md`). `palavras_saida` nunca tem
  palavra da IA. O `edl.md` mostra por linha **IA · o autor** (leituras da IA · takes do autor) e a fala da IA fora do corte.
- `verify.py` mede a voz de IA residual no corte (modelo por quadro do `locutores.json`) → `qa/verificacao.json`
  `"voz_ia": {"aplicavel", "segundos", "segundos_edl", "trechos", "palavras_ia", "limite": 0.2}` + linha no `qa/diff.md`;
  **> 0,2 s reprova** — `segundos` (acústica: só pega vazamento ≳ 0,5 s e conta ~metade) **ou** `segundos_edl`
  (peças da EDL ± alça dentro das `zonas_ia`: pega vazamento curto e cauda da reverb).

## 4c. `edicao/resolve/<slug>.fcpxml` — timeline do DaVinci Resolve (10/11)
Gerado **sozinho** pelo `edl.py` a cada EDL (e à mão por `resolve.py exportar videos/<slug>`). FCPXML 1.10, 1080×1920 a 25 fps.
- **V1** = uma peça por trecho de fala (`[in, out]` − `cortes_internos`), apontando para a **mídia de edição**
  `edicao/resolve/midia/<fonte>.mp4` (1080×1920 H.264 8-bit 4:2:0, mesmos quadros da fonte, LUT de entrada só para VER,
  som do wav48k) — o Resolve GRÁTIS não abre o H.264 10-bit 4:2:2 de `edicao/fontes/` ("File not found", 21.2, 10/11);
  `--sem-midia` aponta direto para as fontes (Studio). Gerada em 2.º plano pelo `edl.py` (~9 min na 1.ª vez) — o resto do arquivo fica como alça para esticar o corte. Zoom da peça =
  `adjust-transform` (escala relativa ao "fit" + posição em % da altura, mesmo recorte do `janela_zoom`). Nome do
  clipe `L05 · L05-T2 · p1`; marcador na 1.ª peça de cada linha.
- **V2** = cenas extras com arquivo (`split` em cima 1080×608, `full` cover, `card` 1000 px); extra sem arquivo e
  `texto` viram marcador. **A2** = música escolhida (`musica/musica.json`) com o volume sugerido.
- **Não leva** legendas, títulos, animações Remotion nem cor (LUTs em `/Library/.../LUT/Korvu/` só para VER: `resolve.py luts`).
- **Volta**: o autor exporta do Resolve (File › Export › Timeline › FCPXML) para `edicao/resolve/` com outro nome →
  `resolve.py importar videos/<slug> [arquivo] [--simular]`: cada peça da V1 volta ao segmento de onde veio (maior
  sobreposição na mesma fonte), `in/out/cortes_internos` e `zoom_pecas` (escala) refeitos; diferença ≤ ½ quadro =
  valor antigo; peça nova = segmento `manual` da linha vizinha; segmento sem peça = removido. Cópia em
  `edl.antes-resolve.json`, depois `edl.py --recalcular`. Extra arrastado no Resolve só gera AVISO (extras seguem as linhas).

## 5. Arquivos de mídia intermediários
| Arquivo | Especificação |
|---|---|
| `edicao/fontes.json` | por fonte: tipo (`camera|celular|tela`), `perfil` (`vlog` para câmera, `sdr`), fps original, duração, `wav48k`, `audio` (`faixa` usada, `cadeia`, `limpar_ruido`, níveis de cada `faixas[]`), `codec` |
| `edicao/fontes/<fonte>.mp4` | **1440×2560 supersampled** (o punch-in do corte recorta daqui e ainda reduz para 1080×1920; tela cabe inteira com `pad`), **25 fps CFR** (`FPS_PROJETO`), **H.264 High 4:2:2 10-bit** (`yuv422p10le`, decodificado inteiro na ingestão; se sair ilegível → HEVC main422-10), câmera **ainda em V-Log** (full → limitado), AAC mono (só para tocar — o corte usa o WAV) |
| `edicao/audio48k/<fonte>.wav` | **master de áudio sem perdas**: 48 kHz **24-bit mono** da faixa a:0 da câmera (`--faixa-audio N`; a:0 muda → a de melhor SNR), só passa-altas 60 Hz 12 dB/oit. — sem redução de ruído (`--limpar-ruido` = afftdn suave, opt-in) |
| `edicao/audio16k/<fonte>.wav` | mono 16 kHz para transcrição/análise (derivado do master) |
| `edicao/corte.mp4` | resultado do corte (1080×1920, 25 fps, H.264 High 4:2:2 **10-bit**, ainda em V-Log, **zoom por peça já aplicado**, AAC 256k = voz mono nos 2 canais) |
| `edicao/corte-audio.wav` | áudio do corte **sem perdas** (48 kHz 24-bit mono; mesmas peças, alças de 15 ms e crossfades de 30 ms do vídeo) — o `audio.py` masteriza a partir dele (o AAC final é o único encode com perdas) |
| `edicao/preview.mp4` | 540×960 8-bit com LUT de entrada **só para visualizar** (aprovação da EDL), mesmo plano de zoom do corte |
| `edicao/cor/corte-cor.mp4` | V-Log → Rec.709 (`entrada-camera.cube`) + primária + LUT criativo (+ grão) — só câmera/celular; saída 8-bit 4:2:0 bt709, 25 fps |
| `edicao/extras/<ID>.mp4` / `.png` | cenas extras ingeridas (vídeo 1080 de largura, 25 fps; tipo `camera` fica 10-bit V-Log) · `<ID>-cor.mp4` = extra `camera` com a cor da marca |
| `edicao/remotion/` | cópias 8-bit que o `gerar_props.py` cria quando a mídia é 10-bit (o Remotion não lê 10-bit): corte sem cor, extras `camera` sem cor |
| `edicao/reel-props.json` | props para a composição Remotion `Reel` |
| `edicao/render-remotion.mp4` | saída do Remotion (antes do loudnorm) |
| `edicao/final.mp4` | vídeo final: vídeo do render-remotion + áudio do `corte-audio.wav` masterizado pelo `audio.py` (nivelador leve 1,5:1 → ganho linear −14 LUFS → limitador de true peak 4× −1,5 dBTP → AAC 256k; sem EQ) |
| `edicao/final-L01B.mp4` … | variantes com hook alternativo (Trial Reels) |
| `qa/relatorio.md` | 1.ª linha `RESULTADO: PASS` ou `RESULTADO: FAIL` (lida pelo `montar_pacote.py`) |

## 6. `edicao/legendas.json` + `legendas.srt`
Formato `Caption` do `@remotion/captions` + extras:
```json
[{"text": " Você", "startMs": 50, "endMs": 300, "timestampMs": 175, "confidence": 1,
  "linha": "L01", "destaque": false}]
```
- `text` vem de `palavras_saida` (= o roteiro) e passa pelo `limpar_legenda()` do `gerar_props.py`: **sem pontuação nem
  caracteres especiais** na tela (`" " , . ( ) ? ! : ;` …) — pedido do autor, 2026-09-16. Hífen dentro da palavra fica
  (pré-pago); hífen solto vira espaço. Palavra que fica vazia depois da limpeza é descartada. O `legendas.srt` (arquivo
  de acessibilidade do pacote) segue o mesmo texto. A mesma limpeza vale para **tudo o que aparece escrito na tela**:
  o `titulo` (contexto, impacto, seleção, rabisco — derivado ou vindo de `titulo.json`) e os overlays `tipo: texto`
  da coluna TELA.

## 7. `edicao/reel-props.json` (entrada da composição Remotion `Reel`)
```json
{
  "video": "_render/<slug>/cor/corte-cor.mp4",
  "duracaoSeg": 58.7,
  "legendas": [/* seção 6 */],
  "overlays": [/* edl.overlays com caminhos de mídia relativos a remotion/public */],
  "segmentos": [{"saidaInicio": 0, "saidaFim": 2.18, "zoom": null, "layout": "full"}],
  "zoomNoCorte": true,
  "titulo": {"contexto": "Se você usa o ChatGPT assim,", "impacto": "tá jogando tempo fora.", "cinza": 3, "rabisco": "fora"},
  "cta": {"palavra": "NOBEL", "inicio": 53.72, "fim": 56.66, "topo": "comenta", "rodape": "que eu te mando o link oficial", "linha": "L18"},
  "estiloLegenda": "selecao"
}
```
`cta` (14/10, cartão "comenta" + PALAVRA gigante — `remotion/src/components/CtaPalavra.tsx`): `null` sem `cta_palavra`
ou com a linha do CTA fora do corte. `palavra` = `roteiro.json.cta_palavra`; `inicio` = `startMs` da palavra "comenta"
dita na linha de seção `cta` que contém a palavra (legendas §6); `fim` = fim dessa linha + 0,5 s, sem passar do início
da próxima palavra nem da duração; `rodape` = o resto da fala depois da palavra até a 1.ª pontuação (2–7 palavras,
senão "que eu te mando no direct"). As legendas inteiras dentro de [inicio, fim] somem no Reel. `edicao/cta.json`
(opcional) sobrescreve campos; `{"ativo": false}` tira o cartão.
`formato` (opcional, 08/11): `"faixa"` = uma linha só e baixa ("comenta" · palavra · rodapé, ~120 px, base y 1236),
para o take em que o queixo desce abaixo de y≈1000 e o cartão grande (~350 px) cobriria a boca. Padrão `"cartao"`.
Vem de `edicao/cta.json`.
Mídias são expostas ao Remotion via symlink `remotion/public/_render/<slug>/ → videos/<slug>/edicao/`.
`zoomNoCorte: true` (de `edl.json.zoom_no_corte`) = o zoom já está no vídeo → `segmentos[].zoom` vem `null` e o Reel
não aplica punch-in. EDL antiga: `zoom` do segmento (+ `origem` = `zoom_origem`, se houver) aplicado pelo Reel.

## 8. `status.json`
```json
{"slug": "...", "estado": "edicao", "atualizado": "2026-09-20T18:03:00+01:00",
 "historico": [{"estado": "roteiro", "em": "..."}]}
```

## 9. `05-render-pronto/<slug>/pacote.json`
```json
{
  "slug": "...", "criado_em": "...", "duracao": 58.7, "qa": "PASS",
  "arquivos": {
    "video": "video/video-final.mp4",
    "variantes": ["video/video-final-L01B.mp4"],
    "capa": "capa/capa.png",
    "legendas": "legendas/legendas.srt",
    "material": "material/guia.pdf",
    "roteiro": "roteiro.md",
    "qa": "qa-relatorio.md"
  },
  "cta_palavra": "PROMPT",
  "material_titulo": "o guia do prompt",
  "tema": "...", "pilar": "..."
}
```
`material` pode ser `null` só se o CTA não prometer material; com `cta_palavra` é **o PDF** (§1a), o único arquivo de
`material/` que o `montar_pacote.py` copia. `material_titulo` vem do `roteiro.json` e é passado pelo `publicador` para
`post.json → material.titulo`, como o material é chamado no direct ("Aqui está **o guia do prompt** que você pediu");
sem ele, "o material".
Depois de publicar, `07-publicados/<slug>/dm-material.json` = `{"palavra", "media_id_instagram", "material_url"}` —
é o que o `scripts/responder_comentarios.py` lê. No carrossel (09/11) vem também `"formato": "carrossel"`, e o direct usa
`mensagem_direct_carrossel` do `automacao-meta/respostas.yaml` ("no post" em vez de "no vídeo"/"no Reel").

**Selo GAUNTLET** (22/10, `docs/gauntlet.md`) — escrito pelo `montar_pacote.py` (`portoes.selar`), só com os portões
aprovados; o `publicar.py` recusa pacote sem ele (exceto a lista congelada `_controle/gauntlet-legado.json`):
```json
"gauntlet": {
  "versao": 1, "origem": "videos/<slug>", "selado_em": "2026-10-30T18:00:00+00:00",
  "veredictos": {"roteiro": {"impressao": "3f1a9c2b77e0", "em": "…"}, "imagem": {…}, "corte": {…}, "pauta": {…}},
  "arquivos": {"video/video-final.mp4": "<sha256>", "capa/capa.png": "<sha256>", "material/guia.pdf": "<sha256>",
               "legendas/legendas.srt": "<sha256>"}
}
```
Na hora de publicar, cada arquivo do pacote (vídeo, variantes, capa — também a `post.instagram.capa` —, material,
legendas, slides) tem de ser um dos que o portão da origem aprova **naquele momento** (vídeo/legendas → corte, capa e
slides → imagem, material → roteiro); a origem tem de continuar válida.

`formato` (09/11): **ausente = `"reel"`** (todos os pacotes anteriores). `"carrossel"` → §9c. É o único campo que diz
ao `publicar.py` o que publicar; o `post.json` repete o mesmo valor (§10).

### 9c. Pacote de CARROSSEL (09/11) — `05-render-pronto/<slug>/pacote.json`
Origem: `carrosseis/<slug>/` (`carrossel.md` + `slides/01.png…` do `scripts/gerar_carrossel.py` + `material/<palavra>.pdf`).
Montado por `uv run python scripts/montar_pacote.py carrosseis/<slug>`, que exige os portões do alvo carrossel
(**roteiro** = `carrossel.md` inteiro + `material/*.pdf`; **imagem** = `slides/*.png`; **pauta** opcional; **sem corte**)
e confere os slides (3–10, PNG/JPEG, 1080×1440). `slides/grade.jpg` é prévia e não vai ao ar.
```json
{
  "slug": "2026-11-11-certificados", "formato": "carrossel", "criado_em": "...", "qa": "PASS",
  "arquivos": {"slides": ["slides/01.png", "slides/02.png", "…"], "material": "material/selo.pdf",
               "carrossel": "carrossel.md"},
  "cta_palavra": "SELO", "material_titulo": "…", "tema": "…", "pilar": "…",
  "gauntlet": {"versao": 1, "origem": "carrosseis/<slug>", "veredictos": {"roteiro": {…}, "imagem": {…}},
               "arquivos": {"slides/01.png": "<sha256>", "…": "…", "material/selo.pdf": "<sha256>"}}
}
```
- `qa: "PASS"` no carrossel = a conferência dos slides do `montar_pacote.py` + os portões (não há vídeo para o
  revisor-de-video). `cta_palavra`, `material_titulo`, `tema`, `pilar` vêm do frontmatter do `carrossel.md`
  (`palavra`, `material_titulo`, `tema`, `pilar`).
- A ordem de `arquivos.slides` é a ordem no post. Na fila o PORTÃO-PUBLICACAO cobre também `slides/*.png|jpg` (por
  caminho: trocar dois slides de lugar vence o veredicto).
- **Proporção:** o modelo é 3:4 (decisão de 09/11). A documentação da API do Instagram fala em 4:5 a 1,91:1, mas em
  09/11 um teste sem publicar (filhos 1080×1440 + contêiner CAROUSEL, sem `media_publish`) chegou a `FINISHED` — "ready
  to be published", igual ao controle 4:5. O `publicar.py` ainda avisa; se a Meta recusar no `media_publish`
  (code 36003 / subcode 2207009), o erro diz isso.

### 9b. `portoes.json` — livro de veredictos (escrito SÓ por `scripts/portoes.py registrar`)
Em `videos/<slug>/` (portões pauta, roteiro, imagem, corte) e em `06-publicar/<slug>/` (portão publicacao). Nunca editar
à mão: um veredicto é o registro do que o portão viu.
```json
{"versao": 1, "veredictos": [
  {"portao": "imagem", "agente": "portao-imagem", "resultado": "APROVADO|BLOQUEADO|ESCALADO",
   "impressao": "3f1a9c2b77e0", "em": "2026-10-30T18:00:00+00:00", "volta": 1,
   "achados": {"S0": 0, "S1": 0, "S2": 2}, "relatorio": "videos/<slug>/qa/portoes/imagem-2026-10-30-v1.md",
   "arquivos": {"edicao/cor/corte-cor.mp4": "<sha256>", "capa/capa-A.png": "<sha256>"},
   "nota": "opcional", "decisao_autor": "só depois de um ESCALADO: a opção que ele escolheu"}
]}
```
`arquivos` = impressão de cada arquivo da área no momento do veredicto (o `roteiro.md` entra pela fala + CTA/material;
o `post.json` pelos campos que vão ao ar). Estado de um portão = o último veredicto, **vencido** se algum arquivo da
área hoje não estiver entre os que ele aprovou. Cache de hashes em `_controle/.cache-portoes.json` (só velocidade).

## 10. `06-publicar/<slug>/post.json` (escrito pelo `publicador`, lido por `scripts/publicar.py`)
```json
{
  "slug": "...",
  "publicar_em": "2026-09-21T19:00:00+01:00",
  "plataformas": ["instagram", "facebook"],
  "estado": "agendado",
  "confirmar": true,
  "instagram": {"legenda_arquivo": "legenda-instagram.txt", "capa": "capa/capa.png",
                "share_to_feed": true, "trial": null, "container_id": null, "media_id": null, "permalink": null},
  "facebook": {"legenda_arquivo": "legenda-facebook.txt", "tipo": null, "video_id": null, "permalink": null},
  "material": {"palavra": "PROMPT", "arquivo": "material/guia.pdf", "titulo": "o guia do prompt", "url": null},
  "primeiro_comentario": {"arquivo": "primeiro-comentario.txt", "instagram_id": null, "facebook_id": null},
  "publicado_em": null,
  "erros": []
}
```
- `estado` ∈ `agendado | aguardando_confirmacao | publicando | publicado | erro | pausado`.
- `aguardando_confirmacao`: hora chegou mas `confirmar` é true (primeiros posts) ou o post está > 6 h atrasado — só publica com `publicar <slug> --sim` depois do OK do autor.
- `facebook.tipo` (14/10): `null` até publicar; `"reel"` (vídeo ≤ 90 s → `/{page-id}/video_reels`) ou `"video"`
  (> 90 s → vídeo da Página, `graph-video…/{page-id}/videos`; a API de Reels do FB só aceita 3–90 s). A duração vem
  de `pacote.duracao` (ou ffprobe). `video_id`/`permalink` valem para os dois tipos.
- `trial`: `null` ou `{"graduation_strategy": "MANUAL|SS_PERFORMANCE"}`.
- `material`: `{palavra, arquivo, titulo, url}` — `palavra` = `pacote.cta_palavra`, `arquivo` = `pacote.arquivos.material`
  (o PDF), `titulo` = `pacote.material_titulo`, `url` = `null` até o upload. O `publicar.py` sobe para o R2 **só esse
  arquivo** (nunca a pasta `material/` inteira) e grava a URL aqui e no `dm-material.json`.
- `primeiro_comentario` (09/11): o texto vem de `primeiro-comentario.txt` (escrito pelo `publicador`, coberto pelo
  PORTÃO-PUBLICACAO). Logo depois de publicar em cada rede, a própria conta comenta esse texto (`POST /{media|video}/comments`)
  e o id fica em `instagram_id` / `facebook_id`. Falhar aqui não desfaz a publicação: vai para `erros`
  (`instagram-comentario` / `facebook-comentario`) e `publicar.py comentar <slug>` repete só o que falta.
`instagram.container_impressao` (GAUNTLET, 22/10): a impressão do PORTÃO-PUBLICACAO quando o container foi criado; numa nova tentativa, container de outra impressão não é reaproveitado.

**Carrossel** (09/11, pacote §9c) — `post.json` com `"formato": "carrossel"` (o campo só existe no carrossel; Reel não
tem). Sem `instagram.capa` (a capa é o 1.º slide), sem `trial` (Trial é só de Reel), sem `share_to_feed`:
```json
{
  "slug": "...", "formato": "carrossel", "publicar_em": "...", "plataformas": ["instagram", "facebook"],
  "estado": "agendado", "confirmar": true,
  "instagram": {"legenda_arquivo": "legenda-instagram.txt", "filhos": [], "container_id": null,
                "media_id": null, "permalink": null},
  "facebook": {"legenda_arquivo": "legenda-facebook.txt", "tipo": "fotos", "foto_ids": [], "post_id": null,
               "permalink": null},
  "material": {...}, "primeiro_comentario": {...}, "publicado_em": null, "erros": []
}
```
- IG: `filhos` = ids dos contêineres de cada slide (`POST /{ig-user}/media` com `image_url` JPEG no R2 +
  `is_carousel_item=true`); `container_id` = o contêiner `media_type=CAROUSEL` (`children` na ordem + `caption`);
  `media_id`/`permalink` depois do `media_publish`. Os slides sobem para o R2 em `carrosseis/<slug>/NN.jpg`
  (PNG → JPEG, a API do IG só aceita JPEG).
- FB: `tipo: "fotos"`; `foto_ids` = fotos enviadas do disco como NÃO publicadas (`POST /{page-id}/photos`,
  `published=false`); `post_id` = o post da Página (`POST /{page-id}/feed` com `message` + `attached_media[i]`);
  `permalink` vem de `permalink_url`. O 1.º comentário do FB vai no `post_id`.
- `formato` entra na impressão do PORTÃO-PUBLICACAO (muda o que vai ao ar).

## 11. `07-publicados/<slug>/metricas.json` (escrito por `scripts/metricas.py`, lido pelo `analista-de-metricas`)
```json
{
  "slug": "...", "publicado_em": "...", "permalink_instagram": "...", "permalink_facebook": "...",
  "media_id_instagram": "...", "video_id_facebook": "...", "duracao_s": 61.2, "palavra": "PROMPT",
  "trial": null, "tema": "...", "pilar": "...", "nota_retencao": "A API da Meta não dá a curva…",
  "leituras": [{
    "lido_em": "2026-10-18T09:30:00+01:00", "dias_desde_publicacao": 5.1,
    "instagram": {"media_id": "...", "campos": {"like_count": 0, "comments_count": 0, "...": "..."},
                  "trial": "<trial_params ou o que a API disse>", "metricas": {"views": 0, "reach": 0, "...": 0},
                  "nao_suportadas": {"follows": "<mensagem da Meta>"}, "erro": null, "permissao_em_falta": null},
    "facebook": {"video_id": "...", "metricas": {"blue_reels_play_count": 0}, "nao_suportadas": {}},
    "comentarios_palavra": {"com_palavra": 0, "directs": 0, "pessoas": 0, "fonte": "_controle/comentarios/estado.json"},
    "resumo": {"instagram": {"views", "alcance", "curtidas", "comentarios", "salvamentos", "compartilhamentos",
                             "seguidores_ganhos", "visitas_perfil", "tempo_medio_s", "pct_medio_assistido",
                             "taxas_sobre_alcance_pct": {"salvamentos", "comentarios", "compartilhamentos", "curtidas",
                                                         "comentarios_palavra"}},
               "facebook": {"plays", "alcance", "tempo_medio_s", "pct_medio_assistido", "seguidores_ganhos"},
               "palavra": {"comentarios", "directs"}}
  }],
  "ultima": {"...": "cópia da leitura mais recente"}
}
```
- Taxas em **%** sobre o alcance do Instagram; `pct_medio_assistido` = tempo médio ÷ `duracao_s` (do `pacote.json`).
  Tempos da Meta vêm em ms e são gravados em segundos no `resumo`; os valores crus ficam em `metricas`.
- Leitura **completa** = Instagram com `metricas` e sem `erro`. O launchd lê 1×/dia os Reels com ≥ 5 dias sem leitura
  completa; leitura com permissão em falta é repetida no dia seguinte. `--forcar` acrescenta outra leitura (histórico).
- `_controle/metricas.md` é gerado a partir destes arquivos (uma linha por vídeo, a `ultima`); não editar à mão.

## 12. `painel/biblioteca.yaml` — o acervo de estilos da Biblioteca do painel (escrito pelo autor, lido pelo sincronizador)

A tela **Biblioteca** do painel (`painel/design/telas/biblioteca.md`) mostra o acervo de estilos do estúdio: looks de
cor, estilos de capa e de legenda, fontes, animações, armazenamento e a stack. Parte disso vem de arquivos que já existem
(os looks de `00-marca/cor/luts/` + `00-marca/cor/cor.md`, as animações de `videos/<slug>/animacoes/<Exx>/brief.md`, o
armazenamento do próprio banco). **O que nenhum outro arquivo registra fica aqui**, num YAML que o autor mantém, como
o `painel/equipe.yaml`. Quem lê é o `painel/sync/sincronizar.py` (a cada 15 min, pelo launchd), que **só lê** e copia
para o banco do painel. O arquivo é auditado pelo PORTÃO-DADOS (área `dados`, padrão `*.yaml`).

### Forma geral
Um mapa com até seis seções. Cada seção é uma **lista**; a ordem dos itens é a ordem na tela (coluna `ordem`).

```yaml
capas:        # estilos de capa                → capa_estilos + capa_estilos_exemplos
legendas:     # estilos de legenda             → legenda_estilos
fontes:       # fontes da marca                → fontes
ferramentas:  # a stack (aba Sistema)          → sistema_ferramentas
modelos:      # a frase de cada modelo de IA   → modelos_descricao (e sistema_modelos.descricao)
looks:        # nome, frase e rosto de cada cartão de look → looks.nome, descricao, rosto_ire, rosto_ire_em, rosto_ire_amostra
```
Texto = string não vazia; espaços nas pontas saem. Caminho = relativo à raiz do projeto, com `/`, sem `/` no começo,
sem `..` e sem `\`.

### `capas` — estilos de capa
| Campo | Obrigatório | Formato | O que é |
|---|---|---|---|
| `id` | sim | minúsculas-com-hífen, único na seção | a chave do estilo (`capa_estilos.id`) |
| `nome` | sim | texto | o nome na tela |
| `descricao` | sim | texto | o que caracteriza o estilo |
| `ficha` | sim (pode ser `null`) | caminho | a ficha do estilo no projeto; o banco marca se ela existe (`ficha_existe`) |
| `em_uso` | sim | `true` / `false` | se é o estilo usado hoje |
| `exemplos` | sim | lista não vazia de slugs de pacote (`AAAA-MM-DD-…`), sem repetir | capas reais: `<pasta>/<slug>/capa/capa.png`, procurada em `07-publicados/`, depois `06-publicar/`, depois `05-render-pronto/` (o pacote anda entre as três) |

Só capas com o autor, nunca com a foto de outra pessoa (`CLAUDE.md`, regra 3): abra cada imagem antes de pôr o slug.

### `legendas` — estilos de legenda
Os mesmos campos de `capas`, sem `exemplos` (`id`, `nome`, `descricao`, `ficha`, `em_uso`). A amostra é desenhada pela
tela a partir da ficha.

### `fontes` — fontes da marca
| Campo | Obrigatório | Formato | O que é |
|---|---|---|---|
| `familia` | sim | texto, único na seção | o nome da família |
| `remotion` | sim (pode ser `null`) | letras e dígitos | o pacote `@remotion/google-fonts/<remotion>` que o `remotion/src/brand.ts` carrega; `null` = fonte que não passa pelo Remotion |
| `estilo` | sim | `normal` ou `italico` | o 1.º argumento do `loadFont` (`"normal"` / `"italic"`) |
| `pesos` | sim | lista de inteiros de 100 a 1000, sem repetir | os `weights` do `loadFont` |
| `uso` | sim | texto | onde a fonte aparece |
| `reserva` | não (padrão `false`) | `true` / `false` | só alternativa na pilha (a tela mostra as outras) |

O sincronizador confere cada fonte no `brand.ts` (`fontes.confere_brand_ts`): importado o pacote, com o mesmo estilo e
os mesmos pesos = `true`; diferente = `false` e aviso.

### `ferramentas` — a stack
| Campo | Obrigatório | Formato | O que é |
|---|---|---|---|
| `nome` | sim | texto, único na seção | a peça |
| `tipo` | sim | texto | o que ela é ("API", "Linguagem", "Banco de dados"…) |
| `desc` | sim | texto | o que ela faz neste estúdio (no banco, `descricao`: `desc` é palavra reservada no SQL) |
| `versao` | não | `{arquivo: <x>.json, pacote: <p>}` · `{arquivo: <x>.toml, chave: <a.b>}` · `{arquivo: <outro>}` | de onde LER a versão em uso: `dependencies`/`devDependencies` do package.json, a chave do .toml (pontos = seções) ou a 1.ª linha não vazia. A versão nunca é escrita à mão |

### `modelos` — a frase de cada modelo de IA
| Campo | Obrigatório | Formato | O que é |
|---|---|---|---|
| `modelo` | sim | o id do modelo nos registros do Claude Code (ex.: `claude-opus-5-5`), único | o mesmo id da tabela de preços do sincronizador |
| `desc` | sim | texto | a frase da aba Sistema (no banco, `descricao`) |

O percentual dos 30 dias não vem daqui: vem do consumo (view `sistema_modelos`).

### `looks` — o nome, a frase e o rosto de cada cartão de look
Os looks em si **não** estão aqui. Os cartões são `vlog` (o quadro da amostra como a câmera grava), `rec709` (a
`entrada-camera.cube`) e cada `korvu-look-vN.json` do topo de `00-marca/cor/luts/` (`_descartadas/` fica fora). O
estado de cada look vem do `cor.md` (`versao_ativa` = em uso, `alternativa_medida` = alternativa, `arquivados: [vN]` =
arquivado). Aqui ficam o texto do cartão e a medida do rosto do autor, em IRE.

| Campo | Obrigatório | Formato | O que é |
|---|---|---|---|
| `id` | sim | `vlog`, `rec709` ou `vN`, único | o cartão |
| `nome` | não | texto | o nome na tela; **vence** o `"nome"` do `.json` do look, que continua inteiro em `looks.ficha` |
| `desc` | não | texto | a frase do cartão (no banco, `looks.descricao`) |
| `rosto_ire` | não; só em `vN` | número de 0 a 110, com ponto decimal (`40.9`) | o rosto medido, em IRE (`vlog` e `rec709` são referência: rosto neles = ✗) |
| `medido_em` | sim **se houver `rosto_ire`** | `AAAA-MM-DD` | a data da medição (não a do look) |
| `amostra` | não (só com `rosto_ire`) | texto | o arquivo ou corte medido |
| `fonte` | sim **se houver `rosto_ire`** | `arquivo:linha[,linha]` (ex.: `00-marca/cor/cor.md:7,41`) | de onde veio o número; o `painel/tests/test_biblioteca_yaml.py` confere que ele aparece nessas linhas |

`medido_em`, `amostra` ou `fonte` sem `rosto_ire` = ✗ (uma medida sem o número). Cartão sem item = nome do `.json` (o
`vlog` não tem `.json`: NULL), sem frase e sem medida, sem aviso.

### O que dá ✗ e o que dá ⚠
**✗ — a passagem para e nada é gravado.** O painel continua com a passagem anterior, e o log
(`_controle/logs/painel.log`) ganha uma linha `✗ arquivo do projeto ilegível (painel/biblioteca.yaml: …)` que diz o
lugar (ex.: `capas[1]: falta em_uso`). Acontece com:
- YAML inválido;
- o topo não é um mapa;
- seção desconhecida, ou seção que não é lista;
- item que não é mapa;
- chave desconhecida num item (um campo com nome errado não passa calado);
- campo obrigatório faltando, ou valor fora do formato da tabela;
- `id`/`familia`/`nome`/`modelo` repetido na mesma seção.

**⚠ — a passagem segue.** Sai uma linha `⚠ …` no log e o dado fica vazio ou marcado. Acontece com:
- o arquivo ausente (tudo vazio) ou uma seção ausente (ela vazia);
- capa de exemplo não encontrada (`pasta`/`caminho` NULL);
- ficha que não existe (`ficha_existe = false`);
- fonte que não bate com o `brand.ts`, ou que não deu para conferir;
- versão não encontrada no arquivo indicado (`versao` NULL);
- modelo fora da tabela de preços (`com_preco = false`);
- `looks` com um `id` que não é cartão da passagem (um look que foi para `_descartadas/`, ou `vlog`/`rec709` sem a
  amostra/entrada): o item é ignorado.

### Como acrescentar um item
Nada de código nem migração: o item novo vira uma linha nova no banco na próxima passagem.

| Para acrescentar | O que fazer |
|---|---|
| estilo de capa | um item em `capas` com pelo menos um slug de pacote cuja `capa/capa.png` exista (e mostre o autor) |
| estilo de legenda | um item em `legendas` |
| fonte | primeiro carregá-la no `remotion/src/brand.ts`, depois um item em `fontes` com o mesmo estilo e os mesmos pesos |
| ferramenta | um item em `ferramentas` |
| frase de modelo | um item em `modelos` |
| look | o `.cube` + `.json` em `00-marca/cor/luts/` (não precisa do yaml); o nome, a frase e a medida do rosto, se houver, num item em `looks`; a prévia (a foto do autor com o look) sai com `uv run python painel/sync/previas_looks.py`, que gera só a do look novo |
| animação | um `brief.md` em `videos/<slug>/animacoes/<Exx>/` (não precisa do yaml) |

Depois, conferir:
- `uv run python painel/sync/sincronizar.py --seco` mostra a contagem nova e nenhum ⚠;
- `uv run python painel/tests/test_biblioteca_yaml.py` confere o yaml real contra a maquete aprovada
  (`painel/design/telas/biblioteca.html`), o `brand.ts` e as fontes dos números.

**Mudar o formato** (uma seção ou um campo novo): o código que aceita o formato novo entra primeiro (ou no mesmo
comando da troca); só depois o yaml real ganha o campo. Ao contrário, o sincronizador em produção recusa o arquivo (✗) e
o painel fica parado na passagem anterior até a troca (PD29, 25/10).

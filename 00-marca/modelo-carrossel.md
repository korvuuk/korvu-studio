# Modelo de CARROSSEL da Korvu — APROVADO pelo autor em 09/11/2026

> Substitui o modelo editorial de 07/11 (papel bege, 4:5, "korvu." no topo), que nunca foi publicado.
> Decisões: `docs/decisoes.md` (07/11 e 09/11). Referência estudada (estrutura, não design):
> `01-ideias/pesquisas/referencias-carrossel/2026-11-09-plataformas-gratuitas/analise.md`.
> **Exemplo vivo:** `carrosseis/_modelo-cursos-gratis/` (`carrossel.md` + `slides/`). Copie a pasta para começar um novo.
> Gerador: `uv run python scripts/gerar_carrossel.py carrosseis/<slug>/carrossel.md`.

## 1. A pegada
O autor abre e fecha o carrossel; o miolo ensina. Cada item é uma **instituição ou ferramenta renomada** (universidade,
empresa de IA) mostrada pelo **logo oficial** — o nome conhecido é o que faz parar e salvar. Foco: ensinar e dar
informação útil, com link.

```
[CAPA: Autor + logos + promessa] → [ITEM] × n (molde fixo) → [RESUMO salvável] → [CTA: Autor + palavra]
```

## 2. Formato
- **3:4 = 1080×1440** PNG (o mais comprido, cara de Reels). **3 a 10 slides** (teto da API do Instagram).
- **Cabeçalho LIMPO:** sem "korvu.", sem "@sua_conta", sem número de página, sem "arrasta". Nada de enfeite.
- **Fonte:** Inter Tight (a da animação) — títulos em **900, CAIXA ALTA**; texto em 500. Um acento: laranja `#E85002`.
- **Foto do autor em preto e branco** na capa e no CTA.

## 3. Os slides
| Slide | O que leva |
|---|---|
| **capa** | foto do autor em P&B (o **frame da PAUSA DA CAPA** — ver §5) + **até 6 logos oficiais** em quadros brancos em volta da cabeça (nunca sobre o rosto) + **número em laranja** + título em 2 linhas ("6 CURSOS / GRÁTIS DE IA") + 1 linha de subtítulo |
| **item** (um por instituição) | molde fixo, igual ao da referência: **logo + NOME + link** no topo → **1 frase** (≤ 30 palavras, teto 45) → **etiquetas** (a 1.ª em laranja: grátis · duração · certificado · idioma · pré-requisito) → **a página oficial** numa tela de notebook que sai pelo pé do slide. Cada item dá uma razão diferente para valer |
| **resumo** | "SALVA ESSA LISTA": todos os itens numa tela, com logo, nome, uma linha e o número. É o slide que se salva/printa (gerado sozinho a partir dos itens) |
| **cta** | Autor de novo (outro frame da pausa, de preferência sorrindo) + "COMENTA **PALAVRA**" + o que a pessoa recebe (o PDF com os links) |

## 4. Regras de conteúdo
- PT-BR ("você", "pra"), voz do autor; nada de "expert". **Não inventar experiência dele** ("eu fiz esse curso") se não for verdade.
- **Todo fato com fonte oficial conferida no dia** (gratuidade, preço e duração mudam): as URLs ficam no frontmatter
  `fontes:` do `carrossel.md`. No slide não entra "Fonte:" (padrão 19/10). Ser honesto quando há porém
  ("pede Python", "sem certificado formal") — a referência mostrou que isso aumenta a confiança.
- **Logo SEMPRE oficial, nunca recriado** (09/11). Baixar do Wikimedia Commons (ou kit de imprensa) para
  `00-marca/assets/logos-terceiros/<nome>.png` e anotar origem e licença em `FONTES.md` — autorização permanente do autor.
  Mostrar a marca é permitido (regra 3); nunca como parceria nem colado a um logo da Korvu.
- **Print da página oficial:** `node scripts/print_limpo.mjs <url> carrosseis/<slug>/prints/<nome>.png --espera 8000`
  (abre a página, **remove os avisos de cookies** — inclusive os do meio da tela — e fotografa em 2880×1800).
  O que sobrar (faixa de cookies que não é fixa) sai com recorte do ffmpeg (`crop`). Conferir olhando.
- **Palavra-chave = sempre um PDF** com os links (produtor-de-material), **diferente da palavra do Reel** se os dois
  estiverem no ar ao mesmo tempo (21/10). Nunca prometer PDF que não exista.
- Legenda do post: palavra-chave na 1.ª linha, ≤ 5 hashtags, pedido de salvar.

## 5. A foto do autor (frame da pausa da capa)
Toda gravação começa com ele parado olhando a câmera (a **pausa da capa**). Esse trecho fica nos intermediários
`videos/<slug>/edicao/fontes/*.mp4` (1440×2560, **ainda em V-Log**) — tirar o frame de lá, com o LUT de entrada:

```
"$FFMPEG_BIN" -ss <tempo> -i videos/<slug>/edicao/fontes/<arquivo>.mp4 -frames:v 1 \
  -vf "lut3d=00-marca/cor/luts/entrada-camera.cube" carrosseis/<slug>/fotos/capa.png
```
O tempo é o do candidato `pausa-capa` em `videos/<slug>/capa/candidatos/scores.json` (o mesmo frame da capa do Reel).
Sem gravação nova do tema, vale a pose da capa de outro Reel (`videos/<slug>/capa/candidatos/pose-*.png`, já com cor).
O gerador põe em P&B. Ajustar o enquadramento com `foto_posicao:` se o rosto não ficar entre ~y 270 e 790 (os logos
ocupam os cantos de cima), `foto_brilho:` (padrão 1.12; gravação com pouca luz pede ~1.45) e `titulo_tamanho:`
(padrão 124 px; "6 CERTIFICADOS" pediu 106).
Só ler a pasta do vídeo — nunca escrever nela (pode ser de outra sessão).

## 6. Esteira
```
pesquisa / fichamento (ai-engineer/biblioteca/... ou dossiê) → PORTÃO-PAUTA
→ carrosseis/<AAAA-MM-DD-palavra>/carrossel.md (copiar de _modelo-cursos-gratis)  → revisor-de-roteiro (PORTÃO-ROTEIRO)
→ logos oficiais + prints + fotos da pausa da capa
→ uv run python scripts/gerar_carrossel.py carrosseis/<slug>/carrossel.md   → slides/01.png… + grade.jpg
→ portao-imagem → Autor aprova olhando a grade → produtor-de-material (PDF) → publicador (legenda) → portao-publicacao
```
Cadência pretendida: 1 carrossel por dia (07/11).

## 7. O que ainda falta (não é desta área)
- **Publicação automática de carrossel**: o `scripts/publicar.py` só publica Reel (IG = contêiner `CAROUSEL`; FB = post
  com várias fotos) — área **automação Meta**. Até lá, o autor posta pelo app com os PNG de `slides/`.
- `pacote.json`/selo e `portoes.py` ainda não conhecem o alvo "carrossel".

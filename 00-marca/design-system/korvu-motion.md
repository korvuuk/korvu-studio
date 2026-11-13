# Design System Korvu — MOTION (animação explicativa em tela cheia)

> **Aprovado pelo autor em 05/11 — tema VIDRO** (série AI Engineer, `ai-engineer/`). Pedido dele: "animação fluida,
> um motion design que mostra tutorial… flat design, degradê, obsidian… seguindo o nosso guideline", depois a
> referência (YouTube `D5qpBbEWTxo`, de Sanji Chien): **vidro, muito clean, muito suave**, com animação também
> **por cima do vídeo dele falando**. Modelos: `videos/_modelos/ai-engineer-rag/`, código em
> `remotion/src/animacoes/tecnico/` (`motion.ts` = tokens, `ModeloRAG.tsx` = o modelo).
> Fica ao lado dos outros dois sistemas: `korvu-video.md` (legenda, grade, cartela) e `korvu-editorial.md` (PDF e
> cartão do CTA). Nenhuma cor de marca nova: tudo sai do laranja `#E85002`, do nude `#D9C3AB` e do preto.

## 1. Formato — tela cheia, sem dividir
1. **Autor fala** (com animação leve POR CIMA dele: selo da série, ícones de vidro, número que conta, barra de
   vidro embaixo) →
2. **transição BOLA** (05/11, 2.ª volta: a versão de recorte duro foi "muito amador"). A bola abre a partir do cartão sob o queixo, com a **borda macia** (máscara radial com ~140 px de pena). No anel, um núcleo branco desfocado, halo laranja e halo vermelho por fora, como em D5qpBbEWTxo 16:13. A curva é bezier(0.65,0,0.35,1), em ~30 frames. **O vídeo dele sai de foco (0→18 px) e cresce (1→1,12) enquanto a bola cobre**, e o palco entra de 1,1→1 desfocado. Código: `AnelBola` em `ModeloMisto.tsx` →
3. **animação em tela cheia** contando o conceito como tutorial, etapa a etapa (01, 02, 03…) →
4. **transição de volta**: a bola fecha no mesmo ponto, em ~34 frames, e o palco sai de foco. **Antes de virar um ponto, a bola se dissolve** (raio 560→260: o anel engrossa, desfoca e some) e o autor volta a ficar nítido. Nunca fechar seco até o peito. → Autor de novo, com o resumo em vidro ao lado.

Nada de `split` nesta série (o split continua valendo nos vídeos de história/perfil).

## 2. Tema — VIDRO é o padrão (Autor, 05/11)
A `obsidiana` foi descartada; o código ainda tem o tema só como alternativa, não usar sem ele pedir.

| | `vidro` (molde da referência) | `obsidiana` |
|---|---|---|
| Fundo | **preto `#050506` com luzes laranja que passeiam** (2.ª volta de 05/11: o campo laranja inteiro "fica muito laranja"), anéis concêntricos bem finos, vinheta | preto `#060608`, luzes em degradê (laranja, nude, um toque de roxo) que respiram, grade de pontos |
| Cartão | vidro: branco 7 %, borda branca 20 %, desfoque 28 px, brilho de 1,5 px no topo | `#131318`, borda branca 8 % |
| Destaque (o que está ativo agora) | degradê laranja com brilho | degradê laranja com brilho |
| Título | **Inter Tight 600, tracking −0,05em** (`FONTE.motion`; 05/11: Geist 700 "muito gorda"). Rótulos em 500, nunca 700+ | Bricolage 800, branco |
| Resposta certa | cartão branco, texto escuro | cartão de papel `#EFEBE3`, texto escuro |

Sobre o vídeo do autor, nos dois temas: **vidro translúcido** (branco 14 %, borda 42 %, desfoque 22 px).

## 3. Regras de movimento (do `launch-motion`, adaptadas para 25 fps vertical)
Skill instalada em `~/.claude/skills/launch-motion` (05/11). O que vale aqui:
- **Storyboard primeiro, animação depois.** Cada cena tem: o que aparece, como se move, a câmera e o intervalo de
  frames. A soma tem de bater com a fala. Sem storyboard, as cenas saem fora de ordem e tudo se mexe ao mesmo tempo.
- **Nada se move em linha reta** (sempre mola ou easing).
- **Entrada ~0,5 s (12–13 frames)** com leve passada do ponto (mola, damping ~13–14). **Saída mais rápida que a
  entrada** (~60 %, ease-in).
- **O que é importante fica ≥ 1,5 s (38 frames)** na tela. Número que conta leva ~1 s (25 frames), nunca pula
  de uma vez.
- **Nada para por completo**: o que está parado continua respirando (escala 1 → 1,02 ou ±4–6 px) e a câmera
  sempre tem um micro-empurrão.
- **Como no After Effects**: elementos ligados se movem juntos (pai/filho); cada item de um grupo entra **2–4
  frames depois** do anterior; o próximo movimento começa antes do último terminar (nos ~20 % finais).
- **Mesmos elementos de ponta a ponta**: o pedaço de documento vira ponto, que vira linha do contexto. Morfar
  em vez de cortar é o que deixa a explicação fluida.
- **Clique** = pressão de 1 → 0,96 → 1 em ~8 frames; **cursor** anda em arco, nunca em reta.
- **Câmera**: um contêiner por cena, sempre com easing de entrada e saída; panorâmica ≥ 0,8 s.
- **Projeto a 25 fps e 1080×1920** (regra da raiz). Os 60 fps e 1920×1080 da skill NÃO valem aqui.
- Antes do vídeo inteiro: **um quadro de cada cena** renderizado e olhado (sobreposição, texto saindo da tela).

## 4. Texto e área segura
- **NADA sobre o rosto do autor (05/11).** Por cima do vídeo dele, tudo fica **do queixo para baixo** (faixa entre o queixo e y 1250) ou acima da cabeça. Medir o rosto do take com o detector da skill `capa-reels` (`frame_candidates.py`) e somar ~40 px de folga abaixo do queixo; no corte de teste o queixo chega a y 909 → faixa y 950–1250. Também vale no zoom do corte (o rosto cresce).
- Título de etapa em y ≈ 300, conteúdo entre y 380 e 1250 (a base é da interface do Instagram).
- **Palavra GRANDE em cada etapa** (05/11, como o "Two Options" da referência): uma palavra que ocupa a largura (até 260 px, `fitText` em 960 px). O branco esmaece para baixo, as letras entram uma a uma (sobem e ganham foco), e a pílula com o número fica em cima. Componente `TituloGigante`; o conteúdo começa em y ≈ 560 para não tapar a palavra.
- **Título da série sobre o autor** (05/11): "AI ENGINEER" em **CAIXA ALTA grande** (Inter Tight 600, 124 px, −0,035em), branco sólido com sombra suave, **sem pílula de vidro** (sumia sobre o vídeo). Em cima, a pílula laranja "#NN". Fica do queixo para baixo (y ≈ 960) e as letras entram uma a uma. O que vier por baixo começa em y ≥ 1200.
- Texto mínimo 36 px. Sem pontuação na tela (decisão de 16/09). Minúsculas.
- Nome técnico em inglês aparece pequeno, com a tradução grande ("retrieval → **buscar**").

## 5. Som
Toda animação tem sound design: `00-marca/som/sound-design.md`.

## 6. Misturar animação + vídeo extra + imagem (Autor, 05/11 — prioridade da série)
"Não ficar só animações": cada explicação junta **os três elementos na mesma cena**. A mídia de verdade (vídeo
extra, gravação de tela, foto) entra **dentro** do vidro e vira peça da animação, nunca um corte seco para um
B-roll solto. Modelo: `videos/_modelos/ai-engineer-misto/`, código `remotion/src/animacoes/tecnico/ModeloMisto.tsx`.

| Padrão | O que acontece | Quando usar |
|---|---|---|
| **A. Cartão sobre o autor** | vídeo extra num cartão de vidro **abaixo do queixo**, tocando enquanto ele fala | anunciar o assunto/ferramenta antes de sair dele |
| **B. A mídia vira o palco** | o cartão cresce até virar a janela e o palco abre a partir do retângulo dele (em vez do círculo) | a transição o autor → animação quando existe vídeo do assunto |
| **C. Anotação presa ao vídeo** | etiquetas e contorno laranja desenhados sobre o que acontece no vídeo (pergunta, resposta, botão) | gravação de tela, demo, interface |
| **D. Foto em leque → vídeo** | fotos em molduras de vidro com Ken Burns; a do meio dissolve e vira vídeo | quando há foto e vídeo do mesmo assunto (hardware, lugar, pessoa) |
| **E. Dado por cima do vídeo** | barra de vidro, número que conta, etiqueta de estado dentro da janela | números, progresso, antes/depois |
| **F. Mídia vira nó do diagrama** | a janela encolhe e vira o nó ("modelo") com o vídeo tocando dentro; linhas e pulsos ligam os nós | arquitetura, fluxo (app → api → modelo, MCP, RAG) |
| **G. Miniaturas vivas no resumo** | as mídias da explicação voltam como miniaturas tocando dentro das barras do resumo | fecho da explicação |

Regras:
- **Um elemento de mídia é o mesmo de ponta a ponta** (foto → janela → nó → miniatura): morfar, nunca cortar.
- Vídeo extra **sempre mudo** dentro da animação, em loop se acabar (ou bumerangue preparado no ffmpeg).
- Logos de emissora/marca d'água: cortar no preparo (`crop`), nunca tapar com elemento.
- Foto nunca parada: Ken Burns 1,04 → 1,14 e flutuação de ±5 px.
- Mídia de terceiros segue a regra 4 da raiz (B-roll com licença × comentário); créditos só na descrição (19/10).
- Gravação de tela não recebe LUT (regra 8); a moldura de vidro é que dá o acabamento.

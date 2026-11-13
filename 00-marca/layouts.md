# Layouts do vídeo — principal + cenas extras

> **Regra do autor (2026-09-17), com screenshots de referência:** o **formato do arquivo** decide o layout.
> Extra deitado (formato YouTube) divide a tela; extra em pé ocupa a tela toda. Os números abaixo são os valores
> em `remotion/src/brand.ts` (`LAYOUTS`).

Tela 1080×1920 · 25 fps · zonas seguras: topo 270 px, base 670 px, laterais 65 px (direita 120 px).

| Modo | Quando | Extra | Principal (Autor) | Legendas |
|---|---|---|---|---|
| **full-principal** (padrão) | hook, CTA, falas de opinião | — | tela cheia | y≈1150 |
| **split** | extra **deitado** (largura/altura ≥ 1,2 — 16:9) | **em cima, encostado no topo**: largura cheia, caixa 1080×608 em y 0 (sem faixa preta — Autor, 02/10) | **embaixo** (de y 608 até o fim), recortada no rosto | **y≈715**, logo abaixo da divisória |
| **full** | extra **em pé** (vertical) | tela cheia (`cover`) | sai de cena; volta quando o extra termina | por cima, se a mídia não tiver texto |
| **card** | print, número, imagem rápida | cartão arredondado central (1000×330, pé em y 1250) | atrás, escurecido | some enquanto o cartão está ativo |
| **solo** | imagem/vídeo retangular isolado, sem outro elemento pra encaixar (§ abaixo) | `contain` centralizado **dentro da área útil** (y 270 até 1250 − `legendaReservada`), moldura + fundo de marca ao redor | sai de cena | **abaixo da caixa** (y≈1150, dentro da área reservada — nunca sobre a mídia) |

## Regras
- **O formato manda.** O `modo` escrito no roteiro é sugestão; o `gerar_props.py` mede o arquivo e corrige (e avisa no log). `card` é a exceção: é escolha de layout.
- **Transição fluida** (não pode ser corte seco): a câmera **desliza** entre tela cheia e o painel de baixo em `LAYOUTS.split.transicaoFrames` (10 frames ≈ 0,4 s), com curva suave, e o extra entra deslizando de cima. Na saída o caminho é o inverso: o extra sai e o autor volta a ocupar a tela.
- **Abrir com a imagem do CONTEÚDO em tela cheia** (voz do autor por cima) e o autor entra depois — teste C5/C10/C20 (decisão de 17/10, `_controle/estrategia-de-alcance.md` §2.8). **Fechar** com o autor em tela cheia (CTA).
- Não ficar mais de ~8 s sem mudança visual (extra, zoom ou texto).
- **O vídeo final é cru:** extra que falta não vira etiqueta no render de entrega (`gerar_props.py --final`). A etiqueta "EXTRA Exx FALTANDO" existe só no preview/revisão, para eu e você sabermos o que ainda falta; o QA reprova até o arquivo chegar.
- Crédito de extras de terceiros: "Fonte: X", pequeno, dentro da zona segura.

## Legenda no topo (`full`/`pilha` sem texto na tela, mas o close aperta a boca) — decisão de 27/10
Achado no V20/E13 (fecho emocional do Jensen, L16, RC-JH17): a linha "por cima, se a mídia não tiver texto" da
tabela acima existia só no papel — ninguém tinha implementado. O caso que forçou: um close de rosto em `full`
sem informação nenhuma na tela, mas o enquadramento necessário deixava a boca bem em cima da faixa normal da
legenda (y≈1150). Apertar o corte pra fugir dela **deformava a imagem** (zoom alto demais, cortando a testa na
linha dos óculos) — não é opção pro fecho emocional do vídeo. A solução certa é mover a LEGENDA, não apertar o
corte:
- **`legendaTopo: true` no overlay** (contrato em `docs/contratos.md`): a legenda sobe pra `LEGENDA.centroYTopo`
  (390, logo abaixo da zona segura de cima, com folga calculada pro pior caso — bloco de 2 linhas com palavra
  `destaque`, ~223 px) enquanto esse overlay está ativo, em vez de ficar embaixo brigando com o rosto.
- **Só pra mídia SEM texto próprio** — se o extra tem texto/número/diagrama na tela, o caso é outro: `denso`
  (legenda SOME, não sobe — ver "Legenda nunca compete com informação..." abaixo).
- Quem monta os overlays decide olhando o frame: se o enquadramento normal (sem zoom forçado) deixa a boca na
  faixa da legenda, marca `legendaTopo`; nunca aperta o corte pra "resolver" isso.
- **O véu escuro troca de lado junto com a legenda** (achado do portão-imagem v8, mesmo dia, IM-JH-L16): o `full`
  sempre desenhava um véu de BAIXO atrás da legenda normal (`LAYOUTS.enquadrado.veuBaixo`) — com `legendaTopo`
  isso escurecia o rosto à toa (nariz/boca/queixo), sem legenda ali pra justificar. Com `legendaTopo: true` o véu
  de CIMA entra no lugar (`veuTopo`, reforçado pra dar contraste de verdade atrás da legenda que subiu, inclusive
  a palavra ainda não dita em cinza).

## Imagem/vídeo retangular isolado (modo `solo`), sem outro elemento pra encaixar (decisão de 27/10)
Achado no Jensen Huang (E22 "cartão CUDA", E24 "cartão AlexNet", E23 "diagrama Serial×Parallel"): o `solo` atual é só
"imagem inteira sobre preto" — isso deixa tarja preta vazia em cima/embaixo (a imagem não é 9:16) e passa impressão
não profissional. Regra nova, **obrigatória sempre que não houver outro elemento pra preencher o layout**:
- **Nunca** deixar um retângulo isolado flutuando sobre preto liso. Ele tem que ficar **centralizado na tela**, com
  uma **moldura** (borda fina, estilo do design system) ao redor, e o espaço que sobra em volta preenchido pelo
  **fundo de marca** `00-marca/assets/fundos/grade-isometrica-escura.png` (1080×1920, grade isométrica escura) —
  nunca preto liso nem repetir a mesma imagem borrada de fundo.
- **"Centralizado na tela" = centralizado DENTRO DA ÁREA ÚTIL, com a legenda ABAIXO da caixa** (como o `card`) —
  **não** enviesado pro topo, e **não** no centro bruto da tela inteira (960 de 1920). Duas voltas no mesmo dia
  (27/10, sempre com screenshots do autor): 1.ª volta, achado no E17 "3 fundadores" — a caixa ficava enviesada
  pro topo (y≈284–1014), com um vazio enorme embaixo só com a legenda por cima; **2.ª volta, achado no CUDA** —
  centralizar na tela inteira (960) parecia resolver, mas uma caixa grande (até `alturaMax`=700) centralizada aí
  vai de y 625 a 1295, **estourando a zona segura de baixo** (`AREA_SEGURA.limiteY`=1250) e colidindo com a
  legenda ("Programming model" atrás de "Depois uma das"). A caixa centraliza dentro de `AREA_SEGURA.y` (270) até
  `AREA_SEGURA.limiteY − legendaReservada` (`LAYOUTS.solo.legendaReservada`, hoje 190 px) — essa faixa reservada
  no fim é onde a legenda mora (y≈1150, a mesma posição padrão: cai dentro da faixa reservada por construção, com
  folga mesmo numa legenda de 2 linhas de `destaque`). Caixa pequena (ex. E17) sobra mais espaço antes da
  legenda — é esperado, bate com as referências do autor (caixa ~700–1100 px de um quadro 974×1766, legenda
  abaixo, sem sobrepor), não é bug.
- **O Ken Burns do `solo` nunca pode fazer a caixa passar do encaixe máximo** (achado no E17, 27/10: o `scale()`
  aplicado na caixa JÁ no tamanho máximo crescia além da composição e o rótulo "CHRIS MALACHOWSKY" perdia o "C",
  cortado pela borda do vídeo — bug do motor, não da mídia). Como `solo` é sempre `contain` (uma das duas
  dimensões já fica rente ao limite, sem margem, por definição), o zoom tem que crescer a caixa de verdade
  (layout) a partir de um tamanho um pouco menor, encostando no limite só no último quadro — nunca um `transform`
  por cima de uma caixa que já está no tamanho máximo.
- Vale pro `solo` sempre, e pro `full` quando o cover-crop 9:16 não preenche o quadro (imagem mais larga que alta
  sobra tarja) — nesses casos trocar `full` por este tratamento centralizado.
- **Legenda nunca compete com informação que já está na imagem/vídeo** (achado no E23, diagrama Serial×Parallel: a
  legenda caiu em cima dos rótulos TASK/PROBLEM). Se o extra tem texto, número ou diagrama denso na tela, mover a
  legenda pra fora da área de conteúdo (ou segurar a legenda até o extra sair) — nunca sobrepor.
- **`area`/zoom não pode cortar logo ou texto na metade** (achado no E05: "NVIDIA" cortado pela borda do recorte
  9:16) nem deixar a imagem tremida pelo próprio zoom/pan (achado no E33, letreiro do Denny's). Se o enquadramento
  ideal corta o texto, prefira um corte mais largo ou troque de mídia.
- **Priorizar o personagem sobre o cenário genérico** quando falar de um lugar/objeto dele: se há material do
  Jensen (ou de quem for) falando/presente, preferir isso a um plano vazio do espaço (achado no E35, booth vazio do
  Denny's, sem impacto) ou a uma imagem escolhida só porque bate a palavra-chave no texto (achado no E33: o editor
  pegou "qualquer coisa com Denny's escrito", não o melhor plano). A escolha de mídia é por **impacto visual**, não
  por correspondência literal de palavra.

**Implementado** (`remotion/src/brand.ts`): `FUNDO_MARCA.isometrico` (a imagem, via symlink `remotion/public/_marca` →
`00-marca/assets`, criado pelo `gerar_props.py`) + `MOLDURA_ISOLADA` (borda/raio) + componente `FundoIsometrico.tsx`,
usados em `solo` (sempre) e em `full` sem `enquadrar` quando `h/w < LAYOUTS.full.proporcaoCobre` (sobra tarja). A
flag `denso: true` no overlay (contrato em `docs/contratos.md` §4) **some com a legenda** enquanto esse overlay
está ativo — testado no próprio E23 (diagrama Serial×Parallel, `full` + `enquadrar`): reposicionar não bastou
porque o cover-crop preenche o quadro inteiro e o diagrama tem rótulo em toda altura, sem faixa livre sobrando;
"segurar a legenda até o extra sair" garante nunca sobrepor. Quem monta os overlays (`produtor-de-extras`/
`montar_v2.py`) marca a flag olhando o frame.


## Nada sobre o rosto do autor (05/11)
Qualquer elemento por cima do vídeo dele (selo, ícone, número, barra de vidro, cartão, título) fica do queixo para baixo ou acima da cabeça — nunca no rosto. Medir o rosto real do take; detalhe em `00-marca/design-system/korvu-motion.md` §4 e `docs/decisoes.md` §3 (05/11).

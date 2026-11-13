# Decisões — o que fazer e o que não fazer

> **Leia isto antes de produzir qualquer coisa.** Cada linha é uma decisão de método, com o motivo. Se algo aqui
> contradiz o seu instinto, **vale isto**. Quando o autor decidir algo novo, acrescente uma linha **no mesmo dia**,
> com a data e o motivo — este arquivo é a memória do projeto e não pode depender de ninguém lembrar.
>
> As decisões abaixo vêm do estúdio original (set.–nov. 2026) e explicam por que o código é como é. Mude o que não
> servir para o seu estúdio — mas mude aqui primeiro, depois no código.
>
> Estado atual: `_controle/CONTINUAR.md` · Regras operacionais: `CLAUDE.md` · Formatos: `docs/contratos.md`

## 1. Roteiro

| Decisão | Por quê | Onde está |
|---|---|---|
| **Roteiro narrativo**: história com começo, meio e fim (gancho → contexto → desafio → virada → clímax → reflexão → CTA), escrita primeiro como texto corrido e só depois partida em linhas | roteiro picado em frases soltas soa lido e robótico | `00-marca/modelo-roteiro-narrativo.md`, `roteirista` |
| **Sem contagem de palavras nem teto de duração**: a duração é a que a história pedir | cortar a história para caber num número tirava justamente o que prendia | `roteirista`, `qa_check.py` (teto = limite da Meta) |
| **O roteiro tem SÓ o que se fala** (tabela `ID · Seção · FALA`). Nada de gesto, olhar, cenário | quem grava sabe se posicionar; instrução de palco polui a leitura | `roteiro-reels`, `parse_roteiro.py` |
| **Duas saídas, uma fonte**: `roteiro.md` técnico (IDs para o editor) e `roteiro-limpo.txt` para quem grava | os IDs servem à edição, não à pessoa | `parse_roteiro.py` |
| **Vídeo sobre uma pessoa** = quem é, de onde veio, o que fez → só então a notícia | o público vê a notícia mas não sabe quem é a pessoa | `roteirista` |
| **Números em algarismo** no roteiro e na leitura (1947, 50 anos, 15%) | lê-se mais rápido | `roteirista` |
| **Sem fórmula repetida entre vídeos** (aberturas, conectores, fechos iguais) — o `dramaturgo` passa depois do roteirista | o público percebe o molde e o vídeo ganha cara de IA | `dramaturgo`, `scripts/repeticoes_roteiro.py` |
| **CTA de palavra-chave falado, só no fim, palavra curta** (até ~6 letras), que entrega **um PDF** de no máximo 2 páginas, a entrega primeiro | palavra longa erra na digitação; PDF longo não é lido | `cta.md`, `produtor-de-material` |
| **Toda gravação abre com a pausa da capa** (3 s parado, olhando a câmera, pose diferente a cada vídeo) | a capa sai desse trecho, sem procurar quadro a quadro | `parse_roteiro.py`, `frame_candidates.py` |

## 2. Edição — o editor tem de entender como a pessoa fala

| Decisão | Por quê | Onde está |
|---|---|---|
| **Improviso é take válido**: o editor escolhe o take que mais encaixa na linha, aceitando a frase dita do jeito da pessoa | exigir a frase literal fazia a linha virar `faltando` e sumir do vídeo | `align.py` |
| **Vale o ÚLTIMO take** da linha | quem grava refaz até sair do jeito certo | `align.py` (`escolher`) |
| **Gagueira e palavra comida quase não penalizam**; o dicionário `fala-autor.json` ensina o que a transcrição ouve errado | punir tropeço escolhia sempre o take mais mecânico | `align.py`, `00-marca/fala-autor.json` |
| **Legenda vem do ROTEIRO**, não do que a transcrição ouviu; sem pontuação nem caractere especial | "prompt" virava "pronto" na legenda | `edl.py`, `gerar_props.py` |
| **Cortes disfarçados com zoom alternado** (1,00 ↔ 1,12, centrado no rosto), segurando ≥ 1 s | corte seco no mesmo enquadramento salta | `edl.py`, `render_corte.py` |
| **Nenhum take termina no meio de uma frase**; peça de fala nunca < 0,8 s | o render descartava a peça e a fala sumia sem aviso | `align.py`, `apertar_ritmo.py` |
| **Áudio fiel à câmera**: sem redução de ruído, compressão suave, −14 LUFS | o denoise deixava a voz abafada e "apertada" | `ingest.py`, `audio.py` |
| **Gravação com monitor de voz**: duas vozes no áudio, o editor corta só a do apresentador | ler um teleprompter trava; repetir o que se ouve soa natural | `locutores.py` |

## 3. Cenas extras e animação

| Decisão | Por quê | Onde está |
|---|---|---|
| **O formato do arquivo decide o layout**: deitado (16:9) → `split`, extra em cima e a pessoa embaixo; vertical → `full` | é o que encaixa sem tarja | `gerar_props.py` (`modo_pelo_formato`) |
| **Extras encostados = faixa contínua com corte seco**, sem "sobe e desce" do split | o vaivém cansa | `scripts/extras_continuos.py`, `Reel.tsx` |
| **Toda imagem em movimento** (Ken Burns / zoom) e créditos na descrição do post, não na tela | imagem parada derruba a retenção | `gerar_props.py` |
| **Vídeo é melhor que foto** nas cenas extras; vídeo sobre uma pessoa mostra a pessoa | foto não dá credibilidade | `pesquisador-de-material` |
| **Nada sobre o rosto**: todo elemento por cima fica do queixo para baixo ou acima da cabeça | texto no rosto foi o defeito mais reprovado | `render_capa.py`, `korvu-motion.md` |
| **A ferramenta de que o vídeo fala pode aparecer com a cara dela** (interface, logo), sem sugerir parceria | o público reconhece na hora | `CLAUDE.md` regra 3 |
| **Todo motion leva efeito sonoro**, suave, embaixo da voz | movimento mudo parece inacabado | `00-marca/som/sound-design.md` |

## 4. Imagem e cor

| Decisão | Por quê | Onde está |
|---|---|---|
| **Cor por fonte, nunca global**, corrigindo o mínimo, com alvo na mediana dos arquivos bons | a câmera divide a gravação em arquivos com cor diferente; o ajuste global criou um degrau | `cor_pele_casada.py`, regra 11 |
| **Gravação de tela não recebe LUT** | o LUT é para a imagem da câmera | `aplicar_cor.py`, regra 8 |
| **Capa = quadro parado do próprio vídeo** (boca fechada, sem mão em movimento), uma capa por variante, refeita quando a cor muda | capa tirada da cor velha foi para a fila | `capa-reels`, PORTÃO-IMAGEM |
| **PDF editorial curto**, sem nome pessoal (autoria = a marca) | o material é da marca, não da pessoa | `korvu-editorial.md`, `gerar_material_pdf.py` |

## 5. Organização e entrega

| Decisão | Por quê | Onde está |
|---|---|---|
| **GAUNTLET: quem faz não aprova** — cada área tem um portão que audita antes de chegar ao autor | "corrigido" sem estar e capa errada na fila chegaram ao autor por auto-relato | `docs/gauntlet.md`, `scripts/portoes.py` |
| **Mover para `06-publicar/` = autorização para publicar**; os primeiros posts pedem confirmação | uma parada humana clara antes de ir ao ar | `publicar.py`, regra 2 |
| **Publicar sempre IG + FB** com o mesmo vídeo; variantes de hook vão como Trial Reel | uma versão normal por vídeo, o resto testa sem queimar o perfil | `publicador`, `calendario.md` |
| **Sem servidor**: launchd consulta a Meta (comentários, métricas) em vez de webhook | webhook exige endereço público ligado 24 h | `automacao-meta/ARQUITETURA.md` |
| **Automação de comentários só entrega o material** (resposta + direct com o PDF); nada de conversa ou CRM | o objetivo é entregar o que foi prometido no vídeo | `responder_comentarios.py` |
| **Uma revisão por vez**: cada render novo apaga o anterior | pasta cheia de rascunhos confunde quem vem depois | `scripts/limpar_video.py` |
| **Métricas aos 5 dias alimentam o roteirista**; vídeo muito acima da média vira série no mesmo ângulo | o que funcionou tem de voltar para o próximo roteiro | `metricas.py`, `analista-de-metricas`, `acertos.py` |
| **O painel e o índice de contexto só leem** os arquivos; o banco é derivado e pode ser refeito | os arquivos são a fonte da verdade | `painel/sync/`, `estudio-contexto/` |
| **Toda sessão deixa uma entrada no `HANDOFF.md`** e atualiza o `_controle/CONTINUAR.md` | várias sessões em paralelo perdiam o fio | `docs/handoff-modelo.md` |

## 6. O que NÃO fazer

- Não definir o público por país ou por língua.
- Não prometer no CTA material que não existe em `videos/<slug>/material/`.
- Não renderizar o final sem a EDL aprovada; não publicar fora da fila.
- Não dizer "corrigido" sem olhar o quadro ou o número onde estava o defeito (regra 10).
- Não converter o projeto para 30 fps.
- Não versionar `.env`, vídeos, dados de quem comentou ou métricas reais.

## 7. Decisões do seu estúdio

| Data | Decisão | Por quê | Onde está |
|---|---|---|---|
| | | | |

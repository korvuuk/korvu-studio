# Sound design da Korvu

> **Decisão do autor, 05/11:** "temos que usar o som, transição, efeito sonoro para dar mais vida ao motion…
> precisamos ter sound design no projeto". Vale para TODA animação e transição (série AI Engineer primeiro, e
> depois as cenas extras dos outros vídeos). A música de fundo continua com o `produtor-musical` (`/musica`).
> Este arquivo cobre os **efeitos**.

## Regras
1. **Todo movimento que importa tem som**: entrada de cena (whoosh), elemento que nasce (pop), clique, texto
   digitado, documento cortado, número que conta (ticks), virada (riser → impacto), resposta certa (brilho),
   erro, ligação entre dois pontos (conectar).
2. **O som cai no frame do movimento**, não "mais ou menos perto": cada efeito é colocado no mesmo frame em
   que a peça começa a se mover (lista `SONS` no componente do Remotion).
3. **O som fica embaixo da voz.** Efeitos são tempero: volume 0,4–0,9 no Remotion, e no master a voz manda
   (−14 LUFS do vídeo inteiro pelo `audio.py`). Nada de efeito que cubra uma palavra.
4. **Pouco e limpo**: o mesmo efeito para o mesmo gesto em toda a série (o pop é sempre o mesmo pop), para criar
   reconhecimento. Nada de som de desenho animado.
5. **Sem som em loop contínuo** além da música.

## Biblioteca
- Catálogo (nome, uso, descrição): `00-marca/som/sfx.json`.
- Arquivos: `remotion/public/_marca/sfx/<nome>.mp3` (ElevenLabs) ou `.wav` (sintético, reserva). No Remotion:
  `staticFile("_marca/sfx/<nome>.mp3")`.
- Gerar com a ElevenLabs Sound Effects: `uv run python scripts/gerar_sfx.py` (só os que faltam;
  `--refazer <nome>` para trocar um).
- Reserva sem API: `uv run python scripts/sfx_sintetico.py` (sintetizados com numpy, mesmos nomes).

**Estilo: cinematográfico e suave** (Autor, 05/11): ar, reverb quente, cauda longa, nada seco nem de desenho animado. As descrições do `sfx.json` seguem essa linha; o `gerar_sfx.py` iguala o pico de todos em −3 dBFS.

**Estado em 05/11 (noite):** chave nova da ElevenLabs ativa; os 13 efeitos são da ElevenLabs (`.mp3`). A chave não tem a permissão `user_read`; para gerar efeitos isso não importa.

---
description: Um vídeo foi muito acima da média? Descobre o DNA do acerto e traz uma série de ideias parecidas para o banco
argument-hint: [slug do vídeo — vazio = todos os acertos pendentes]
---

1. `uv run python scripts/acertos.py --pendentes` (recalcula a partir de `07-publicados/*/metricas.json`).
   Se "$ARGUMENTS" tiver um slug, trabalhar nele mesmo que não esteja na lista.
2. Se `_controle/aprendizados.md` estiver mais velho que a leitura do vídeo, rodar antes o **analista-de-metricas**
   (ele atualiza os aprendizados que o multiplicador lê).
3. Para cada acerto (o de maior força primeiro): subagente **multiplicador-de-acertos**.
4. Assim que ele terminar, **portao-pauta** sobre a série (sem perguntar). BLOQUEADO → volta ao multiplicador (até 3 voltas).
5. Mostrar ao autor: o DNA do acerto em poucas linhas, as 3 melhores ideias da série (pontos, tema, hook) e
   perguntar qual vira `/novo-video`.

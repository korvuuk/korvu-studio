# Etiquetas sugeridas

Crie no GitHub em **Issues → Labels** (ou com `gh label create <nome> --color <cor> --description "<descrição>"`).

| Etiqueta | Cor | Para quê |
|---|---|---|
| `good first issue` | `7057ff` | boa para a primeira contribuição: pequena, bem descrita, sem mexer em várias áreas |
| `help wanted` | `008672` | a gente quer ajuda de fora nisto |
| `erro` | `d73a4a` | algo não funciona como a documentação diz |
| `melhoria` | `a2eeef` | ideia nova ou ajuste |
| `pergunta` | `d876e3` | dúvida de uso |
| `documentação` | `0075ca` | docs, README, volumes em `docs/` |
| `triagem` | `ededed` | ainda não foi olhada |
| `S0` | `b60205` | vai ao ar errado (publica coisa errada, vaza dado) |
| `S1` | `e99695` | quebra o fluxo ou a confiança |
| `S2` | `fbca04` | melhoria, pode esperar |
| `área: roteiro` | `c5def5` | roteirista, dramaturgo, roteiro-reels, PDF |
| `área: edição` | `c5def5` | corte-por-roteiro, áudio, legendas |
| `área: imagem` | `c5def5` | cor, capa, extras, animação, Remotion |
| `área: publicação` | `c5def5` | publicar.py, comentários, métricas, API da Meta |
| `área: painel` | `c5def5` | painel web, banco, sincronizador |
| `área: contexto` | `c5def5` | estudio-contexto (grafo, busca, MCP) |

Para criar todas de uma vez (com o `gh` autenticado, dentro do repositório):

```bash
while IFS='|' read -r _ nome cor desc _; do
  nome=$(echo "$nome" | sed 's/^ *`//;s/` *$//'); cor=$(echo "$cor" | tr -d ' `'); desc=$(echo "$desc" | sed 's/^ *//;s/ *$//')
  [ -n "$nome" ] && [ "$nome" != "Etiqueta" ] && [ "$nome" != "---" ] && gh label create "$nome" --color "$cor" --description "$desc" --force
done < <(grep '^| `' .github/labels.md)
```

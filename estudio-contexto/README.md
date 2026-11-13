# estudio-contexto

Camada de **contexto** do estúdio Korvu Studio: grafo de entidades (projetos, agentes, vídeos, portões, veredictos,
decisões, documentos) + busca híbrida local (vetorial + texto + grafo) + servidor MCP **somente leitura** para os
agentes. Especificação aprovada: [`ESPECIFICACAO.md`](ESPECIFICACAO.md). Construído em 12/11/2026.

Os **arquivos continuam sendo a fonte da verdade**. O índice e o grafo são derivados, ficam num schema próprio
(`contexto`) no Postgres local do painel e podem ser apagados e refeitos do zero a qualquer momento.

## Usar

```bash
cd estudio-contexto
uv run python -m contexto.sincronizar          # migra, indexa (incremental) e recalcula o grafo — ~15 s sem mudanças
uv run python -m contexto.sincronizar --grafo  # só o grafo (não reembeda)
uv run pytest -q -p no:cacheprovider           # testes (banco descartável; precisa do Postgres do painel ligado)
uv run python avaliacao/avaliar.py --relatorio avaliacao/resultado.md   # avaliação (perguntas em avaliacao/perguntas.yaml)
```

Precisa do Postgres do painel no ar (`bash painel/iniciar.sh`, 127.0.0.1:55322). O modelo de embedding
(`intfloat/multilingual-e5-small`, ~470 MB) fica no cache do Hugging Face; o servidor MCP roda com
`HF_HUB_OFFLINE=1`, sem rede.

**Sincronização automática:** launchd `uk.korvu.contexto` roda o sincronizador a cada 30 min e ao entrar na sessão
(prioridade baixa, sem rede). Instalar/reinstalar: `bash estudio-contexto/launchd/instalar.sh`; desligar:
`bash estudio-contexto/launchd/desinstalar.sh`; forçar agora: `launchctl kickstart -k gui/$(id -u)/uk.korvu.contexto`.
Log: `estudio-contexto/logs/contexto.log`. Se o Postgres do painel estiver desligado, a passagem registra uma linha e
tenta de novo na seguinte.
A busca devolve `indice_atualizado_em` para o agente saber a idade do índice.

## Ferramentas do MCP (`.mcp.json` da raiz → `estudio-contexto`)

| Ferramenta | Para quê |
|---|---|
| `contexto_do_projeto(projeto)` | área, pastas, dependências, agentes, documentos principais, decisões |
| `contexto_do_video(slug)` | estado, portões, veredictos (com o relatório), decisões, publicação e métricas |
| `buscar(consulta, projeto?, tipo?, limite?, agente?, desde?, ate?)` | trechos com caminho, seção, data e nós ligados |
| `vizinhos(no, profundidade?)` | nós e arestas ao redor (`video:…`, `agente:…`, `decisao:PD9`, ou só o nome) |
| `decisoes_sobre(tema)` | decisões do `docs/decisoes.md` e códigos PD do backlog, com data, motivo e onde estão |
| `quem_fiscaliza(agente)` | portão que fiscaliza o agente e os veredictos recentes |

Consultam: o diretor (sessão principal, `CLAUDE.md` › Ferramentas), `roteirista` e `portao-dados`.

## Como funciona

| Peça | Arquivo |
|---|---|
| Mapa dos projetos | `projetos.yaml` |
| Lista explícita do corpus | `corpus.yaml` |
| Schema `contexto` (nós, arestas, documentos, trechos com `vector(384)` + HNSW + `tsvector`) | `migrations/001_schema_contexto.sql` |
| Exclusões fixas (segredos, mídia), detector de token, máscara de identificadores | `contexto/seguranca.py` |
| Chunking (markdown por `##`, YAML/JSON por item, linha longa de tabela = 1 trecho) | `contexto/chunking.py` |
| Grafo (lê `public.*` do painel em transação só-leitura) | `contexto/grafo.py` |
| Indexação incremental (hash do arquivo + hash do trecho) | `contexto/indexar.py` |
| Busca: vetorial + textual + entidades + datas, RRF (k = 60) com o 1.º de cada lista garantido | `contexto/busca.py` |
| Ferramentas e servidor (FastMCP, papel `contexto_leitor`) | `contexto/consultas.py`, `contexto/servidor.py` |

Segurança: o módulo **não lê o `.env`**; `.env*`, mídia e pastas de vendor ficam fora por regra fixa; arquivo com
padrão de token é recusado inteiro; identificadores de conta (URN do LinkedIn, nome de bucket R2, ids numéricos de
conta) são mascarados antes de indexar. O servidor MCP abre a conexão só-leitura e baixa para `contexto_leitor`
(só `SELECT` no schema `contexto`, nada no `public` do painel). `tests/test_seguranca.py` confere no índice real que
nenhum valor do `.env` aparece (lê as chaves sem imprimir os valores).

## Avaliação (§9)

No estúdio original, com 30 perguntas tiradas dos próprios vídeos: Recall@5 0,96 e 80 % de respostas corretas.
O `avaliacao/perguntas.yaml` deste repositório é um exemplo curto — troque pelas perguntas do seu estúdio. Ajustes feitos, na ordem pedida pela especificação (chunking e grafo antes de
trocar o modelo): limite de trecho 1800 → 1100, decisão longa = trecho próprio, versão do chunking no hash,
palavras de pergunta fora da busca textual, datas da pergunta como lista do RRF, 1.º lugar de cada lista garantido.

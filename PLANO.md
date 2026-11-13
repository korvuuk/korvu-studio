# Plano da extração — Korvu Studio

Como este repositório foi montado a partir do estúdio privado (12/11/2026). **Cópia de arquivos, nunca clone:** o
histórico do repositório privado tem dados pessoais, então este começa com histórico zero.

## O que entrou

| Pasta | O que é | Limpeza feita |
|---|---|---|
| `.claude/agents/` (29), `.claude/commands/` (20) | a equipe e os comandos | nome do autor → "o autor"; conta → `@sua_conta`; área pessoal e outro projeto do autor tirados |
| `.claude/skills/` (10 próprias) | roteiro, corte, cor, legendas, capa, áudio, QA, animação, tela, gerar imagem | caminhos `/Users/…` → `ffmpeg` do PATH |
| `skills-lock.json` | as skills de terceiros (Remotion, Supabase, `watch`, `apple-design`) **por referência** | não copiadas |
| `scripts/` | publicação, comentários, métricas, portões, PDF, carrossel… | e-mail, conta, domínio e fuso → `.env` (`CONTA_INSTAGRAM`, `TZ_PUBLICACAO`) |
| `remotion/` | composições do Reel | sem `node_modules`, `out/`, renders e a gravação de demonstração |
| `painel/` | painel web + Supabase + sincronizador + design | sem `node_modules`, `.next*`, `trabalho/`, `previas/`, `portoes/`, referências e retratos da equipe; conta e fuso configuráveis (`painel/web/src/lib/estudio.ts`); `project_id` próprio |
| `automacao-meta/` | arquitetura e configuração do app da Meta | URL de webhook antigo e caminho do Mac tirados |
| `estudio-contexto/` | grafo + busca + MCP só leitura | sem índice, logs e relatórios; perguntas de avaliação trocadas por um exemplo |
| `docs/` | contratos, GAUNTLET, decisões (genéricas), os dois volumes da documentação | volumes movidos para `docs/estudio/` e `docs/painel/`, regerados pelos geradores, com links entre si |
| `00-marca/` | só o método: modelo de roteiro, tom, hooks, CTA, público, pilares, layouts, design system, cor (LUTs), som, regras legais | sem amostras de voz, fotos, referências de filmes, logos de terceiros; `voz-autor.md` e `fala-autor.json` são modelos vazios |
| `tests/` | suítes sem mídia | fixtures fictícias no lugar do roteiro, do calendário e do carrossel reais |
| `exemplos/` | estúdio de demonstração fictício + `seed.sql` do painel | tudo inventado |

## O que ficou fora

`videos/`, `05-render-pronto/`, `06-publicar/`, `07-publicados/`, `_controle/`, `01-ideias/`, `02-calibracao/`,
`carrosseis/` reais, `BG VIDEO/`, `transcricoes.json`, `linkedin/` (pessoal), `ai-engineer/` (biblioteca de estudo
pessoal), `HANDOFF.md`, `_controle/CONTINUAR.md`, o `docs/decisoes.md` original (virou a versão genérica),
`.env`, `.mcp.json` original (caminhos locais), toda mídia bruta, o perfil e o dicionário de voz do autor,
`sobre-autor.md`, `referencias-criadores.md`, `00-marca/cor/{amostras,analises,referencias}`, `assets/logo` e
`assets/logos-terceiros`, efeitos sonoros gerados (`*.mp3`), `painel/web/public/equipe/` (origem das fotos a confirmar),
`scripts/linkedin.py` e o job `uk.korvu.linkedin` (dependem da pasta pessoal `linkedin/`), `scripts/limpeza/`, a
pasta `painel/design/telas/` inteira (maquetes e especificações por tela tinham números reais do perfil, consumo de
IA, temas de vídeos não publicados, quadros do rosto do autor e os retratos da equipe; o design system, os tokens e
os componentes ficam).

O `.gitignore` deixa fora do git as pastas de dados de quem usar o estúdio (`videos/`, `_controle/`, `06-publicar/`…).

## Verificação

- `python3 -I scripts/varrer_privacidade.py` limpo (também roda no CI, com o gitleaks).
- Testes sem mídia verdes na cópia (portões, publicação, métricas, comentários, CTA, cor, prévias dos looks).
- Painel aberto com o `seed.sql` de demonstração numa instância separada; telas fotografadas (`exemplos/capturas/`).
- Auditoria do `portao-dados` (privacidade, segredos, testes) e do `portao-interface` (README e docs).

## Resíduos conhecidos (S2)

- Identificadores de código usam `apresentador` (locutor da gravação) e `autor` (quem decide): `decisao_autor`,
  `locutor: apresentador`. Os valores com o nome antigo não são lidos.
- A documentação e alguns comentários citam slugs de vídeos já publicados do estúdio original como exemplo histórico.
- As capturas de `docs/painel/` mostram o painel do estúdio original (liberadas pelo autor "como estão" em 12/11);
  a vitrine do README usa as capturas da demo.
- Alguns agentes ainda citam `ai-engineer/` e o LinkedIn pessoal (áreas que ficaram fora); são instruções sem efeito.
- Agentes, comentários e o Volume 2 ainda citam `painel/design/telas/` (saiu do repositório; o `painel/design/README.md` explica).
- `painel/tests/test_biblioteca_yaml.py` confere o `biblioteca.yaml` contra a maquete da Biblioteca e os vídeos do SEU
  estúdio: sem a maquete, é pulado; não roda no CI.
- O Volume 2 (`docs/painel/`) ainda cita, no "Instalar", o `@` fixo e os retratos de `web/public/equipe/`; na cópia a
  conta já vem de `NEXT_PUBLIC_CONTA_INSTAGRAM` e, sem retrato, o painel mostra as iniciais.

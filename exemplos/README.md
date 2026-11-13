# Demonstração do painel (dados fictícios)

Tudo aqui é inventado: quatro vídeos de IA para iniciantes, os portões de cada um, uma publicação com métricas,
leituras do perfil de uma conta `@korvu_demo` e registros sintéticos do Claude Code. Serve para clonar o repositório e
ver o painel com conteúdo.

| Pasta / arquivo | O que é |
|---|---|
| `estudio-demo/` | raiz de projeto fictícia (`PAINEL_PROJETO`): `videos/`, `05-render-pronto/`, `06-publicar/`, `07-publicados/`, `_controle/`. Empresta do repositório, por links simbólicos relativos, `.claude/`, `00-marca/`, `remotion/`, `scripts/` e, dentro de `painel/`, `equipe.yaml`, `cambio.yaml`, `web/` e `supabase/`. O `painel/biblioteca.yaml` é próprio (os exemplos de capa apontam para os pacotes da demo). |
| `registros-demo/` | registros `.jsonl` fictícios do Claude Code (`PAINEL_REGISTROS`) — a tela de tokens e custos. |
| `gerar_demo.py` | recria as duas pastas do zero, sempre igual para a mesma data-base. |
| `gerar_seed.sh` | sincroniza a demo num banco de teste e grava `painel/supabase/seed.sql` (só dados do schema `public`). |
| `capturas/` | três telas do painel com a demo carregada (1440 px). |

Os quatro vídeos: `…-resumir-reunioes` (publicado, com métricas), `…-planilha-com-ia` (agendado em `06-publicar/`),
`…-prompt-claro` (gravado, em edição, capa BLOQUEADA no portão da imagem) e `…-ia-no-atendimento` (roteiro aprovado).
Nenhuma mídia pesada: as capas são PNG lisos gerados pelo script, o PDF da palavra-chave é de uma página só e as
gravações entram pelo manifesto `brutos/principal/ARQUIVADO.json` (originais "arquivados fora do Mac").

![Visão geral](capturas/inicio-1440.png)
![Produção de conteúdo](capturas/producao-1440.png)
![Desempenho](capturas/desempenho-1440.png)

## Ver o painel com a demo (o jeito rápido)

O `painel/supabase/config.toml` já carrega `painel/supabase/seed.sql` no reset:

```bash
docker network create -o com.docker.network.bridge.host_binding_ipv4=127.0.0.1 \
  supabase_network_korvu-studio-painel   # portas só em 127.0.0.1 (como o painel/so-no-mac.sh)
cd painel && supabase start
supabase db reset                       # aplica as migrações e carrega o seed.sql (APAGA o que houver no banco)
supabase status                         # API URL e service_role key
```

`painel/web/.env.local`:

```bash
SUPABASE_URL=http://127.0.0.1:55321
SUPABASE_SERVICE_ROLE_KEY=<service_role key do supabase status>
NEXT_PUBLIC_CONTA_INSTAGRAM=@korvu_demo
NEXT_PUBLIC_TZ_PUBLICACAO=America/Sao_Paulo
PAINEL_PROJETO=<caminho absoluto do repositório>/exemplos/estudio-demo   # as capas saem daqui
```

```bash
cd painel/web && npm ci && npx next dev -p 3456
```

**Não rode o sincronizador apontando para a raiz do repositório depois do reset** (nem o `bash painel/iniciar.sh`,
que sincroniza a raiz e lê os registros do Claude Code da sua máquina) — ele regrava o banco com o que achar lá. Para ressincronizar a demo, use o comando abaixo, com as duas variáveis apontando para `exemplos/`.

## Recriar a demo e o seed

```bash
uv run python exemplos/gerar_demo.py                     # data-base 2026-11-12
uv run python exemplos/gerar_demo.py --hoje 2027-03-01   # outra data-base (slugs, datas e janelas andam junto)
```

As telas contam "últimos 30 dias" a partir de hoje. Se a demo parecer vazia (tokens zerados, publicação "há meses"),
gere de novo com `--hoje` na data de hoje e sincronize:

```bash
PAINEL_PROJETO="$PWD/exemplos/estudio-demo" PAINEL_REGISTROS="$PWD/exemplos/registros-demo" \
PAINEL_DB_URL=postgresql://postgres:postgres@127.0.0.1:55322/postgres \
  uv run python painel/sync/sincronizar.py
```

**Sempre** passe `PAINEL_REGISTROS`: sem ele o sincronizador lê os registros reais do Claude Code da sua máquina
(`~/.claude/projects/…`) e o consumo de verdade vai para o banco.

Para gravar um `seed.sql` novo, use uma instância Supabase **separada** (outro `project_id`, outras portas), com as
migrações aplicadas, e:

```bash
bash exemplos/gerar_seed.sh <contêiner do Postgres> <URL do Postgres>
# ex.: bash exemplos/gerar_seed.sh supabase_db_korvu-studio-demo postgresql://postgres:postgres@127.0.0.1:55622/postgres
```

O script recria a demo, esvazia o histórico de passagens, sincroniza, faz o `pg_dump --data-only --schema=public
--inserts --no-owner --no-privileges` pelo `docker exec`, embrulha numa transação (as FKs entre `departamentos` e
`agentes` são circulares e conferidas no commit) e recusa o resultado se o grep de privacidade achar algo.

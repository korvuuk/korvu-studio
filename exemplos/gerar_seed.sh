#!/usr/bin/env bash
# Gera painel/supabase/seed.sql (só dados do schema public) a partir da demo fictícia.
#
#   bash exemplos/gerar_seed.sh <contêiner do Postgres demo> <URL do Postgres demo>
#   ex.: bash exemplos/gerar_seed.sh supabase_db_korvu-studio-demo postgresql://postgres:postgres@127.0.0.1:55622/postgres
#
# Use SEMPRE uma instância Supabase separada, já com as migrações aplicadas (exemplos/README.md): o sincronizador
# REGRAVA as tabelas do banco que recebe. Recusa a porta 55322 (a do painel de quem usa o estúdio de verdade).
set -euo pipefail
[ $# -eq 2 ] || { sed -n 2,7p "$0" >&2; exit 2; }
CONTEINER=$1 URL=$2
case "$URL" in *:55322/*) echo "✗ 55322 é a porta do painel de uso real — use a instância demo" >&2; exit 2 ;; esac
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEED="$RAIZ/painel/supabase/seed.sql"
cd "$RAIZ"

uv run python exemplos/gerar_demo.py
# o histórico de passagens não é espelho dos arquivos (o sincronizador só acrescenta): a demo leva uma passagem só
docker exec "$CONTEINER" psql -U postgres -d postgres -qc "truncate public.sincronizacoes" >/dev/null
PAINEL_PROJETO="$RAIZ/exemplos/estudio-demo" PAINEL_REGISTROS="$RAIZ/exemplos/registros-demo" PAINEL_DB_URL="$URL" \
  uv run python painel/sync/sincronizar.py | tail -1

TMP=$(mktemp)
docker exec "$CONTEINER" pg_dump -U postgres -d postgres --data-only --schema=public --inserts --no-owner \
  --no-privileges 2>/dev/null >"$TMP"
{
  echo "-- Dados FICTÍCIOS de demonstração do painel (exemplos/estudio-demo + exemplos/registros-demo)."
  echo "-- Gerado por exemplos/gerar_seed.sh — não editar à mão. Carregado pelo \`supabase db reset\`."
  echo "-- Uma transação só: departamentos ↔ agentes têm FKs circulares (deferrable initially deferred)."
  echo "BEGIN;"
  grep -vE '^\\(un)?restrict ' "$TMP"   # meta-comandos do psql 17.6+: o CLI do Supabase não os entende
  echo "COMMIT;"
} >"$SEED"
rm -f "$TMP"

# privacidade: nada de nome, conta, caminho de máquina, e-mail, número longo ou slug dos vídeos reais
if grep -nE '/Users/|/private/|/home/|@gmail|[0-9]{15,}' "$SEED"; then
  echo "✗ o seed.sql tem dado que não devia (linhas acima)" >&2; exit 1
fi
echo "✓ $(grep -c '^INSERT' "$SEED") INSERTs em painel/supabase/seed.sql — grep de privacidade limpo"

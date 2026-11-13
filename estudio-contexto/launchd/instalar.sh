#!/bin/bash
# Instala o agendador do contexto do estúdio (launchd, usuário atual):
#   uk.korvu.contexto → python -m contexto.sincronizar, a cada 30 min + ao entrar
# Fica dentro de estudio-contexto/ (não mexe em scripts/launchd/ do estúdio). Log: estudio-contexto/logs/contexto.log
#   bash estudio-contexto/launchd/instalar.sh
#   bash estudio-contexto/launchd/instalar.sh --so-gerar X   → só gera o plist final em X (não instala)
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
MODULO="$(cd "$DIR/.." && pwd)"
PROJETO="$(cd "$MODULO/.." && pwd)"
LABEL=uk.korvu.contexto
UV="${UV_BIN:-$(command -v uv || true)}"
[ -z "$UV" ] && [ -x /opt/homebrew/bin/uv ] && UV=/opt/homebrew/bin/uv
if [ -z "$UV" ] || [ ! -x "$UV" ]; then
  echo "uv não encontrado. Defina UV_BIN=/caminho/para/uv" >&2
  exit 1
fi

gerar() {  # gerar <saida>
  sed -e "s|__UV__|$UV|g" -e "s|__PROJETO__|$PROJETO|g" -e "s|__HOME__|$HOME|g" \
      "$DIR/$LABEL.plist" > "$1"
  plutil -lint "$1" >/dev/null
}

if [ "${1:-}" = "--so-gerar" ]; then
  gerar "${2:?indique o arquivo de saída}"
  echo "Gerado: $2"
  exit 0
fi

mkdir -p "$MODULO/logs" "$HOME/Library/LaunchAgents"
DESTINO="$HOME/Library/LaunchAgents/$LABEL.plist"
gerar "$DESTINO"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$DESTINO"
launchctl enable "gui/$(id -u)/$LABEL"
echo "✓ Instalado: $DESTINO"
echo "  Forçar uma execução agora: launchctl kickstart -k gui/$(id -u)/$LABEL"
echo "  Log: estudio-contexto/logs/contexto.log"

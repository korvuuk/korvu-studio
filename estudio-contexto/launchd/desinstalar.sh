#!/bin/bash
# Desliga e remove o agendador do contexto do estúdio. O índice continua no banco; rodar à mão volta a ser o caminho.
set -euo pipefail
LABEL=uk.korvu.contexto
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
echo "✓ Removido: $LABEL"

# AGENTS.md — para assistentes de IA que trabalham neste repositório

Vale para qualquer agente de código (Claude Code, Codex, Cursor, Copilot…). O Claude Code também lê o
[`CLAUDE.md`](CLAUDE.md), que tem as regras completas do estúdio; aqui está o essencial.

## O projeto em uma frase
Estúdio de produção de Reels com IA: agentes (`.claude/agents/`) e scripts Python (`scripts/`, `.claude/skills/*/scripts/`)
levam um vídeo do tema à publicação no Instagram e no Facebook; portões auditam cada etapa; um painel web
(`painel/`) mostra tudo e só lê os arquivos.

## Como rodar
- Python: sempre `uv run python <script>` (Python 3.12). Dependências em `pyproject.toml`.
- Testes sem mídia e sem rede: lista em [`CONTRIBUTING.md`](CONTRIBUTING.md#rodar-os-testes).
- Remotion: `cd remotion && npm ci && npx tsc --noEmit`. Painel: `cd painel/web && npm ci && npx tsc --noEmit && npm run lint`.
- Dados para experimentar: `exemplos/estudio-demo/` (fictícios).

## Regras que não se negociam
1. **Português do Brasil** em código, mensagens, comentários e docs ("você", nunca "tu").
2. **Nada de dado real**: nenhum token, e-mail, @ de conta, ID da Meta, nome de quem comentou, caminho `/Users/<nome>/`.
   Antes de terminar: `python3 -I scripts/varrer_privacidade.py`.
3. **Não leia nem imprima `.env`.** Segredos só por variável de ambiente.
4. **Formatos de arquivo** seguem [`docs/contratos.md`](docs/contratos.md); campo novo = contrato atualizado junto.
5. **25 fps** sempre. Saída final 1080×1920 H.264, −14 LUFS.
6. **Nunca publique de verdade** nem chame a API da Meta fora dos testes simulados (`--dry-run`).
7. **Confira no ponto do defeito**: compilar não prova que roda. Olhe o quadro, o número ou a tela onde o problema
   apareceu antes de dizer que está corrigido (regra 10 do `CLAUDE.md`).
8. **Quem faz não aprova** ([`docs/gauntlet.md`](docs/gauntlet.md)): mudou uma área, peça a revisão do portão dela.
9. O painel e o `estudio-contexto` **só leem** os arquivos do projeto. Banco muda só por migração nova em
   `painel/supabase/migrations/` (nunca edite uma antiga), com RLS ligada.

## Onde está o quê
| Preciso de… | Vá em |
|---|---|
| Entender o pipeline e as integrações | `docs/estudio/README.md` |
| Entender o painel e o banco | `docs/painel/README.md`, `painel/README.md` |
| Saber por que algo é assim | `docs/decisoes.md` |
| Formato de um JSON | `docs/contratos.md` |
| O que um agente faz | `.claude/agents/<nome>.md` |

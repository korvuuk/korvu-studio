# HANDOFF — diário das sessões (modelo)

> Copie para `HANDOFF.md` na raiz (fica fora do git: é o diário do SEU estúdio).
> **Toda sessão nova lê as 3 entradas do topo**, depois `docs/decisoes.md` e `_controle/CONTINUAR.md`.
> **Toda sessão, ao terminar (ou a cada entrega importante), acrescenta uma entrada NO TOPO**, sem apagar as antigas.

| Arquivo | Para que serve |
|---|---|
| `HANDOFF.md` | **o diário**: o que cada sessão fez, em que arquivos, branch/commit, o que ficou pendente |
| `_controle/CONTINUAR.md` | **o estado atual**: onde cada vídeo/automação está e o próximo passo |
| `docs/decisoes.md` | **as regras do autor**, com data e motivo; vale mais que o instinto de quem trabalha |

## Modelo de entrada

```markdown
## AAAA-MM-DD — <assunto curto>
- **Branch / commit:** `main` @ `<hash curto>` (ou "sem commit")
- **Pedido do autor:** <uma ou duas frases, nas palavras dele quando der>
- **Feito:** <o que mudou, com os arquivos>
- **Verificado:** <teste/comando e o resultado; "não verificado" se for o caso>
- **Decisões novas:** <linha adicionada em docs/decisoes.md, ou "nenhuma">
- **Pendente / próximo passo:** <o que falta e de quem depende>
- **Não mexer:** <pastas/arquivos que outra sessão está usando, se houver>
```

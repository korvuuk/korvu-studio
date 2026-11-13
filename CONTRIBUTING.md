# Como contribuir

Obrigado por querer melhorar o Korvu Studio. Toda ajuda conta: corrigir um erro de digitação, relatar um bug, melhorar
um agente, escrever um teste, traduzir a documentação.

## O caminho de uma contribuição

1. **Abra uma issue antes** se a mudança for grande (agente novo, etapa nova do pipeline, mudança de formato de
   arquivo). Para correções pequenas, pode ir direto ao pull request.
2. **Faça um fork** do repositório no GitHub (botão *Fork*) e clone o seu fork:
   ```bash
   git clone https://github.com/<seu-usuario>/korvu-studio.git
   cd korvu-studio
   ```
3. **Crie um branch** com um nome que diga o que ele faz:
   ```bash
   git checkout -b corrige-legenda-com-acento
   ```
4. Faça a mudança, **rode os testes** (abaixo) e a **varredura de privacidade**.
5. **Commit** com mensagem em português, no imperativo, dizendo o quê e por quê:
   `Corrige legenda que perdia o acento no fim da linha`.
6. **Envie e abra o pull request**:
   ```bash
   git push origin corrige-legenda-com-acento
   ```
   No GitHub, clique em *Compare & pull request* e preencha o modelo (ele já vem com o checklist).

## Rodar os testes

Todos rodam sem mídia real e sem rede (a API da Meta é simulada):

```bash
uv sync
uv run python tests/portoes/test_portoes.py        # GAUNTLET: impressões, S0/S1/S2, selo do pacote
uv run python tests/publicar/test_publicar.py      # agendar, publicar (simulado), carrossel, selo   (precisa do ffmpeg)
uv run python tests/metricas/test_metricas.py      # leitura das métricas aos 5 dias
uv run python tests/comentarios/test_responder.py  # comentário → direct com o PDF
uv run python tests/test_cta_props.py              # cartão do CTA
uv run python tests/cor/test_cor.py                # cor: LUT, primária, V-Log → Rec.709   (ffmpeg com zimg)
uv run python painel/tests/test_previas_looks.py   # prévias dos looks do painel
python3 -I scripts/varrer_privacidade.py           # nenhum segredo, caminho pessoal, e-mail ou ID real
```

Testes que pedem mais do que isso:

| Teste | Precisa de |
|---|---|
| `painel/tests/test_sincronizar.py` | um Postgres do Supabase local no ar (`bash painel/iniciar.sh`, ou outro servidor em `PAINEL_TESTE_SERVIDOR`); cria e apaga um banco de teste próprio |
| `estudio-contexto/tests/` | o Postgres do painel + o modelo de embedding no cache do Hugging Face |
| `painel/tests/test_biblioteca_yaml.py` | os vídeos e pacotes do **seu** estúdio (confere o `biblioteca.yaml` contra eles) |
| `tests/check_synthetic.py` | a cadeia sintética de edição (`tests/README.md`): ffmpeg, a voz `say` do macOS e a transcrição |
| Remotion | `cd remotion && npm ci && npx tsc --noEmit` |
| Painel web | `cd painel/web && npm ci && npx tsc --noEmit && npm run lint` |

O CI do GitHub roda, em todo pull request, os testes da primeira lista (menos o de cor, que pede um ffmpeg com zimg),
o TypeScript e o lint do Remotion e do painel, a varredura de privacidade e o gitleaks.

## Padrões do projeto

- **Português do Brasil** em tudo: código (nomes de funções e variáveis já são em português), comentários, mensagens de
  erro, documentação, commits. "Você", nunca "tu".
- **Python** com `uv run python …` (Python 3.12). Biblioteca padrão quando der; dependência nova só com motivo no PR.
- **Os arquivos são a fonte da verdade.** O painel e o índice de contexto só leem; nada escreve fora do lugar dele.
- **Formatos de arquivo** seguem [`docs/contratos.md`](docs/contratos.md). Campo novo = atualizar o contrato no mesmo PR.
- **25 fps** em todo o projeto; nunca converter para 30.
- **Nada de dado real** em teste, exemplo ou documentação: nomes, @ de contas, IDs da Meta, e-mails, caminhos
  `/Users/<você>/`. Use dados inventados (veja `exemplos/`).
- Conferir **no ponto do defeito** (regra 10 do [`CLAUDE.md`](CLAUDE.md)): compilar não prova que roda; olhe o quadro,
  o número ou a tela onde o problema apareceu.

## O GAUNTLET como checklist de revisão

O estúdio usa portões para não deixar passar o que quem fez não enxerga ([`docs/gauntlet.md`](docs/gauntlet.md)). A
revisão de um pull request segue a mesma ideia — **quem fez não aprova**. Quem revisa confere, pela área que o PR toca:

| Área | Portão | O que olhar |
|---|---|---|
| Agentes de pauta e pesquisa | PORTÃO-PAUTA | fato com fonte; identidade de quem aparece; caminho certo do material (licença × comentário) |
| Roteiro e PDF | PORTÃO-ROTEIRO | voz e regras de alcance; CTA que entrega o que promete; PDF ≤ 2 páginas |
| Cor, capa, extras, animação | PORTÃO-IMAGEM | cadeia de cor; nada sobre o rosto; olhar os quadros, não só o código |
| Edição, áudio, Remotion | PORTÃO-CORTE | specs (1080×1920, 25 fps, −14 LUFS); corte contra o roteiro; testes sintéticos |
| Publicação e automação Meta | PORTÃO-PUBLICACAO | só publica o que tem selo; nada de chamada real nos testes; token nunca no log |
| Painel web | PORTÃO-INTERFACE | fiel ao design aprovado; tela olhada em 1440 e 375 px; chave nenhuma no navegador |
| Banco e sincronizador | PORTÃO-DADOS | migração versionada; RLS; o sincronizador só lê o projeto; teste para cada mapeamento |

Severidades: **S0** vai ao ar errado · **S1** quebra o fluxo ou a confiança · **S2** melhoria. PR com S0 ou S1 aberto
não entra.

Se você usa IA para programar, o [`AGENTS.md`](AGENTS.md) e o [`CLAUDE.md`](CLAUDE.md) explicam as regras para ela.

## Etiquetas

As issues usam as etiquetas de [`.github/labels.md`](.github/labels.md). Procurando por onde começar? Filtre por
`good first issue`.

## Conduta

Este projeto segue o [Código de Conduta](CODE_OF_CONDUCT.md). Problema de segurança? Não abra issue pública: veja
[`SECURITY.md`](SECURITY.md).

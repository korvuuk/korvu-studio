---
name: gerar-imagem
description: Gera uma imagem por IA para o estúdio — Gemini 3.1 Flash Image (via OpenRouter) ou OpenAI gpt-image-2 — com modo teste barato, imagens de referência (logo, estilo) e registro de tudo o que foi gerado. Usar quando uma cena extra, animação, capa, carrossel ou PDF precisar de uma imagem que não existe e não há material livre que sirva. Nunca para imagem realista de pessoa real além do autor.
---

# Gerar imagem (Gemini · OpenAI)

Integração de imagem do estúdio: OpenRouter + Gemini e OpenAI `gpt-image-2`.
Script: `scripts/gerar_imagem.py`.

## Antes de gerar (nessa ordem)
1. **Já existe?** Procure no próprio vídeo (`videos/<slug>/material/`, `brutos/extras/`) e em `00-marca/`.
2. **Tem material livre?** Para B-roll de coisa real (pessoa, lugar, produto), o caminho é `/material`
   (licença) ou print da ferramenta — imagem gerada não substitui foto real de um fato.
3. **Precisa mesmo?** Gerar custa dinheiro. Gere **uma** e valide; nada de lote de "variações para ver".

## Regras (CLAUDE.md da raiz)
- **Regra 3:** nunca imagem realista de pessoa real além do autor (nem "parecida com"). Ilustração, objeto,
  cenário, interface, metáfora visual — sim.
- Logo de terceiro só identificando a ferramenta de que o vídeo fala, nunca sugerindo parceria.
- Texto dentro da imagem gerada sai errado com frequência: o texto de tela é do Remotion/Claude Design, não da IA.
- Imagem gerada que entra num vídeo passa pelo **PORTÃO-IMAGEM** como qualquer extra.

## Motores
| `--motor` | Modelo | Quando | Chave |
|---|---|---|---|
| `teste` (padrão) | OpenRouter `sourceful/riverflow-v2-fast` | validar composição, barato | `OPENROUTER_API_KEY` |
| `gemini` | OpenRouter `google/gemini-3.1-flash-image-preview` | final; bom com referência de marca | `OPENROUTER_API_KEY` |
| `openai` | OpenAI `gpt-image-2` (`images/generations`; `images/edits` com `--ref`) | final; bom em fotorrealismo de objeto e em editar a partir de referência | `OPENAI_API_KEY` |

Chaves no `.env` da raiz (nomes no `.env.example`). O script lê do ambiente/`.env` e nunca imprime a chave.
Quem não tiver uma das chaves usa só o motor da outra.

## Uso
```bash
# 1) ver o pedido sem gastar (sem chave, sem rede)
uv run python .claude/skills/gerar-imagem/scripts/gerar_imagem.py --saida videos/<slug>/material/gerado/E05.png \
  --prompt "…" --motor gemini --seco
# 2) validar barato
uv run python .claude/skills/gerar-imagem/scripts/gerar_imagem.py --saida …/E05-teste.png --prompt "…" --motor teste
# 3) final, com referência de estilo
uv run python .claude/skills/gerar-imagem/scripts/gerar_imagem.py --saida …/E05.png --prompt-arquivo prompt.txt \
  --motor gemini --ref 00-marca/<referencia>.png
# OpenAI, vertical
uv run python .claude/skills/gerar-imagem/scripts/gerar_imagem.py --saida …/E05.png --prompt "…" --motor openai --tamanho 1024x1536
```
Onde salvar: `videos/<slug>/material/gerado/` (cena extra entra depois em `brutos/extras/` pelo `produtor-de-extras`),
`videos/<slug>/animacoes/<ID>/` (animação), `carrosseis/<pasta>/` (carrossel). Cada imagem acrescenta uma linha em
`imagens-geradas.jsonl` na mesma pasta (data, motor, modelo, prompt, referências) — é o registro do que foi gerado.

## Prompt
Inglês costuma render melhor. Diga: assunto, composição, estilo Korvu (fundo preto/grafite, luz laranja #FF7A35,
limpo, sem texto), proporção. Termine com "no text, no watermark".

## Ainda não existe
Geração de **vídeo** por IA não está integrada ao estúdio (12/11). Quando for, entra como skill própria.

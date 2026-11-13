# O que faltou no dossiê (Volume 1 · Estúdio)

Anotado pela designer-de-documentacao em 12/11/2026. A página mostra só o que está no dossiê; o que segue ficou de
fora ou aparece como "não documentado / não confirmado".

## Fatos que o dossiê não traz
1. **Custo do Cloudflare R2 e do plano da ElevenLabs** em uso: a página diz "não documentado" (dossiê §5.4 e §12.1).
2. **Plano/custo real do Claude Code**: só a estimativa a preço de tabela do painel (§12.2).
3. **App Review da Meta**: não confirmado se o app passou por revisão nem se directs para contas de fora já saíram
   (§12.4). A página diz isso no passo 6 de "Para reproduzir".
4. **Validade real do token da Página** atual ("expira: nunca"?): só o `verificar-tokens` mostraria (§12.5).
5. **Versões do ffmpeg e do Node.js**: não fixadas em arquivo (§12.6). A tabela diz "não fixada" / "—".
6. **Chaves da skill `watch` (Groq/OpenAI)**: não confirmado se estão configuradas (§12.3). O cartão diz "não confirmado".
7. **`pages_manage_engagement` no token**: não confirmado (§12.7).
8. **Versões de PyYAML, python-dotenv e soundfile**: estão no dossiê (§3) mas não no `dados.json`; a tabela diz "ver
   `uv.lock`" para não ter versão que o `dados.json` não confirma.
9. **Capturas**: o volume não tem capturas de tela (o dossiê avisa). A capa usa o diagrama do sistema no lugar da
   captura principal.

## Deixado de fora de propósito (dado operacional ou privado)
- **Horários das vagas semanais e o fuso** de `_controle/calendario.md`: o dossiê pede para decidir se ficam públicos
  ("Revisar antes de publicar"). A página fala só em "vagas semanais do calendário" e "fuso do calendário ou
  `TZ_PUBLICACAO`". Decisão para o autor.
- IDs de conta, app, Página e mídia; nome do bucket e domínio público do R2; e-mail; caminhos absolutos do Mac: nada
  disso está na página nem no README (o build recusa caminho do Mac, e-mail, padrões de chave e domínio do R2).
- Nomes de quem comentou e conteúdo do `estado.json`: não usados.

## Divergências do dossiê que a página mostra (porque ajudam quem reproduz)
- Token **não renova sozinho** (§4.3): nota destacada na seção Meta.
- A lista de 7 permissões do `ARQUITETURA.md` está **incompleta** (§12, divergência 3): dito no passo 2 de "Para reproduzir".
- ~~`qa_check.py` reprova vídeo acima de 180 s~~ — **corrigido em 12/11**: `dur_max` = 900 s, igual ao `publicar.py`.
- Trial padrão vazio no calendário (§4.8 e divergência 4): dito na seção Meta.
- Testes 112/116 e o motivo das 4 falhas (§10): seção Qualidade.

## Não mostradas (não ajudam quem reproduz)
Divergências 1, 2, 6, 7, 8 e 9 do §12 (textos antigos em `ARQUITETURA.md`, docstrings, caminho do `resolve.py`, TODO do
Supabase).

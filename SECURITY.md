# Segurança

## Como relatar uma vulnerabilidade

**Não abra issue pública** para problema de segurança. Use o relato privado do GitHub: na página do repositório,
aba **Security** → **Report a vulnerability**. Diga o que encontrou, como reproduzir e qual o impacto. A resposta
inicial vem em até 7 dias.

## O que conta como problema de segurança aqui

- Um caminho em que um **token da Meta, chave da ElevenLabs ou do R2** apareça em log, arquivo versionado, mensagem de
  erro ou no navegador.
- O painel ou o banco local **acessível pela rede** (eles foram feitos para escutar só em `127.0.0.1`).
- O sincronizador do painel ou o índice de contexto **escrevendo** nos arquivos do projeto (eles só leem).
- A automação de comentários respondendo ou mandando material para quem não pediu, ou publicando fora do fluxo
  (sem pacote selado pelo GAUNTLET).
- Dado pessoal (nome de quem comentou, @, e-mail, IDs) indo para o repositório.

## Boas práticas para quem usa o Korvu Studio

- Segredos só no `.env` (já está no `.gitignore`). O `.env.example` tem só os nomes das variáveis.
- Antes de cada commit: `python3 -I scripts/varrer_privacidade.py`. O CI roda a mesma varredura e o gitleaks.
- O Supabase local vem com as **chaves de demonstração públicas** do Supabase CLI. Elas só servem no seu computador;
  troque antes de expor o painel em qualquer rede.
- Os tokens da Página do Facebook não renovam sozinhos: `uv run python scripts/publicar.py verificar-tokens`.
- Não rode o painel nem o banco com portas abertas para a rede (`bash painel/so-no-mac.sh` confere).

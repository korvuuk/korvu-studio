## O que muda

<!-- Uma ou duas frases: o quê e por quê. Ligue a issue: "Resolve #123". -->

## Como testei

<!-- Os comandos que rodou e o resultado. Mudou tela, cor, corte ou capa? Anexe a imagem do ponto que mudou. -->

## Checklist (GAUNTLET — quem faz não aprova)

- [ ] Testes da área passam (`CONTRIBUTING.md` → Rodar os testes)
- [ ] `python3 -I scripts/varrer_privacidade.py` sem achados — nenhum token, @ real, e-mail, ID da Meta ou `/Users/<você>/`
- [ ] Conferi no ponto do defeito (o quadro, o número ou a tela), não só que compila
- [ ] Formato de arquivo novo ou mudado está em `docs/contratos.md`
- [ ] Tudo em português do Brasil (código, mensagens, docs)
- [ ] Mudou o painel: olhei a tela em 1440 e 375 px
- [ ] Mudou o banco: migração nova em `painel/supabase/migrations/` (nunca editar uma antiga) e RLS ligada

**Portão que revisa:** <!-- PORTÃO-PAUTA · ROTEIRO · IMAGEM · CORTE · PUBLICACAO · INTERFACE · DADOS -->

# painel/design — design system "korvu. painel"

O sistema que o autor fez no Claude Design (23/10/2026), importado em PT-BR, com os valores exatos da fonte.
Substitui o korvu-editorial **só dentro do painel**.

> **No repositório público** não vêm as maquetes e especificações por tela (`telas/`), as prévias (`previas/`), a
> verificação de fidelidade (`verificacao/fidelidade.py`, que compara com as referências) nem as referências (`painel/referencias/`): tinham dados reais do estúdio de origem.
> Comentários no código e nos agentes que citam `painel/design/telas/<tela>.md` apontam para essas especificações;
> o comportamento de cada tela está descrito no Volume 2 (`docs/painel/`). Quem quiser redesenhar uma tela cria a
> sua maquete em `telas/` e a especificação ao lado.

Por onde começar:
1. `tokens.css` / `tokens.json` — cores, tipografia, espaços e raios.
2. `design-system.md` — as regras: cor, tipografia, grade, 375 px, cada componente, estados, pendências.
3. `handoff.md` — o que o engenheiro-frontend faz com isto.
4. `contraste.md` — cada par medido; o que falha não foi trocado (vai ao autor).
5. `movimento.css` — Movimento v1 (03/11, skill `apple-design`): o controle afunda no toque, popovers nascem do
   botão, a gaveta do celular desce do topo; respeita "menos movimento". Regras no `design-system.md` §7.1.
   Movimento v2 (04/11): cartões, barras, anéis e linha entram com animação e os números contam (§7.2).

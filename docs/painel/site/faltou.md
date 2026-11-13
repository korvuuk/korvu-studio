# O que faltou no dossiê (designer-de-documentacao, 12/11/2026)

O que a documentação precisou e o dossiê não traz. Nada disso foi inventado: onde faltou, a página diz que falta ou
fica sem o dado.

## Faltou fato
1. **"Por quê" da maioria das tecnologias.** O dossiê só registra o motivo escrito no projeto para 11 das 18 linhas da
   tabela de tecnologia. As outras 7 ficam com "—" no site (Next.js, React, TypeScript, Tailwind, ESLint, Python,
   psycopg). Para o portfólio valeria o dono escrever o motivo de cada escolha.
2. **De onde vem cada dado, bloco a bloco.** O dossiê lista as tabelas por TELA, não por bloco. O site mostra a lista da
   tela inteira ao lado dos blocos numerados, sem ligar tabela a bloco.
3. **Licença do código.** Para "gente de fora baixar e reusar" no GitHub falta dizer sob que licença o painel é
   publicado. Só as fontes têm licença conhecida (Geist, OFL 1.1, cópia em `site/fontes/OFL.txt`). O README não declara
   licença.
4. **Como obter o código.** Não há URL de repositório nem comando de clone no dossiê; a instalação começa "na raiz do
   projeto".
5. **Versões sem arquivo que as fixe:** Supabase CLI (o ambiente respondeu 2.109.1, mas não é do código), uv, ffmpeg,
   Colima, Chrome. No site aparecem sem versão.
6. **Criação do `painel/web/.env.local`:** passo deduzido pelo documentador, não confirmado. O site e o README marcam
   como "não confirmado".
7. **`test_sincronizar.py`:** não rodado; o resultado aparece como "não rodado", sem número.
8. **Primeiro `supabase start` aplicando as 18 migrações:** provável, não testado. Marcado assim no site.
9. ~~**Origem das fotos da equipe**~~ — resolvido em 13/11: imagens geradas por IA, não pessoas reais (decisão do autor). Antes: o README do painel e o `equipe.yaml` divergem (foto
   realista × ilustração gerada); o dossiê não confirma se são imagens geradas por IA. Elas aparecem nas capturas.

## Decisões de desenho que não vêm do dossiê (para o portão conferir)
10. **Modo escuro.** O design system "korvu. painel" tem um tema só (Marfim, "não existe modo escuro"). A regra da página
    pede modo escuro; ele foi montado só com cores que já existem nos tokens (`sidebar #111111`, `sidebar-raised
    #1D1C1A`, `sidebar-line #2C2A27`, `sidebar-ink #F5F2E8`, `sidebar-ink-2 #9A9385`, `line-strong`/`ink-2 #6B6458`
    para bordas, e o acento `#FF4D00` como foco e laranja de texto, a mesma regra do `focus-on-dark`). Nenhuma cor nova.
    As amostras do design system e as capturas ficam sempre no Marfim.
11. **Posição dos marcadores sobre as capturas** (os números 1, 2, 3… de cada tela): medida por mim olhando as fotos de
    1440 px; a ordem e o nome dos blocos são os do dossiê.
12. **Capturas no tamanho original.** As 18 PNG foram copiadas sem editar (2× de densidade, ~17 MB no total). O site as
    carrega todas de uma vez; se o peso pesar na publicação, a saída é uma cópia reduzida feita com decisão do dono.
13. **Linha do tempo das migrações** ficou em HTML (não virou SVG solto). Os SVG soltos são os 4 diagramas:
    arquitetura, banco, segurança e sincronização.
14. **Contagem de componentes.** O dossiê diz 48 arquivos e lista os nomes com `Graficos (Barras, Legenda, Rosca,
    Sparkline)` como um só; o site mostra os 48 nomes de arquivo.

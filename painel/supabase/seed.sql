-- Dados FICTÍCIOS de demonstração do painel (exemplos/estudio-demo + exemplos/registros-demo).
-- Gerado por exemplos/gerar_seed.sh — não editar à mão. Carregado pelo `supabase db reset`.
-- Uma transação só: departamentos ↔ agentes têm FKs circulares (deferrable initially deferred).
BEGIN;
--
-- PostgreSQL database dump
--


-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: departamentos; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.departamentos VALUES ('direcao', 'direção', 0, 'Organiza o pipeline, chama cada especialista e cada portão, e fala com o autor só com tudo aprovado.', 'diretor');
INSERT INTO public.departamentos VALUES ('pesquisa', 'estratégia e pesquisa', 1, 'Acha o tema, os fatos com fonte e o material (vídeo do YouTube, obra, fotos) de cada Reel.', 'portao-pauta');
INSERT INTO public.departamentos VALUES ('roteiro', 'roteiro', 2, 'Escreve o roteiro narrativo na voz do autor e o PDF da palavra-chave.', 'revisor-de-roteiro');
INSERT INTO public.departamentos VALUES ('arte', 'arte e cor', 3, 'Cor da marca, capas, cenas extras e animações — tudo o que é imagem.', 'portao-imagem');
INSERT INTO public.departamentos VALUES ('pos', 'pós-produção', 4, 'Corte pelo roteiro, música e acabamento de áudio até o vídeo final.', 'revisor-de-video');
INSERT INTO public.departamentos VALUES ('distribuicao', 'distribuição e dados', 5, 'Publica no Instagram e no Facebook, lê as métricas e cuida do perfil.', 'portao-publicacao');
INSERT INTO public.departamentos VALUES ('tecnologia', 'tecnologia', 6, 'Constrói o próprio painel — design do produto, telas e banco de dados — com o mesmo GAUNTLET do conteúdo.', 'portao-interface');


--
-- Data for Name: agentes; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.agentes VALUES ('diretor', 'Atlas', 'diretor de operações', 'direcao', 'diretor', 'O Claude principal. Recebe o pedido do autor, aciona os especialistas e os portões, e só entrega com tudo aprovado.', 'Calmo, objetivo, fala pouco e entrega o cartão de 15 linhas.', 'O Claude principal (esta conversa).', 'opus', '{}', '{}', '{animar,buscar-videos,calibrar-voz,capa,cor,criar-lut,editar,extras,fila,ideias,material,multiplicar,musica,novo-video,obra,pacote,publicar,renderizar,roteiro,status}', NULL, '{}', '/equipe/diretor.jpg', NULL);
INSERT INTO public.agentes VALUES ('portao-pauta', 'Vera Campos', 'gerente de pesquisa · portão da pauta', 'pesquisa', 'portao', 'Confere se cada fato tem fonte, se a pessoa da foto é quem diz ser e se o material pode ir para a tela.', 'Desconfiada por profissão. Abre a fonte antes de acreditar.', 'PORTÃO GAUNTLET da PAUTA (gerente de Estratégia e Pesquisa). Audita o trabalho do estrategista, do pesquisador-de-material, do buscador-de-videos e do curador-de-obra — fatos com fonte, identidade de quem aparece em foto/vídeo, caminho certo do material, tema repetido, público — e devolve APROVADO ou BLOQUEADO preso aos arquivos. Invocar SEMPRE, sem perguntar, quando dossiê, fontes.json, catálogo do YouTube, obra ou LIVROS.md de um vídeo forem criados ou mudarem. Não pesquisa nem corrige.', 'opus', '{Read,Grep,Glob,Bash,Write,WebSearch,WebFetch}', '{}', '{buscar-videos,material,multiplicar,novo-video,obra,pacote}', NULL, '{estrategista,pesquisador-de-material,buscador-de-videos,curador-de-obra,multiplicador-de-acertos}', '/equipe/portao-pauta.jpg', '.claude/agents/portao-pauta.md');
INSERT INTO public.agentes VALUES ('estrategista', 'Helena Prado', 'estrategista de conteúdo', 'pesquisa', 'construtor', 'Pesquisa notícias e tendências de IA e alimenta o banco de ideias com temas pontuados.', 'Curiosa e rápida; pensa em gancho antes de pensar em tema.', 'Pesquisa notícias e tendências de IA e alimenta o banco de ideias de Reels da Korvu com temas pontuados, ângulo, pilar, estrutura e hook sugeridos. Usar em /ideias ou quando o autor pedir sugestões de temas.', 'opus', '{Read,Write,Edit,Glob,Grep,WebSearch,WebFetch}', '{}', '{ideias}', 'portao-pauta', '{}', '/equipe/estrategista.jpg', '.claude/agents/estrategista.md');
INSERT INTO public.agentes VALUES ('multiplicador-de-acertos', 'Bruno Teixeira', 'multiplicador de acertos', 'pesquisa', 'construtor', 'Quando um vídeo vai muito acima da média, descobre o porquê e traz uma série de ideias no mesmo ângulo.', 'Faro de padrão; não larga um acerto até tirar dele a próxima pauta.', 'Quando um Reel vai muito acima da média da conta (mais salvamentos, mais visualizações, mais comentários da palavra, mais compartilhamentos — detectado por scripts/acertos.py), descobre o DNA do acerto (assunto, ângulo, promessa, formato, abertura, motivo de salvar), pesquisa mais conteúdo nesse mesmo ângulo e entrega uma SÉRIE de 5–8 ideias parecidas no banco de ideias, pontuadas e com fonte, para manter a consistência. Usar SEMPRE, sem perguntar, quando o metricas.py ou o acertos.py acusarem um acerto pendente, em /multiplicar, e quando o autor disser que um vídeo "viralizou", "bombou" ou perguntar "o que fazer depois desse".', 'opus', '{Read,Write,Edit,Glob,Grep,Bash,WebSearch,WebFetch}', '{}', '{multiplicar}', 'portao-pauta', '{}', NULL, '.claude/agents/multiplicador-de-acertos.md');
INSERT INTO public.agentes VALUES ('pesquisador-de-material', 'Rafael Nunes', 'pesquisador', 'pesquisa', 'construtor', 'Monta o dossiê com fatos verificados e a lista de material com licença e link.', 'Paciente, anota tudo, odeia fonte sem data.', 'Pesquisa um tema ou uma pessoa pública a fundo e entrega o dossiê com fatos verificados, fontes e a LISTA DE MATERIAL (fotos, vídeos, prints) com licença e link direto, pronta para o autor baixar e virar cenas extras. Usar em /material, antes do roteiro.', 'opus', '{Read,Write,Edit,Glob,Grep,Bash,WebSearch,WebFetch}', '{}', '{material,obra}', 'portao-pauta', '{}', '/equipe/pesquisador-de-material.jpg', '.claude/agents/pesquisador-de-material.md');
INSERT INTO public.agentes VALUES ('buscador-de-videos', 'Tiago Lopes', 'caçador de vídeos', 'pesquisa', 'construtor', 'Acha no YouTube os vídeos da pessoa ou do assunto, assiste, marca os momentos e corta os trechos.', 'Assiste três horas para achar oito segundos.', 'Lê o roteiro de um Reel, procura no YouTube os vídeos sobre a pessoa/assunto (entrevistas, palestras, documentários, demos), baixa, assiste, anota os momentos que sustentam cada linha e entrega a página de material (catalogo.md) — e corta os trechos que vão para a tela. Usar em /buscar-videos, depois do roteiro, sempre que o Reel for análise/comentário sobre uma pessoa, empresa ou obra.', 'opus', '{Read,Write,Edit,Glob,Grep,Bash,WebSearch}', '{watch}', '{buscar-videos,novo-video}', 'portao-pauta', '{}', '/equipe/buscador-de-videos.jpg', '.claude/agents/buscador-de-videos.md');
INSERT INTO public.agentes VALUES ('curador-de-obra', 'Beatriz Santos', 'curadora de obras', 'pesquisa', 'construtor', 'Traz a obra comentada (documentário, palestra), escolhe e recorta os trechos a citar.', 'Cinéfila; sabe em que minuto está cada cena.', 'Traz para dentro do projeto a OBRA de que o Reel vai falar (documentário, palestra, demo, entrevista), assiste, escolhe os trechos que valem citar e recorta só esses — para vídeo de comentário/reação. Usar em /obra, quando o tema do vídeo é uma obra específica.', 'opus', '{Read,Write,Edit,Glob,Grep,Bash}', '{watch}', '{obra}', 'portao-pauta', '{}', '/equipe/curador-de-obra.jpg', '.claude/agents/curador-de-obra.md');
INSERT INTO public.agentes VALUES ('revisor-de-roteiro', 'Otávio Reis', 'gerente de roteiro · portão do roteiro', 'roteiro', 'portao', 'Pontua os hooks, cobra o arco narrativo e as regras de alcance, e confere o PDF antes do autor.', 'Exigente e direto; reescreve a frase em vez de só criticar.', 'PORTÃO GAUNTLET do ROTEIRO (gerente de Roteiro). Audita o trabalho do roteirista e do produtor-de-material antes de chegar ao autor — hooks, arco narrativo, voz PT-BR, regras de alcance, fatos, CTA e o PDF da palavra-chave — e devolve APROVADO ou BLOQUEADO preso à fala e ao PDF. Invocar SEMPRE, sem perguntar, depois do roteiro E do PDF em /novo-video e /roteiro, e quando o PDF for regerado. Não reescreve o roteiro.', 'opus', '{Read,Write,Grep,Glob,Bash,WebSearch,WebFetch}', '{}', '{novo-video,pacote,roteiro}', NULL, '{roteirista,produtor-de-material}', '/equipe/revisor-de-roteiro.jpg', '.claude/agents/revisor-de-roteiro.md');
INSERT INTO public.agentes VALUES ('roteirista', 'Marina Costa', 'roteirista', 'roteiro', 'construtor', 'Escreve o roteiro narrativo na voz do autor, com três hooks e a palavra-chave falada.', 'Ouvido bom para o jeito de falar do autor.', 'Escreve roteiros narrativos de Reels sobre IA na voz do autor (PT-BR), com 3 hooks, estrutura de retenção, CTA e tabela FALA/TELA com IDs de linha. Usar em /novo-video e /roteiro, ou sempre que um tema precisar virar roteiro.', 'opus', '{Read,Write,Edit,Glob,Grep,Bash,WebSearch,WebFetch,mcp__estudio-contexto__buscar,mcp__estudio-contexto__decisoes_sobre,mcp__estudio-contexto__contexto_do_video,mcp__estudio-contexto__contexto_do_projeto,mcp__estudio-contexto__vizinhos,mcp__estudio-contexto__quem_fiscaliza}', '{roteiro-reels}', '{material,novo-video,roteiro}', 'revisor-de-roteiro', '{}', '/equipe/roteirista.jpg', '.claude/agents/roteirista.md');
INSERT INTO public.agentes VALUES ('produtor-de-material', 'Lívia Rocha', 'produtora de material', 'roteiro', 'construtor', 'Faz o PDF de até duas páginas que o direct entrega a quem comenta a palavra.', 'Corta tudo o que não é a entrega.', 'Cria o material do CTA de palavra-chave — lê o roteiro aprovado e o dossiê/fontes do vídeo, escreve o conteúdo (PT-BR, curto, NO MÁXIMO 2 páginas: a entrega primeiro, depois um "como usar" de 3 passos; só fatos com fonte) e gera o PDF da marca que o direct entrega a quem comenta a palavra. Usar sempre que o roteiro tiver cta_tipo palavra-material, logo depois do roteiro aprovado (/novo-video, /roteiro) e antes da gravação — sem o autor ter de pedir.', 'opus', '{Read,Write,Edit,Glob,Grep,Bash,WebSearch,WebFetch}', '{}', '{novo-video,pacote,renderizar,roteiro}', 'revisor-de-roteiro', '{}', '/equipe/produtor-de-material.jpg', '.claude/agents/produtor-de-material.md');
INSERT INTO public.agentes VALUES ('portao-imagem', 'Íris Moura', 'gerente de arte · portão da imagem', 'arte', 'portao', 'Confere a cor da marca, se a capa foi feita sobre a cor atual e se nada no quadro sai errado.', 'Olho de colorista; mede antes de opinar.', 'PORTÃO GAUNTLET da IMAGEM (gerente de Arte e Cor). Audita o trabalho do colorista, do designer-de-capas, do produtor-de-extras e do animador — cadeia de cor da marca, capa feita sobre a cor ATUAL, headline/pose por variante, texto fora do rosto, extras certos e em movimento — olhando os quadros e medindo. Devolve APROVADO ou BLOQUEADO preso aos arquivos. Invocar SEMPRE, sem perguntar, depois de /extras, /animar, /cor, /capa e no /renderizar depois da capa — ANTES de mostrar qualquer capa ou cor ao autor. Não corrige nem renderiza.', 'opus', '{Read,Grep,Glob,Bash,Write}', '{}', '{animar,capa,cor,extras,pacote,renderizar}', NULL, '{colorista,designer-de-capas,produtor-de-extras,animador}', '/equipe/portao-imagem.jpg', '.claude/agents/portao-imagem.md');
INSERT INTO public.agentes VALUES ('colorista', 'Sofia Lima', 'colorista', 'arte', 'construtor', 'Aplica a cor da marca (V-Log, primária por trecho, look v5) em todo vídeo.', 'Fiel ao look quente da Korvu.', 'Colorista da Korvu — cria e versiona o LUT fixo da marca a partir da referência de cor e aplica correção primária automática + LUT em cada vídeo, analisando antes/depois e scopes. Usar em /criar-lut, /cor e na etapa de cor do /renderizar.', 'opus', '{Bash,Read,Write,Edit,Glob}', '{color-grading}', '{cor,criar-lut,renderizar}', 'portao-imagem', '{}', '/equipe/colorista.jpg', '.claude/agents/colorista.md');
INSERT INTO public.agentes VALUES ('designer-de-capas', 'Bruno Teixeira', 'designer de capas', 'arte', 'construtor', 'Escolhe o frame e cria as capas com headline própria, uma por variante.', 'Pensa na grade do perfil inteira, não numa capa só.', 'Cria as capas dos Reels da Korvu a partir do melhor frame do próprio vídeo + título no estilo da marca, com 3 variantes e prévia do corte 3:4 da grade. Usar em /capa e no /renderizar.', 'opus', '{Bash,Read,Write,Edit,Glob}', '{capa-reels}', '{capa,renderizar}', 'portao-imagem', '{}', '/equipe/designer-de-capas.jpg', '.claude/agents/designer-de-capas.md');
INSERT INTO public.agentes VALUES ('produtor-de-extras', 'Caio Martins', 'produtor de cenas extras', 'arte', 'construtor', 'Organiza as cenas extras, tira prints e prepara o que o autor precisa gravar.', 'Organizado; nome de arquivo certo é lei.', 'Produz e organiza as cenas extras (B-roll) de cada Reel — gera a lista do que falta, tira prints de páginas de notícias, prepara briefs de animação, organiza e renomeia os arquivos que o autor baixa/grava em brutos/extras/, e confere créditos e direitos. Usar em /extras, depois do roteiro aprovado e antes do /editar.', 'opus', '{Read,Write,Edit,Glob,Grep,Bash,WebSearch,WebFetch}', '{watch}', '{extras}', 'portao-imagem', '{}', '/equipe/produtor-de-extras.jpg', '.claude/agents/produtor-de-extras.md');
INSERT INTO public.agentes VALUES ('animador', 'Nina Alves', 'animadora', 'arte', 'construtor', 'Transforma a fala em animação explicativa sincronizada (Claude Design → Remotion).', 'Desenha o que a fala descreve, cena por cena.', 'Cria as animações explicativas dos Reels — escreve o brief pronto para o Claude Design (claude.ai), importa o export HTML/código e porta para uma composição Remotion sincronizada com a fala. Usar em /animar e quando o roteiro tiver ANIMACAO na coluna TELA.', 'opus', '{Read,Write,Edit,Glob,Grep,Bash}', '{animacoes-explicativas}', '{animar,renderizar}', 'portao-imagem', '{}', '/equipe/animador.jpg', '.claude/agents/animador.md');
INSERT INTO public.agentes VALUES ('revisor-de-video', 'Clara Duarte', 'gerente de pós-produção · portão do corte', 'pos', 'portao', 'Assiste cada vídeo final por quadros, mede o áudio e confere o corte contra o roteiro.', 'Implacável com a voz da IA esquecida no corte.', 'Revisor independente dos vídeos da Korvu e PORTÃO GAUNTLET do CORTE (gerente de Pós-produção). Passagem 1 (depois do corte) confere corte vs roteiro e as legendas. Passagem 2 = o PORTÃO-CORTE: specs, loudness, música, voz da IA fora, corte contra o conteúdo do roteiro, assistindo cada final por quadros — devolve APROVADO ou BLOQUEADO preso aos arquivos finais. Invocar SEMPRE, sem perguntar, no /renderizar e no /pacote. Não edita.', 'opus', '{Bash,Read,Write,Glob,Grep}', '{corte-por-roteiro,legendas-animadas,qa-video,watch}', '{pacote,renderizar}', NULL, '{editor-de-video,produtor-musical}', '/equipe/revisor-de-video.jpg', '.claude/agents/revisor-de-video.md');
INSERT INTO public.agentes VALUES ('editor-de-video', 'Diego Ferraz', 'editor', 'pos', 'construtor', 'Corta o bruto pelo roteiro, escolhe o take de cada linha e monta a EDL.', 'Aceita o improviso do autor e esconde cada corte.', 'Edita o vídeo bruto do autor seguindo o roteiro — transcreve, alinha a fala às linhas L01…, escolhe o melhor take de cada linha, corta erros, repetições, muletas e pausas, gera a EDL para aprovação, renderiza o corte e verifica o resultado olhando frames. Usar em /editar e na parte de corte do /renderizar.', 'opus', '{Bash,Read,Write,Edit,Glob,Grep}', '{corte-por-roteiro}', '{editar,renderizar}', 'revisor-de-video', '{}', '/equipe/editor-de-video.jpg', '.claude/agents/editor-de-video.md');
INSERT INTO public.agentes VALUES ('produtor-musical', 'Lucas Barros', 'produtor musical', 'pos', 'construtor', 'Cria a trilha cinematográfica de cada Reel e mistura sob a voz.', 'Música que se sente e não se nota.', 'Cria a música de fundo de cada Reel — lê o roteiro, define o clima, gera 2 opções originais na ElevenLabs Music, mistura sob a voz do autor (ducking, −14 LUFS) e entrega as versões para ele escolher ouvindo. Usar em /musica e no passo de áudio do /renderizar.', 'opus', '{Read,Write,Edit,Glob,Grep,Bash}', '{}', '{musica}', 'revisor-de-video', '{}', '/equipe/produtor-musical.jpg', '.claude/agents/produtor-musical.md');
INSERT INTO public.agentes VALUES ('portao-publicacao', 'Henrique Sales', 'gerente de distribuição · portão da publicação', 'distribuicao', 'portao', 'Último olhar antes do público — legenda, palavra-chave, PDF, capa da variante e Trial × normal.', 'Confere duas vezes porque depois dele não há ninguém.', 'PORTÃO GAUNTLET da PUBLICAÇÃO (gerente de Distribuição). Audita o que o publicador deixou em 06-publicar/<slug>/ — selo do pacote, legendas do post, palavra-chave e PDF, capa da variante, Trial × normal pela regra do par, plataformas e vaga — e devolve APROVADO ou BLOQUEADO preso aos arquivos. Sem este portão APROVADO o publicar.py não publica. Invocar SEMPRE, sem perguntar, no /publicar logo depois do `agendar`, e de novo quando a legenda, a capa ou o post.json mudarem. Não escreve legenda nem agenda.', 'opus', '{Read,Grep,Glob,Bash,Write}', '{}', '{fila,publicar}', NULL, '{publicador}', '/equipe/portao-publicacao.jpg', '.claude/agents/portao-publicacao.md');
INSERT INTO public.agentes VALUES ('publicador', 'Pedro Almeida', 'publicador', 'distribuicao', 'construtor', 'Escreve as legendas do post e agenda a publicação no Instagram e no Facebook.', 'Pontual; vive no calendário.', 'Prepara e agenda a publicação dos Reels da Korvu no Instagram e no Facebook — escreve as legendas do post e os hooks, agenda na próxima vaga do calendário e acompanha a publicação automática. Usar em /publicar, /fila e quando um pacote entrar em 06-publicar/.', 'opus', '{Read,Write,Edit,Glob,Grep,Bash}', '{}', '{publicar}', 'portao-publicacao', '{}', '/equipe/publicador.jpg', '.claude/agents/publicador.md');
INSERT INTO public.agentes VALUES ('analista-de-metricas', 'Júlia Ramos', 'analista de dados', 'distribuicao', 'analista', 'Lê as métricas de cada Reel aos 5 dias e escreve o que funcionou para o próximo roteiro.', 'Só afirma com o número ao lado.', 'Lê as métricas de cada Reel publicado (5 dias depois), compara com os outros vídeos e com o roteiro (hook, estrutura, CTA, duração, palavra-chave) e escreve _controle/aprendizados.md — o que prendeu, o que fez salvar/comentar, o que não funcionou e 3–5 recomendações para o próximo roteiro, sempre com o número que sustenta. Usar quando o metricas.py ler um vídeo novo, quando o autor perguntar "como foi o vídeo X" ou antes de /ideias e /novo-video.', 'opus', '{Read,Write,Edit,Glob,Grep,Bash}', '{}', '{multiplicar}', NULL, '{}', '/equipe/analista-de-metricas.jpg', '.claude/agents/analista-de-metricas.md');
INSERT INTO public.agentes VALUES ('auditor-de-perfil', 'André Fontes', 'auditor de perfil', 'distribuicao', 'analista', 'Audita bio, grade e público do perfil e traça o plano para sair da bolha.', 'Olha o perfil como um desconhecido olharia.', 'Faz a auditoria completa do PERFIL @sua_conta (Instagram) e da Página do Facebook — bio, nome pesquisável, link, destaques, grade, seguidores × seguindo, de que países/cidades vêm os seguidores e quem os vídeos alcançam, alcance de não-seguidores, entrega no Facebook — e entrega o plano para SAIR DA BOLHA (público antigo do Brasil/PALOP) e ser conhecido mundialmente falando de IA, com conteúdo em português (decisão de 21/10: público não se define por país nem por "lusófono"). Usar quando o autor pedir análise do perfil/bio/configuração, quando o alcance cair, ou 1×/mês para comparar a evolução do público.', 'opus', '{Read,Write,Edit,Glob,Grep,Bash,WebSearch,WebFetch}', '{}', '{}', NULL, '{}', '/equipe/auditor-de-perfil.jpg', '.claude/agents/auditor-de-perfil.md');
INSERT INTO public.agentes VALUES ('portao-interface', 'Camila Freitas', 'gerente de tecnologia · portão da interface', 'tecnologia', 'portao', 'Abre cada tela no computador e no celular e confere se o que o autor vê está certo, legível e igual ao design aprovado.', 'Não aceita "compilou"; aceita "eu vi a tela".', 'PORTÃO GAUNTLET da INTERFACE do painel web (gerente de Tecnologia). Audita DUAS áreas, cada uma com o seu veredicto — `design` (o trabalho da designer-de-produto em painel/design/) e `interface` (o do engenheiro-frontend em painel/web/) — fidelidade ao design aprovado, telas olhadas de verdade em computador e celular, dados honestos na tela, gráficos, acessibilidade, chave nenhuma no navegador, tipos/lint/build — e devolve APROVADO ou BLOQUEADO preso aos arquivos. Invocar SEMPRE, sem perguntar, quando o design ou o código do painel mudar, ANTES de mostrar ao autor. Não desenha nem programa.', 'opus', '{Read,Grep,Glob,Bash,Write,Skill}', '{dataviz,design:accessibility-review}', '{}', NULL, '{engenheiro-frontend}', '/equipe/portao-interface.jpg', '.claude/agents/portao-interface.md');
INSERT INTO public.agentes VALUES ('portao-dados', 'Sérgio Lemos', 'portão dos dados', 'tecnologia', 'portao', 'Confere se o banco do painel é a cópia fiel dos arquivos do projeto e se nada lê ou escreve o que não devia.', 'Conta os arquivos ele mesmo antes de acreditar numa contagem.', 'PORTÃO GAUNTLET dos DADOS do painel web (Tecnologia). Audita o trabalho do engenheiro-backend — migrações versionadas, RLS e permissões, o sincronizador que só lê o projeto, contagens que batem com os arquivos, segredos, isolamento de outros Supabase locais, testes — e devolve APROVADO ou BLOQUEADO preso aos arquivos. Invocar SEMPRE, sem perguntar, quando painel/supabase, painel/sync ou painel/tests mudarem. Não programa nem migra.', 'opus', '{Read,Grep,Glob,Bash,Write,Skill,mcp__estudio-contexto__buscar,mcp__estudio-contexto__decisoes_sobre,mcp__estudio-contexto__contexto_do_video,mcp__estudio-contexto__contexto_do_projeto,mcp__estudio-contexto__vizinhos,mcp__estudio-contexto__quem_fiscaliza}', '{}', '{}', NULL, '{engenheiro-backend}', '/equipe/portao-dados.jpg', '.claude/agents/portao-dados.md');
INSERT INTO public.agentes VALUES ('designer-de-produto', 'Lia Monteiro', 'designer de produto (UI/UX)', 'tecnologia', 'construtor', 'Transforma as referências do autor no design system do painel e desenha cada tela antes de alguém programar.', 'Corta tudo o que não responde a uma pergunta do autor.', 'Designer de produto (UI/UX) do PAINEL WEB do Korvu Studio (painel/). Transforma as referências do autor no design system do painel (cores, tipografia, grade, componentes, gráficos) e desenha cada tela — com os estados vazio, carregando e erro — ANTES de alguém programar. Entrega em painel/design/ (especificação + maquete HTML de cada tela) e passa a vez ao engenheiro-frontend. Usar sempre que o painel ganhar tela, componente ou mudança de visual, e quando o autor trouxer referências. Não programa o app.', 'opus', '{Read,Write,Edit,Glob,Grep,Bash,Skill,WebSearch,WebFetch}', '{anthropic-skills:korvu-design-system,dataviz,design:accessibility-review,design:design-critique,design:design-handoff,design:design-system,design:ux-copy,frontend-design:frontend-design}', '{}', 'portao-interface', '{}', '/equipe/designer-de-produto.jpg', '.claude/agents/designer-de-produto.md');
INSERT INTO public.agentes VALUES ('engenheiro-frontend', 'Gabriel Torres', 'engenheiro front-end', 'tecnologia', 'construtor', 'Implementa as telas aprovadas em Next.js — componentes, gráficos, estados e celular — com os dados lidos só pelo servidor.', 'Detalhista com alinhamento e com o estado de erro que ninguém lembrou.', 'Engenheiro front-end do PAINEL WEB do Korvu Studio (painel/web — Next.js 15 App Router + TypeScript + Tailwind v4). Implementa exatamente o que a designer-de-produto aprovou em painel/design/ — telas, biblioteca de componentes, gráficos, estados vazio/carregando/erro, celular — lendo os dados só pelo servidor. Usar sempre que uma tela ou componente do painel for criado ou mudar. Não desenha (isso é da designer) nem mexe no banco (isso é do engenheiro-backend).', 'opus', '{Read,Write,Edit,Glob,Grep,Bash,Skill,WebSearch,WebFetch}', '{anthropic-skills:feature-based-nextjs,anthropic-skills:korvu-design-system,dataviz,design:accessibility-review,frontend-design:frontend-design}', '{}', 'portao-interface', '{}', '/equipe/engenheiro-frontend.jpg', '.claude/agents/engenheiro-frontend.md');
INSERT INTO public.agentes VALUES ('engenheiro-backend', 'Mateus Pacheco', 'engenheiro back-end e dados', 'tecnologia', 'construtor', 'Cuida do banco do painel, das migrações e do sincronizador que copia os arquivos do projeto para o painel.', 'Dado sem origem não entra no banco.', 'Engenheiro back-end e de dados do PAINEL WEB do Korvu Studio — o Supabase próprio do painel (painel/supabase: schema, migrações, RLS, permissões), o sincronizador que copia os arquivos do projeto para o banco (painel/sync), dados novos que as telas pedirem (métricas, histórico de seguidores) e, quando o autor quiser, login e nuvem para o domínio. Usar sempre que o banco, o sincronizador ou a origem de um dado do painel mudar. Não desenha nem faz tela.', 'opus', '{Read,Write,Edit,Glob,Grep,Bash,Skill,WebSearch,WebFetch}', '{}', '{}', 'portao-dados', '{}', '/equipe/engenheiro-backend.jpg', '.claude/agents/engenheiro-backend.md');


--
-- Data for Name: videos; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.videos VALUES ('2026-10-27-resumir-reunioes', 'Resumir reuniões com IA', 'produtividade', 'narrativo', 'ATA', 'publicado', '2026-10-29T19:02:00-03:00', '[{"em": "2026-10-19T10:00:00-03:00", "nota": "roteiro v1", "estado": "roteiro"}, {"em": "2026-10-26T10:00:00-03:00", "nota": "gravado", "estado": "gravacao"}, {"em": "2026-10-27T10:00:00-03:00", "nota": "EDL v1", "estado": "edicao"}, {"em": "2026-10-28T18:00:00-03:00", "nota": "pacote QA PASS", "estado": "pronto"}, {"em": "2026-10-28T19:00:00-03:00", "nota": "fila", "estado": "agendado"}, {"em": "2026-10-29T19:02:00-03:00", "nota": "IG + FB", "estado": "publicado"}]', true, 1, 3920000000, '2026-10-26 18:30:00+00', true, '2026-10-26 21:01:00+00', false, true, 2, 'ATA', 0, '2026-10-27', 'Resumir reuniões com IA', 1, 0, 0, 3920000000);
INSERT INTO public.videos VALUES ('2026-11-06-planilha-com-ia', 'Planilha com IA, sem fórmula', 'tutoriais-rapidos', 'narrativo', 'TABELA', 'agendado', '2026-11-10T09:00:00-03:00', '[{"em": "2026-10-31T10:00:00-03:00", "nota": "roteiro v1", "estado": "roteiro"}, {"em": "2026-11-06T10:00:00-03:00", "nota": "gravado", "estado": "gravacao"}, {"em": "2026-11-07T10:00:00-03:00", "nota": "EDL v1", "estado": "edicao"}, {"em": "2026-11-09T18:00:00-03:00", "nota": "pacote QA PASS", "estado": "pronto"}, {"em": "2026-11-10T09:00:00-03:00", "nota": "fila", "estado": "agendado"}]', true, 2, 4050000000, '2026-11-06 18:50:00+00', true, '2026-11-06 21:02:00+00', false, true, 1, 'TABELA', 1, '2026-11-06', 'Planilha com IA, sem fórmula', 2, 0, 0, 4050000000);
INSERT INTO public.videos VALUES ('2026-11-10-prompt-claro', 'O prompt claro em três partes', 'tutoriais-rapidos', 'narrativo', 'PROMPT', 'edicao', '2026-11-11T11:00:00-03:00', '[{"em": "2026-11-03T10:00:00-03:00", "nota": "roteiro v1", "estado": "roteiro"}, {"em": "2026-11-05T10:00:00-03:00", "nota": "roteiro v3 (dramaturgo)", "estado": "roteiro"}, {"em": "2026-11-10T16:00:00-03:00", "nota": "gravado em 2 partes", "estado": "gravacao"}, {"em": "2026-11-11T11:00:00-03:00", "nota": "EDL v1 aguardando aprovação", "estado": "edicao"}]', true, 2, 6966000000, '2026-11-10 18:50:00+00', false, '2026-11-10 21:02:00+00', false, true, 3, 'PROMPT', 2, '2026-11-10', 'O prompt claro em três partes', 2, 0, 0, 6966000000);
INSERT INTO public.videos VALUES ('2026-11-19-ia-no-atendimento', 'IA no atendimento do pequeno negócio', 'pequenos-negocios', 'narrativo', 'RESPOSTA', 'roteiro', '2026-11-11T10:00:00-03:00', '[{"em": "2026-11-11T10:00:00-03:00", "nota": "roteiro v1", "estado": "roteiro"}]', false, 0, 0, NULL, false, NULL, false, true, 1, 'RESPOSTA', 0, '2026-11-19', 'IA no atendimento do pequeno negócio', 0, 0, 0, 0);


--
-- Data for Name: animacoes; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.animacoes VALUES ('2026-11-10-prompt-claro/E01', '2026-11-10-prompt-claro', 'E01', 'Pedido vago × pedido claro', '{L03,L04}', 'split', 7.2, '2026-11-10-prompt-claro', false, NULL, 'videos/2026-11-10-prompt-claro/animacoes/E01/brief.md');


--
-- Data for Name: biblioteca_materiais; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.biblioteca_materiais VALUES ('2026-10-27-resumir-reunioes:dossie', '2026-10-27-resumir-reunioes', 'dossie', 'dossiê de pesquisa', 'videos/2026-10-27-resumir-reunioes/material', 'pesquisador-de-material', NULL, false);
INSERT INTO public.biblioteca_materiais VALUES ('2026-10-27-resumir-reunioes:pdf:modelo-de-ata.pdf', '2026-10-27-resumir-reunioes', 'pdf', 'Modelo de ata', 'videos/2026-10-27-resumir-reunioes/material/modelo-de-ata.pdf', 'produtor-de-material', NULL, false);
INSERT INTO public.biblioteca_materiais VALUES ('2026-11-06-planilha-com-ia:pdf:dez-pedidos-de-planilha.pdf', '2026-11-06-planilha-com-ia', 'pdf', 'Dez pedidos de planilha', 'videos/2026-11-06-planilha-com-ia/material/dez-pedidos-de-planilha.pdf', 'produtor-de-material', NULL, false);
INSERT INTO public.biblioteca_materiais VALUES ('2026-11-06-planilha-com-ia:dossie', '2026-11-06-planilha-com-ia', 'dossie', 'dossiê de pesquisa', 'videos/2026-11-06-planilha-com-ia/material', 'pesquisador-de-material', NULL, false);
INSERT INTO public.biblioteca_materiais VALUES ('2026-11-10-prompt-claro:dossie', '2026-11-10-prompt-claro', 'dossie', 'dossiê de pesquisa', 'videos/2026-11-10-prompt-claro/material', 'pesquisador-de-material', NULL, false);
INSERT INTO public.biblioteca_materiais VALUES ('2026-11-10-prompt-claro:pdf:prompt-em-tres-partes.pdf', '2026-11-10-prompt-claro', 'pdf', 'Prompt em tres partes', 'videos/2026-11-10-prompt-claro/material/prompt-em-tres-partes.pdf', 'produtor-de-material', NULL, false);
INSERT INTO public.biblioteca_materiais VALUES ('2026-11-10-prompt-claro:extras', '2026-11-10-prompt-claro', 'extras', 'cenas extras', 'videos/2026-11-10-prompt-claro/brutos/extras', 'produtor-de-extras', 'videos/2026-11-10-prompt-claro/brutos/extras/E02.png', false);
INSERT INTO public.biblioteca_materiais VALUES ('2026-11-19-ia-no-atendimento:dossie', '2026-11-19-ia-no-atendimento', 'dossie', 'dossiê de pesquisa', 'videos/2026-11-19-ia-no-atendimento/material', 'pesquisador-de-material', NULL, false);
INSERT INTO public.biblioteca_materiais VALUES ('2026-11-19-ia-no-atendimento:pdf:modelos-de-resposta.pdf', '2026-11-19-ia-no-atendimento', 'pdf', 'Modelos de resposta', 'videos/2026-11-19-ia-no-atendimento/material/modelos-de-resposta.pdf', 'produtor-de-material', NULL, false);


--
-- Data for Name: biblioteca_arquivos; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.biblioteca_arquivos VALUES ('videos/2026-10-27-resumir-reunioes/material/dossie.md', '2026-10-27-resumir-reunioes:dossie', '2026-10-27-resumir-reunioes', 'material', '.md', 'documento', 126, '2026-10-13 13:00:00+00', false, false);
INSERT INTO public.biblioteca_arquivos VALUES ('videos/2026-10-27-resumir-reunioes/material/fontes.json', '2026-10-27-resumir-reunioes:dossie', '2026-10-27-resumir-reunioes', 'material', '.json', 'pesquisa', 74, '2026-10-13 13:00:00+00', false, false);
INSERT INTO public.biblioteca_arquivos VALUES ('videos/2026-10-27-resumir-reunioes/material/modelo-de-ata.pdf', '2026-10-27-resumir-reunioes:pdf:modelo-de-ata.pdf', '2026-10-27-resumir-reunioes', 'material', '.pdf', 'documento', 889, '2026-10-13 13:00:00+00', false, false);
INSERT INTO public.biblioteca_arquivos VALUES ('videos/2026-11-06-planilha-com-ia/material/dez-pedidos-de-planilha.pdf', '2026-11-06-planilha-com-ia:pdf:dez-pedidos-de-planilha.pdf', '2026-11-06-planilha-com-ia', 'material', '.pdf', 'documento', 897, '2026-10-13 13:00:00+00', false, false);
INSERT INTO public.biblioteca_arquivos VALUES ('videos/2026-11-06-planilha-com-ia/material/dossie.md', '2026-11-06-planilha-com-ia:dossie', '2026-11-06-planilha-com-ia', 'material', '.md', 'documento', 131, '2026-10-13 13:00:00+00', false, false);
INSERT INTO public.biblioteca_arquivos VALUES ('videos/2026-11-06-planilha-com-ia/material/fontes.json', '2026-11-06-planilha-com-ia:dossie', '2026-11-06-planilha-com-ia', 'material', '.json', 'pesquisa', 74, '2026-10-13 13:00:00+00', false, false);
INSERT INTO public.biblioteca_arquivos VALUES ('videos/2026-11-10-prompt-claro/material/dossie.md', '2026-11-10-prompt-claro:dossie', '2026-11-10-prompt-claro', 'material', '.md', 'documento', 132, '2026-10-13 13:00:00+00', false, false);
INSERT INTO public.biblioteca_arquivos VALUES ('videos/2026-11-10-prompt-claro/material/fontes.json', '2026-11-10-prompt-claro:dossie', '2026-11-10-prompt-claro', 'material', '.json', 'pesquisa', 74, '2026-10-13 13:00:00+00', false, false);
INSERT INTO public.biblioteca_arquivos VALUES ('videos/2026-11-10-prompt-claro/material/prompt-em-tres-partes.pdf', '2026-11-10-prompt-claro:pdf:prompt-em-tres-partes.pdf', '2026-11-10-prompt-claro', 'material', '.pdf', 'documento', 898, '2026-10-13 13:00:00+00', false, false);
INSERT INTO public.biblioteca_arquivos VALUES ('videos/2026-11-10-prompt-claro/brutos/extras/E02.png', '2026-11-10-prompt-claro:extras', '2026-11-10-prompt-claro', 'brutos/extras', '.png', 'imagem', 234, '2026-10-13 13:00:00+00', false, false);
INSERT INTO public.biblioteca_arquivos VALUES ('videos/2026-11-19-ia-no-atendimento/material/dossie.md', '2026-11-19-ia-no-atendimento:dossie', '2026-11-19-ia-no-atendimento', 'material', '.md', 'documento', 139, '2026-10-13 13:00:00+00', true, false);
INSERT INTO public.biblioteca_arquivos VALUES ('videos/2026-11-19-ia-no-atendimento/material/fontes.json', '2026-11-19-ia-no-atendimento:dossie', '2026-11-19-ia-no-atendimento', 'material', '.json', 'pesquisa', 74, '2026-10-13 13:00:00+00', true, false);
INSERT INTO public.biblioteca_arquivos VALUES ('videos/2026-11-19-ia-no-atendimento/material/modelos-de-resposta.pdf', '2026-11-19-ia-no-atendimento:pdf:modelos-de-resposta.pdf', '2026-11-19-ia-no-atendimento', 'material', '.pdf', 'documento', 907, '2026-10-13 13:00:00+00', true, false);


--
-- Data for Name: biblioteca_mais_utilizados; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.biblioteca_mais_utilizados VALUES ('00-marca/voz-autor.md', 'Voz do autor', 4, 'roteiros', 'vídeos com videos/<slug>/roteiro.json (videos.tem_roteiro): todo roteiro é escrito a partir da voz do autor (CLAUDE.md)', false);
INSERT INTO public.biblioteca_mais_utilizados VALUES ('00-marca/cor/luts/korvu-look-v5.cube', 'Look da Korvu v5', 3, 'vídeos gravados', 'vídeos com gravação em brutos/principal/ (videos.gravado): a cor da marca vai em todo vídeo gravado — look ativo v5 (docs/decisoes.md, 18/09)', true);
INSERT INTO public.biblioteca_mais_utilizados VALUES ('00-marca/cor/luts/entrada-camera.cube', 'LUT de entrada V-Log', 3, 'vídeos gravados', 'vídeos com gravação em brutos/principal/ (videos.gravado): toda imagem da câmera entra por ela', true);
INSERT INTO public.biblioteca_mais_utilizados VALUES ('scripts/gerar_material_pdf.py', 'Molde do PDF da palavra', 4, 'PDFs da palavra', 'PDFs de videos/<slug>/material/ (biblioteca_materiais, grupo pdf): todo PDF da palavra sai do molde', true);


--
-- Data for Name: biblioteca_referencias; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.biblioteca_referencias VALUES ('00-marca/referencias', 0, 0);
INSERT INTO public.biblioteca_referencias VALUES ('painel/referencias', 0, 0);


--
-- Data for Name: calendario_vagas; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.calendario_vagas VALUES (2, 'terca', '19:00:00', 'America/Sao_Paulo');
INSERT INTO public.calendario_vagas VALUES (4, 'quinta', '19:00:00', 'America/Sao_Paulo');
INSERT INTO public.calendario_vagas VALUES (6, 'sabado', '11:00:00', 'America/Sao_Paulo');


--
-- Data for Name: cambio; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cambio VALUES ('GBP', '2026-10-23', 0.746500, 'XE, média de mercado');


--
-- Data for Name: capa_estilos; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.capa_estilos VALUES ('serifa-e-rabisco', 0, 'Serifa + rabisco', 'A palavra-chave em Playfair itálico, com um rabisco por baixo.', '00-marca/referencias/capas/estilo-editorial-escuro.md', false, false);
INSERT INTO public.capa_estilos VALUES ('grotesca-e-sublinhado', 1, 'Grotesca + sublinhado', 'Título grotesco, a última palavra sublinhada (cinza ou laranja). Uma capa por variante.', NULL, NULL, true);


--
-- Data for Name: capa_estilos_exemplos; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.capa_estilos_exemplos VALUES ('serifa-e-rabisco', 0, '2026-10-27-resumir-reunioes', '07-publicados', '07-publicados/2026-10-27-resumir-reunioes/capa/capa.png', '2026-10-27-resumir-reunioes');
INSERT INTO public.capa_estilos_exemplos VALUES ('grotesca-e-sublinhado', 0, '2026-11-06-planilha-com-ia', '06-publicar', '06-publicar/2026-11-06-planilha-com-ia/capa/capa.png', '2026-11-06-planilha-com-ia');


--
-- Data for Name: execucoes; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.execucoes VALUES ('sessao-demo-1.jsonl', 'principal', 'sessao-demo-1', NULL, NULL, NULL, 'diretor', 'direcao', NULL, NULL, NULL, NULL, '2026-10-23 11:00:00+00', '2026-11-11 12:00:00+00', true, '2026-11-12 22:31:57.58142+00');
INSERT INTO public.execucoes VALUES ('sessao-demo-1/subagents/agent-demo01.jsonl', 'subagente', 'sessao-demo-1', 'demo01', NULL, 'roteirista', 'roteirista', 'roteiro', 'roteiro v1 (demo)', 1, true, '2026-11-19-ia-no-atendimento', '2026-11-10 13:05:00+00', '2026-11-10 13:40:00+00', true, '2026-11-12 22:31:57.58142+00');
INSERT INTO public.execucoes VALUES ('sessao-demo-1/subagents/agent-demo02.jsonl', 'subagente', 'sessao-demo-1', 'demo02', NULL, 'editor-de-video', 'editor-de-video', 'pos', 'EDL v1 (demo)', 1, true, '2026-11-10-prompt-claro', '2026-11-11 14:10:00+00', '2026-11-11 14:10:00+00', true, '2026-11-12 22:31:57.58142+00');
INSERT INTO public.execucoes VALUES ('sessao-demo-2.jsonl', 'principal', 'sessao-demo-2', NULL, NULL, NULL, 'diretor', 'direcao', NULL, NULL, NULL, NULL, '2026-11-09 15:03:00+00', '2026-11-09 15:20:00+00', true, '2026-11-12 22:31:57.58142+00');
INSERT INTO public.execucoes VALUES ('sessao-demo-2/subagents/agent-demo03.jsonl', 'subagente', 'sessao-demo-2', 'demo03', NULL, 'publicador', 'publicador', 'distribuicao', 'legendas do post (demo)', 1, true, '2026-11-06-planilha-com-ia', '2026-11-09 15:08:00+00', '2026-11-09 15:08:00+00', true, '2026-11-12 22:31:57.58142+00');


--
-- Data for Name: fila; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fila VALUES ('2026-11-06-planilha-com-ia', '2026-11-15 22:00:00+00', '{instagram,facebook}', 'agendado', 'SS_PERFORMANCE', 'TABELA', false, false, 'videos/2026-11-06-planilha-com-ia', true, '[]', '2026-11-06-planilha-com-ia');


--
-- Data for Name: fontes; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.fontes VALUES ('Geist', 0, 'Geist', 'normal', '{400,500,600,700,800,900}', 'Títulos e legendas dos Reels; o painel.', false, true);
INSERT INTO public.fontes VALUES ('Bricolage Grotesque', 1, 'BricolageGrotesque', 'normal', '{800}', 'Cartão do CTA e o PDF da palavra.', false, true);
INSERT INTO public.fontes VALUES ('Inter', 2, 'Inter', 'normal', '{500,600}', 'Texto editorial dos cartões.', false, true);
INSERT INTO public.fontes VALUES ('Playfair Display', 3, 'PlayfairDisplay', 'italico', '{400,500}', 'A palavra em itálico da capa.', false, true);
INSERT INTO public.fontes VALUES ('Inter Tight', 4, 'InterTight', 'normal', '{500,800}', 'Reserva da Geist nas legendas e títulos.', true, false);


--
-- Data for Name: legenda_estilos; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.legenda_estilos VALUES ('texto-selecionado', 0, 'Texto Selecionado', 'As palavras entram no ritmo da fala, com um realce de seleção, a frase de impacto em grotesca pesada e o rabisco na palavra-chave.', '00-marca/referencias/legendas/estilo-selecao.md', false, true);


--
-- Data for Name: looks; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.looks VALUES ('rec709', 0, 'base', 'Só a conversão', NULL, '{}', '{}', NULL, NULL, '2026-09-15', '00-marca/cor/luts/entrada-camera.json', '{"cube": "00-marca/cor/luts/entrada-camera.cube", "nome": "entrada-camera", "saida": {"espaco": "Rec.709 / BT.1886 (gamma 2.4), RGB 0–1 full range", "intencao": "equivalente técnico à LUT V-709 da Panasonic (não é a oficial)"}, "camera": "Panasonic Lumix S5IIX", "interp": "tetrahedral", "metodo": "colour.log_decoding_VLog → linear V-Gamut → RGB_to_RGB V-Gamut→BT.709 (D65, sem CAT) → exposição (18% fica 18%) → soft-clip de gamut (RGC simplificado) → curva fílmica por canal f=m·(x/(x+s0))^p, g=f²/(f+t) com reconstrução parcial da matiz → inverso BT.1886 (g^(1/2.4)) → clamp 0–1", "entrada": {"nota": "super-brancos > 940 (> +6.8 stops) cortados; S5IIX satura antes (~+6 stops)", "curva": "Panasonic V-Log", "gamut": "V-Gamut", "dominio": "RGB 0–1 como o lut3d vê após yuv limited (tv) → RGB full (in_range=tv)", "x_para_vlog": "V = (64 + 876·x)/1023", "codigo_para_x": "x = (código10 − 64)/876"}, "tamanho": 65, "criado_em": "2026-09-15T18:28:00+01:00", "parametros": {"m": 1.011859, "p": 1.3, "t": 0.012, "s0": 0.630894, "cinza": 0.43, "gamut_limiar": 0.8, "gamut_limite": [1.2, 1.3, 1.3], "gamut_potencia": 1.2, "preservar_matiz": 0.7, "matriz_vgamut_para_709": [[1.806574, -0.695698, -0.110879], [-0.170089, 1.305955, -0.135865], [-0.025206, -0.154468, 1.179674]]}, "provisorio": true, "saida_neutros_codigo": {"+0 stops": 0.43, "+1 stops": 0.5703, "+2 stops": 0.7068, "+3 stops": 0.8189, "+4 stops": 0.897, "+5 stops": 0.9446, "+6 stops": 0.9712, "-2 stops": 0.2012, "-4 stops": 0.0685, "-6 stops": 0.0175, "+6.8 stops": 0.9832, "+2.32 stops": 0.7461, "preto V-Log (código 128)": 0.0}}', '00-marca/cor/luts/entrada-camera.cube', '36f44ee9a1ae44be424cecb583e4439bdbbca8b59f4aa9d272813125645ffc25', NULL, NULL, NULL, NULL, NULL, 'V-Log para Rec.709, ainda sem look.');
INSERT INTO public.looks VALUES ('v4', 1, 'look', 'Look v4', 'arquivado', '{arquivados}', '{13}', false, NULL, '2026-09-15', '00-marca/cor/luts/korvu-look-v4.json', '{"cube": "00-marca/cor/luts/korvu-look-v4.cube", "nome": "korvu-look-v4", "avisos": [], "espaco": "Rec.709 / gamma 2.4 (SDR), valores 0–1", "interp": "tetrahedral", "metodo": "mkl", "versao": "v4", "amostra": {"frames": ["25.61s", "41.51s", "57.41s", "73.31s", "89.20s", "105.10s", "121.00s", "136.90s", "152.79s", "168.69s", "184.59s", "200.49s", "216.38s", "232.28s", "248.18s", "264.08s", "279.97s", "295.87s", "311.77s", "327.67s"], "arquivo": "videos/2026-01-05-exemplo/brutos/principal/PRAQ0967.MOV", "dimensoes_frame": [540, 1024], "transformacao_entrada": "camera: V-Log/V-Gamut (yuv422p10le, yuv full range (Lumix V-Log 0–1023) → gbrp16le) → Rec.709 via 00-marca/cor/luts/entrada-camera.cube (gerada, provisória)"}, "tamanho": 33, "aprovada": false, "criado_em": "2026-09-15T22:40:31+01:00", "parametros": {"mkl": {"M": [[0.760573, 0.183109, 0.290365], [0.183109, 1.019253, 0.016923], [0.290365, 0.016923, 0.786291]], "mu_r": [0.346511, 0.371264, 0.318585], "mu_s": [0.565225, 0.425444, 0.317083]}}, "aprovada_em": null, "cinza_saida": {"0%": 0.0, "18%": 0.1013, "50%": 0.4538, "100%": 0.9972}, "intensidade": 0.6, "referencias": [{"sha1": "7ff84a1985f0", "arquivo": "ref-tenet-01a.jpg"}, {"sha1": "9d311079c23d", "arquivo": "ref-tenet-01b.jpg"}, {"sha1": "9629436b6d68", "arquivo": "ref-tenet-01d.jpg"}], "antes_depois": "00-marca/cor/analises/v4-antes-depois.png", "estatisticas": {"amostra": {"p02": 0.1189, "p98": 0.7925, "rgb_medio": [0.5645, 0.4248, 0.3165], "luma_media": 0.4467, "contraste_std": 0.2197, "saturacao_media": 0.496, "pretos_esmagados_pct": 0.0, "brancos_estourados_pct": 0.0}, "referencia": {"p02": 0.0292, "p98": 0.8901, "rgb_medio": [0.3462, 0.3709, 0.3183], "luma_media": 0.3619, "contraste_std": 0.2661, "saturacao_media": 0.2708, "pretos_esmagados_pct": 0.02, "brancos_estourados_pct": 0.0}, "amostra_com_lut": {"p02": 0.0246, "p98": 0.7846, "rgb_medio": [0.4337, 0.3922, 0.3174], "luma_media": 0.3956, "contraste_std": 0.2473, "saturacao_media": 0.3523, "pretos_esmagados_pct": 1.15, "brancos_estourados_pct": 0.0}}, "alvo_primaria": {"luma": 0.44657, "nota": "domínio de entrada da LUT: é a exposição/neutro que a LUT leva até à média da referência. aplicar_cor.py ajusta cada take para cá.", "confiavel": true, "frac_pele": 0.932, "rgb_neutro": [0.22375, 0.14511, 0.08111], "frac_recortado": 0.0003, "frac_meios_tons": 0.0463}, "proteger_pele": 0.0, "dominio_entrada": "Rec.709 depois da LUT de entrada (câmera V-Log passa primeiro por V-Log→709; o aplicar_cor aplica a mesma entrada antes desta LUT)"}', '00-marca/cor/luts/korvu-look-v4.cube', '225659a3e54f9af0e74c977a7527ef13bab56616f43d7ff25cc7208d97f49946', NULL, NULL, NULL, NULL, NULL, 'O look “Tenet”, frio e contido; nunca aprovado.');
INSERT INTO public.looks VALUES ('v5', 2, 'look', 'Look v5 · WAY', 'em_uso', '{versao_ativa}', '{5}', true, '2026-09-18', '2026-09-15', '00-marca/cor/luts/korvu-look-v5.json', '{"cube": "00-marca/cor/luts/korvu-look-v5.cube", "nome": "WAY v5 — ATIVO (escolhido pelo autor em 2026-09-18, comparação v5 x v11)", "avisos": [], "espaco": "Rec.709 / gamma 2.4 (SDR), valores 0–1", "interp": "tetrahedral", "metodo": "mkl", "versao": "v5", "amostra": {"frames": ["25.61s", "41.51s", "57.41s", "73.31s", "89.20s", "105.10s", "121.00s", "136.90s", "152.79s", "168.69s", "184.59s", "200.49s", "216.38s", "232.28s", "248.18s", "264.08s", "279.97s", "295.87s", "311.77s", "327.67s"], "arquivo": "videos/2026-01-05-exemplo/brutos/principal/PRAQ0967.MOV", "dimensoes_frame": [540, 1024], "transformacao_entrada": "camera: V-Log/V-Gamut (yuv422p10le, yuv full range (Lumix V-Log 0–1023) → gbrp16le) → Rec.709 via 00-marca/cor/luts/entrada-camera.cube (gerada, provisória)"}, "tamanho": 33, "aprovada": true, "criado_em": "2026-09-15T23:03:13+01:00", "parametros": {"mkl": {"M": [[0.924022, -0.13572, -0.069853], [-0.13572, 0.881075, 0.072799], [-0.069853, 0.072799, 0.653743]], "mu_r": [0.23298, 0.241123, 0.232775], "mu_s": [0.564956, 0.425521, 0.317272]}}, "aprovada_em": "2026-09-18", "cinza_saida": {"0%": 0.0017, "18%": 0.0897, "50%": 0.3553, "100%": 0.7801}, "intensidade": 0.7, "referencias": [{"sha1": "781bc1620c48", "arquivo": "ref-way-01a.jpg"}, {"sha1": "097643eb976f", "arquivo": "ref-way-01b.jpg"}, {"sha1": "46ce44457153", "arquivo": "ref-way-01c.jpg"}], "antes_depois": "00-marca/cor/analises/v5-antes-depois.png", "estatisticas": {"amostra": {"p02": 0.1189, "p98": 0.7925, "rgb_medio": [0.5645, 0.4248, 0.3165], "luma_media": 0.4467, "contraste_std": 0.2197, "saturacao_media": 0.496, "pretos_esmagados_pct": 0.0, "brancos_estourados_pct": 0.0}, "referencia": {"p02": 0.0224, "p98": 0.5743, "rgb_medio": [0.246, 0.2675, 0.256], "luma_media": 0.2621, "contraste_std": 0.1818, "saturacao_media": 0.3348, "pretos_esmagados_pct": 0.0, "brancos_estourados_pct": 0.0}, "amostra_com_lut": {"p02": 0.0296, "p98": 0.5982, "rgb_medio": [0.3331, 0.2958, 0.2575], "luma_media": 0.301, "contraste_std": 0.1871, "saturacao_media": 0.3704, "pretos_esmagados_pct": 0.0, "brancos_estourados_pct": 0.0}}, "alvo_primaria": {"luma": 0.44657, "nota": "domínio de entrada da LUT: é a exposição/neutro que a LUT leva até à média da referência. aplicar_cor.py ajusta cada take para cá.", "confiavel": true, "frac_pele": 0.932, "rgb_neutro": [0.22375, 0.14511, 0.08111], "frac_recortado": 0.0003, "frac_meios_tons": 0.0463}, "proteger_pele": 0.0, "dominio_entrada": "Rec.709 depois da LUT de entrada (câmera V-Log passa primeiro por V-Log→709; o aplicar_cor aplica a mesma entrada antes desta LUT)", "grao_recomendado": 0.3}', '00-marca/cor/luts/korvu-look-v5.cube', '8f92f7e9b30b5ce7893d4745c5b1d33e441f161d24c5cfc626d7b312bbb21fdd', 23.2, '2026-09-18', 'chatgpt02.MOV (regravação, exposição corrigida)', NULL, NULL, 'O escolhido: “a cor da pele ficou muito boa”.');
INSERT INTO public.looks VALUES ('v11', 3, 'look', 'Look v11', 'alternativa', '{alternativa_medida}', '{9}', false, '2026-09-17', '2026-09-17', '00-marca/cor/luts/korvu-look-v11.json', '{"nome": "WAY v5 + pele recuperada (1.0 stop)", "tipo": "parametrico", "motivo": "APROVADA pelo autor em 2026-09-17: rosto 22,8 IRE, preto 1,3 IRE, branco 98 IRE (sem estourar) · 2026-09-18: DESMARCADA como padrão — o autor comparou v5 x v11 na regravação e escolheu o v5 pela pele. Medições continuam a favor do v11 (rosto 40,9 vs 23,2 IRE); a escolha é dele e a pele tem prioridade no cor.md.", "versao": "v11", "aprovada": false, "criado_em": "2026-09-17", "parametros": {"sat": 0.72, "alta": "0.010,0.004,-0.010", "base": "00-marca/cor/luts/korvu-look-v5.cube", "nome": "WAY v5 + pele recuperada (1.0 stop)", "pivo": 0.42, "preto": 0.0, "branco": 1.0, "neutro": "0,0,0", "sombra": "-0.030,0.012,0.004", "pele_sat": 1.0, "contraste": 1.0, "exposicao": 1.0, "pele_calor": 0.012, "pele_sigma": 28.0, "pele_centro": 35.0, "neutro_croma": 0.06, "pele_croma_min": 0.015, "pele_croma_rampa": 0.06}, "aprovada_em": "2026-09-17"}', '00-marca/cor/luts/korvu-look-v11.cube', '508f740cdbc98eea110aaa1e831c2bd12d1bf4acea317d21b004670604fa075d', 40.9, '2026-09-18', 'chatgpt02.MOV (regravação, exposição corrigida)', NULL, NULL, 'v5 com a pele recuperada (+1 stop). Aprovado como alternativa.');


--
-- Data for Name: publicacoes; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.publicacoes VALUES ('2026-10-27-resumir-reunioes', '2026-10-29 22:02:00+00', 'Resumir reuniões com IA', 'produtividade', 'ATA', 41.6, 'SS_PERFORMANCE', 'https://www.instagram.com/reel/DEMO0001/', 'https://www.facebook.com/reel/1000000001/', '2026-10-27-resumir-reunioes', '{instagram,facebook}', 'publicado');


--
-- Data for Name: metricas; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.metricas VALUES ('2026-10-27-resumir-reunioes', '2026-10-30 12:30:00+00', 0.6, 1840, 1612, 14.8, 35.6, 96, 41, 133, 22, 420, 9.1, 33, 31, false);
INSERT INTO public.metricas VALUES ('2026-10-27-resumir-reunioes', '2026-11-03 12:30:00+00', 4.6, 6210, 5380, 16.2, 38.9, 288, 117, 512, 74, 1310, 9.8, 98, 95, false);


--
-- Data for Name: modelos_descricao; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.modelos_descricao VALUES ('claude-opus-5-5', 0, 'O padrão do dia a dia. A maior parte do trabalho; desde 24 out, o padrão de todos os agentes, portões incluídos.', true);
INSERT INTO public.modelos_descricao VALUES ('claude-sonnet-5-5', 1, 'Mais rápido e mais barato. Era o modelo de 11 agentes até 24 out.', true);
INSERT INTO public.modelos_descricao VALUES ('claude-fable-5-1', 2, 'O mais capaz da Anthropic, e o mais caro. Usado pelo Atlas (a direção) em parte das sessões.', true);


--
-- Data for Name: nao_publicar; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: perfil_snapshots; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.perfil_snapshots VALUES ('2026-10-15 12:30:00+00', 1180, 210, 18, 28, 900, 2700, 60, 140, 80, 405, 495, 310, 6);
INSERT INTO public.perfil_snapshots VALUES ('2026-10-22 12:30:00+00', 1236, 210, 19, 28, 1540, 4620, 85, 230, 110, 616, 924, 322, 9);
INSERT INTO public.perfil_snapshots VALUES ('2026-10-29 12:30:00+00', 1302, 210, 20, 28, 2180, 6540, 110, 320, 140, 763, 1417, 334, 12);
INSERT INTO public.perfil_snapshots VALUES ('2026-11-05 12:30:00+00', 1415, 210, 21, 28, 2820, 8460, 135, 410, 170, 846, 1974, 346, 15);
INSERT INTO public.perfil_snapshots VALUES ('2026-11-12 12:30:00+00', 1488, 210, 22, 28, 3460, 10380, 160, 500, 200, 865, 2595, 358, 18);


--
-- Data for Name: perfil_demografia; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'seguidores', 'country', 'BR', 731);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'seguidores', 'country', 'PT', 165);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'seguidores', 'country', 'US', 94);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'seguidores', 'country', 'ES', 47);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'seguidores', 'city', 'São Paulo, São Paulo', 212);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'seguidores', 'city', 'Rio de Janeiro, Rio de Janeiro', 106);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'seguidores', 'city', 'Lisboa, Lisboa', 70);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'seguidores', 'age', '18-24', 247);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'seguidores', 'age', '25-34', 460);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'seguidores', 'age', '35-44', 283);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'seguidores', 'age', '45-54', 118);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'seguidores', 'gender', 'F', 554);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'seguidores', 'gender', 'M', 601);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'alcancados', 'country', 'BR', 522);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'alcancados', 'country', 'PT', 108);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'alcancados', 'country', 'US', 81);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'alcancados', 'gender', 'F', 441);
INSERT INTO public.perfil_demografia VALUES ('2026-10-15 12:30:00+00', 'alcancados', 'gender', 'M', 450);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'seguidores', 'country', 'BR', 766);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'seguidores', 'country', 'PT', 173);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'seguidores', 'country', 'US', 98);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'seguidores', 'country', 'ES', 49);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'seguidores', 'city', 'São Paulo, São Paulo', 222);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'seguidores', 'city', 'Rio de Janeiro, Rio de Janeiro', 111);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'seguidores', 'city', 'Lisboa, Lisboa', 74);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'seguidores', 'age', '18-24', 259);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'seguidores', 'age', '25-34', 482);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'seguidores', 'age', '35-44', 296);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'seguidores', 'age', '45-54', 123);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'seguidores', 'gender', 'F', 580);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'seguidores', 'gender', 'M', 630);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'alcancados', 'country', 'BR', 893);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'alcancados', 'country', 'PT', 184);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'alcancados', 'country', 'US', 138);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'alcancados', 'gender', 'F', 754);
INSERT INTO public.perfil_demografia VALUES ('2026-10-22 12:30:00+00', 'alcancados', 'gender', 'M', 770);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'seguidores', 'country', 'BR', 807);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'seguidores', 'country', 'PT', 182);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'seguidores', 'country', 'US', 104);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'seguidores', 'country', 'ES', 52);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'seguidores', 'city', 'São Paulo, São Paulo', 234);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'seguidores', 'city', 'Rio de Janeiro, Rio de Janeiro', 117);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'seguidores', 'city', 'Lisboa, Lisboa', 78);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'seguidores', 'age', '18-24', 273);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'seguidores', 'age', '25-34', 507);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'seguidores', 'age', '35-44', 312);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'seguidores', 'age', '45-54', 130);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'seguidores', 'gender', 'F', 611);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'seguidores', 'gender', 'M', 664);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'alcancados', 'country', 'BR', 1264);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'alcancados', 'country', 'PT', 261);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'alcancados', 'country', 'US', 196);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'alcancados', 'gender', 'F', 1068);
INSERT INTO public.perfil_demografia VALUES ('2026-10-29 12:30:00+00', 'alcancados', 'gender', 'M', 1090);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'seguidores', 'country', 'BR', 877);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'seguidores', 'country', 'PT', 198);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'seguidores', 'country', 'US', 113);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'seguidores', 'country', 'ES', 56);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'seguidores', 'city', 'São Paulo, São Paulo', 254);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'seguidores', 'city', 'Rio de Janeiro, Rio de Janeiro', 127);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'seguidores', 'city', 'Lisboa, Lisboa', 84);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'seguidores', 'age', '18-24', 297);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'seguidores', 'age', '25-34', 551);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'seguidores', 'age', '35-44', 339);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'seguidores', 'age', '45-54', 141);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'seguidores', 'gender', 'F', 665);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'seguidores', 'gender', 'M', 721);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'alcancados', 'country', 'BR', 1635);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'alcancados', 'country', 'PT', 338);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'alcancados', 'country', 'US', 253);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'alcancados', 'gender', 'F', 1381);
INSERT INTO public.perfil_demografia VALUES ('2026-11-05 12:30:00+00', 'alcancados', 'gender', 'M', 1410);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'seguidores', 'country', 'BR', 922);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'seguidores', 'country', 'PT', 208);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'seguidores', 'country', 'US', 119);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'seguidores', 'country', 'ES', 59);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'seguidores', 'city', 'São Paulo, São Paulo', 267);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'seguidores', 'city', 'Rio de Janeiro, Rio de Janeiro', 133);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'seguidores', 'city', 'Lisboa, Lisboa', 89);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'seguidores', 'age', '18-24', 312);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'seguidores', 'age', '25-34', 580);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'seguidores', 'age', '35-44', 357);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'seguidores', 'age', '45-54', 148);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'seguidores', 'gender', 'F', 699);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'seguidores', 'gender', 'M', 758);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'alcancados', 'country', 'BR', 2006);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'alcancados', 'country', 'PT', 415);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'alcancados', 'country', 'US', 311);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'alcancados', 'gender', 'F', 1695);
INSERT INTO public.perfil_demografia VALUES ('2026-11-12 12:30:00+00', 'alcancados', 'gender', 'M', 1730);


--
-- Data for Name: perfil_diario; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.perfil_diario VALUES ('2026-10-30', 'reach', 1040, '2026-10-31 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-10-30', 'views', 380, '2026-10-31 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-10-30', 'seguidores', 1415, '2026-10-31 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-10-30', 'profile_views', 12, '2026-10-31 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-10-31', 'reach', 177, '2026-11-01 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-10-31', 'views', 471, '2026-11-01 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-10-31', 'seguidores', 1420, '2026-11-01 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-10-31', 'profile_views', 19, '2026-11-01 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-01', 'reach', 214, '2026-11-02 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-01', 'views', 562, '2026-11-02 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-01', 'seguidores', 1425, '2026-11-02 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-01', 'profile_views', 26, '2026-11-02 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-02', 'reach', 251, '2026-11-03 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-02', 'views', 653, '2026-11-03 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-02', 'seguidores', 1430, '2026-11-03 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-02', 'profile_views', 33, '2026-11-03 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-03', 'reach', 288, '2026-11-04 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-03', 'views', 744, '2026-11-04 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-03', 'seguidores', 1435, '2026-11-04 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-03', 'profile_views', 15, '2026-11-04 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-04', 'reach', 325, '2026-11-05 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-04', 'views', 835, '2026-11-05 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-04', 'seguidores', 1440, '2026-11-05 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-04', 'profile_views', 22, '2026-11-05 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-05', 'reach', 142, '2026-11-06 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-05', 'views', 926, '2026-11-06 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-05', 'seguidores', 1445, '2026-11-06 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-05', 'profile_views', 29, '2026-11-06 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-06', 'reach', 179, '2026-11-07 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-06', 'views', 417, '2026-11-07 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-06', 'seguidores', 1450, '2026-11-07 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-06', 'profile_views', 36, '2026-11-07 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-07', 'reach', 216, '2026-11-08 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-07', 'views', 508, '2026-11-08 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-07', 'seguidores', 1455, '2026-11-08 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-07', 'profile_views', 18, '2026-11-08 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-08', 'reach', 253, '2026-11-09 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-08', 'views', 599, '2026-11-09 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-08', 'seguidores', 1460, '2026-11-09 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-08', 'profile_views', 25, '2026-11-09 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-09', 'reach', 290, '2026-11-10 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-09', 'views', 690, '2026-11-10 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-09', 'seguidores', 1465, '2026-11-10 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-09', 'profile_views', 32, '2026-11-10 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-10', 'reach', 327, '2026-11-11 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-10', 'views', 781, '2026-11-11 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-10', 'seguidores', 1470, '2026-11-11 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-10', 'profile_views', 14, '2026-11-11 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-11', 'reach', 144, '2026-11-12 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-11', 'views', 872, '2026-11-12 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-11', 'seguidores', 1475, '2026-11-12 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-11', 'profile_views', 21, '2026-11-12 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-12', 'reach', 181, '2026-11-13 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-12', 'views', 963, '2026-11-13 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-12', 'seguidores', 1480, '2026-11-13 12:30:00+00');
INSERT INTO public.perfil_diario VALUES ('2026-11-12', 'profile_views', 28, '2026-11-13 12:30:00+00');


--
-- Data for Name: portoes_estado; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.portoes_estado VALUES ('videos/2026-10-27-resumir-reunioes', '2026-10-27-resumir-reunioes', 'pauta', 'portao-pauta', 'aprovado', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('videos/2026-10-27-resumir-reunioes', '2026-10-27-resumir-reunioes', 'roteiro', 'revisor-de-roteiro', 'aprovado', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('videos/2026-10-27-resumir-reunioes', '2026-10-27-resumir-reunioes', 'imagem', 'portao-imagem', 'aprovado', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('videos/2026-10-27-resumir-reunioes', '2026-10-27-resumir-reunioes', 'corte', 'revisor-de-video', 'aprovado', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('videos/2026-11-06-planilha-com-ia', '2026-11-06-planilha-com-ia', 'pauta', 'portao-pauta', 'aprovado', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('videos/2026-11-06-planilha-com-ia', '2026-11-06-planilha-com-ia', 'roteiro', 'revisor-de-roteiro', 'aprovado', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('videos/2026-11-06-planilha-com-ia', '2026-11-06-planilha-com-ia', 'imagem', 'portao-imagem', 'aprovado', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('videos/2026-11-06-planilha-com-ia', '2026-11-06-planilha-com-ia', 'corte', 'revisor-de-video', 'aprovado', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('videos/2026-11-10-prompt-claro', '2026-11-10-prompt-claro', 'pauta', 'portao-pauta', 'aprovado', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('videos/2026-11-10-prompt-claro', '2026-11-10-prompt-claro', 'roteiro', 'revisor-de-roteiro', 'aprovado', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('videos/2026-11-10-prompt-claro', '2026-11-10-prompt-claro', 'imagem', 'portao-imagem', 'bloqueado', '["BLOQUEADO em 2026-11-11T15:00:00-03:00 (S0 0 · S1 1)"]', 1);
INSERT INTO public.portoes_estado VALUES ('videos/2026-11-10-prompt-claro', '2026-11-10-prompt-claro', 'corte', 'revisor-de-video', 'nao_se_aplica', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('videos/2026-11-19-ia-no-atendimento', '2026-11-19-ia-no-atendimento', 'pauta', 'portao-pauta', 'aprovado', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('videos/2026-11-19-ia-no-atendimento', '2026-11-19-ia-no-atendimento', 'roteiro', 'revisor-de-roteiro', 'aprovado', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('videos/2026-11-19-ia-no-atendimento', '2026-11-19-ia-no-atendimento', 'imagem', 'portao-imagem', 'nao_se_aplica', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('videos/2026-11-19-ia-no-atendimento', '2026-11-19-ia-no-atendimento', 'corte', 'revisor-de-video', 'nao_se_aplica', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('06-publicar/2026-11-06-planilha-com-ia', '2026-11-06-planilha-com-ia', 'publicacao', 'portao-publicacao', 'aprovado', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('painel', 'painel', 'design', 'portao-interface', 'nao_se_aplica', '[]', 0);
INSERT INTO public.portoes_estado VALUES ('painel', 'painel', 'interface', 'portao-interface', 'pendente', '["o portão ainda não rodou"]', 0);
INSERT INTO public.portoes_estado VALUES ('painel', 'painel', 'dados', 'portao-dados', 'pendente', '["o portão ainda não rodou"]', 0);


--
-- Data for Name: precos_modelo; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.precos_modelo VALUES ('claude-opus-5-5', 'Opus 5.5', 4.0000, 5.0000, 0.2000, 20.0000, 8.0000);
INSERT INTO public.precos_modelo VALUES ('claude-sonnet-5-5', 'Sonnet 5.5', 2.0000, 2.5000, 0.2000, 10.0000, 4.0000);
INSERT INTO public.precos_modelo VALUES ('claude-fable-5-1', 'Fable 5.1', 10.0000, 12.5000, 0.2500, 50.0000, 20.0000);
INSERT INTO public.precos_modelo VALUES ('claude-opus-5', 'Opus 5', 5.0000, 6.2500, 0.5000, 25.0000, 10.0000);


--
-- Data for Name: prontos; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.prontos VALUES ('2026-10-27-resumir-reunioes', '2026-10-27-resumir-reunioes', 'PASS', 41.6, '2026-10-28 21:00:00+00', 'ATA');
INSERT INTO public.prontos VALUES ('2026-11-06-planilha-com-ia', '2026-11-06-planilha-com-ia', 'PASS', 37.2, '2026-11-09 21:00:00+00', 'TABELA');


--
-- Data for Name: sincronizacoes; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.sincronizacoes VALUES ('2026-11-12 22:31:57.727121+00', '{"usd": "4.3290", "fila": 1, "looks": 4, "cambio": 1, "fontes": 5, "tokens": 551630, "videos": 4, "agentes": 27, "prontos": 2, "metricas": 2, "animacoes": 1, "execucoes": 5, "sem_preco": {}, "arquivadas": 0, "veredictos": 15, "publicacoes": 1, "capa_estilos": 2, "nao_publicar": 0, "uso_execucao": 19, "departamentos": 7, "perfil_diario": 56, "precos_modelo": 4, "portoes_estado": 20, "legenda_estilos": 1, "calendario_vagas": 3, "perfil_snapshots": 5, "modelos_descricao": 3, "perfil_demografia": 90, "sistema_contagens": 1, "biblioteca_arquivos": 13, "registros_presentes": true, "sistema_ferramentas": 11, "biblioteca_materiais": 9, "capa_estilos_exemplos": 2, "biblioteca_referencias": 2, "biblioteca_mais_utilizados": 4}');


--
-- Data for Name: sistema_contagens; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.sistema_contagens VALUES (true, 29, 9, 20);


--
-- Data for Name: sistema_ferramentas; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.sistema_ferramentas VALUES ('Claude Code', 0, 'Agente de IA (terminal)', 'Onde a equipe trabalha: o Atlas (a direção) e os 25 agentes rodam aqui, leem e escrevem os arquivos do projeto e chamam os scripts.', NULL, NULL);
INSERT INTO public.sistema_ferramentas VALUES ('Python 3.12 · uv', 1, 'Linguagem', 'Os scripts do pipeline: cortar pelo roteiro, medir o áudio, montar o pacote, publicar, ler métricas e alimentar este painel.', '3.12', '.python-version');
INSERT INTO public.sistema_ferramentas VALUES ('ffmpeg', 2, 'Programa de linha de comando', 'Corta, junta e converte vídeo e áudio, e aplica os looks de cor (LUTs).', NULL, NULL);
INSERT INTO public.sistema_ferramentas VALUES ('Remotion 4', 3, 'Biblioteca de vídeo (React)', 'Monta o vídeo final por código: legendas, títulos, animações, zooms e o cartão do CTA.', '4.0.525', 'remotion/package.json#remotion');
INSERT INTO public.sistema_ferramentas VALUES ('ElevenLabs', 4, 'API', 'Transcreve a fala com o tempo de cada palavra (Scribe) e gera a música de fundo original (Music).', NULL, NULL);
INSERT INTO public.sistema_ferramentas VALUES ('Meta Graph API', 5, 'API', 'Publica os Reels no Instagram e no Facebook, lê as métricas e responde quem comenta a palavra-chave.', NULL, NULL);
INSERT INTO public.sistema_ferramentas VALUES ('Cloudflare R2', 6, 'Armazenamento na nuvem', 'Guarda o vídeo e a capa que a Meta baixa para publicar, e o PDF da palavra-chave, com o link que vai no direct.', NULL, NULL);
INSERT INTO public.sistema_ferramentas VALUES ('launchd (macOS)', 7, 'Agendador do sistema', 'Roda sozinho: a publicação na hora marcada, as métricas às 09:30, os comentários e a sincronização deste painel.', NULL, NULL);
INSERT INTO public.sistema_ferramentas VALUES ('Next.js 15 · TypeScript', 8, 'Framework web (front-end)', 'Este painel: as telas que você está vendo, rodando só neste Mac.', '15.5.28', 'painel/web/package.json#next');
INSERT INTO public.sistema_ferramentas VALUES ('Supabase · Postgres', 9, 'Banco de dados', 'Guarda os números que o painel mostra, copiados dos arquivos do projeto a cada 15 min.', '17', 'painel/supabase/config.toml#db.major_version');
INSERT INTO public.sistema_ferramentas VALUES ('Claude Design', 10, 'Ferramenta de design', 'Onde as telas do painel e as animações dos vídeos são desenhadas antes de virar código.', NULL, NULL);


--
-- Data for Name: uso_execucao; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.uso_execucao VALUES ('sessao-demo-1.jsonl', '2026-10-23', 'claude-opus-5-5', 1, 1890, 12400, 169000, 1520, 3000, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1.jsonl', '2026-10-26', 'claude-opus-5-5', 1, 2160, 13600, 196000, 1880, 3000, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1.jsonl', '2026-10-27', 'claude-opus-5-5', 1, 2250, 14000, 205000, 2000, 6000, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1.jsonl', '2026-10-28', 'claude-opus-5-5', 1, 2340, 14400, 214000, 2120, 0, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1.jsonl', '2026-10-29', 'claude-opus-5-5', 1, 2430, 14800, 223000, 2240, 3000, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1.jsonl', '2026-10-30', 'claude-opus-5-5', 1, 2520, 15200, 232000, 2360, 6000, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1.jsonl', '2026-11-02', 'claude-opus-5-5', 1, 2790, 16400, 259000, 2720, 6000, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1.jsonl', '2026-11-03', 'claude-opus-5-5', 1, 2880, 16800, 268000, 2840, 0, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1.jsonl', '2026-11-04', 'claude-opus-5-5', 1, 2970, 17200, 277000, 2960, 3000, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1.jsonl', '2026-11-05', 'claude-opus-5-5', 1, 3060, 17600, 286000, 3080, 6000, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1.jsonl', '2026-11-06', 'claude-opus-5-5', 1, 3150, 18000, 295000, 3200, 0, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1.jsonl', '2026-11-09', 'claude-opus-5-5', 1, 3420, 19200, 322000, 3560, 0, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1.jsonl', '2026-11-10', 'claude-opus-5-5', 1, 3510, 19600, 331000, 3680, 3000, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1.jsonl', '2026-11-11', 'claude-opus-5-5', 1, 3600, 20000, 340000, 3800, 6000, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1/subagents/agent-demo01.jsonl', '2026-11-10', 'claude-opus-5-5', 2, 5100, 44000, 450000, 9500, 0, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-1/subagents/agent-demo02.jsonl', '2026-11-11', 'claude-sonnet-5-5', 1, 8800, 52000, 380000, 9200, 12000, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-2.jsonl', '2026-11-09', 'claude-opus-5-5', 1, 1300, 9000, 120000, 1900, 0, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-2.jsonl', '2026-11-09', 'claude-sonnet-5-5', 1, 2100, 16000, 90000, 2500, 0, 0, DEFAULT);
INSERT INTO public.uso_execucao VALUES ('sessao-demo-2/subagents/agent-demo03.jsonl', '2026-11-09', 'claude-sonnet-5-5', 1, 3300, 21000, 70000, 2800, 0, 0, DEFAULT);


--
-- Data for Name: veredictos; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.veredictos VALUES ('videos/2026-10-27-resumir-reunioes', '2026-10-27-resumir-reunioes', 'pauta', 'portao-pauta', 'APROVADO', '8fd8e8d1cb3d', '2026-10-18 13:00:00+00', 1, 0, 0, 0, 'videos/2026-10-27-resumir-reunioes/qa/portoes/pauta-v1.md', NULL, NULL, 0);
INSERT INTO public.veredictos VALUES ('videos/2026-10-27-resumir-reunioes', '2026-10-27-resumir-reunioes', 'roteiro', 'revisor-de-roteiro', 'APROVADO', '159802242a20', '2026-10-19 18:00:00+00', 1, 0, 0, 0, 'videos/2026-10-27-resumir-reunioes/qa/portoes/roteiro-v1.md', NULL, NULL, 1);
INSERT INTO public.veredictos VALUES ('videos/2026-10-27-resumir-reunioes', '2026-10-27-resumir-reunioes', 'imagem', 'portao-imagem', 'APROVADO', '7c5943d518f3', '2026-10-27 14:00:00+00', 1, 0, 0, 0, 'videos/2026-10-27-resumir-reunioes/qa/portoes/imagem-v1.md', NULL, NULL, 2);
INSERT INTO public.veredictos VALUES ('videos/2026-10-27-resumir-reunioes', '2026-10-27-resumir-reunioes', 'corte', 'revisor-de-video', 'APROVADO', '859c9548fab3', '2026-10-27 20:00:00+00', 1, 0, 0, 1, 'videos/2026-10-27-resumir-reunioes/qa/portoes/corte-v1.md', 'S2: legenda da L03 pode quebrar em duas linhas (backlog)', NULL, 3);
INSERT INTO public.veredictos VALUES ('videos/2026-11-06-planilha-com-ia', '2026-11-06-planilha-com-ia', 'pauta', 'portao-pauta', 'APROVADO', '8e51b2d05f77', '2026-10-30 13:00:00+00', 1, 0, 0, 0, 'videos/2026-11-06-planilha-com-ia/qa/portoes/pauta-v1.md', NULL, NULL, 0);
INSERT INTO public.veredictos VALUES ('videos/2026-11-06-planilha-com-ia', '2026-11-06-planilha-com-ia', 'roteiro', 'revisor-de-roteiro', 'BLOQUEADO', '9de832d18d9e', '2026-10-31 17:00:00+00', 1, 0, 1, 0, 'videos/2026-11-06-planilha-com-ia/qa/portoes/roteiro-v1.md', 'S1: o CTA prometia um material que não existia', NULL, 1);
INSERT INTO public.veredictos VALUES ('videos/2026-11-06-planilha-com-ia', '2026-11-06-planilha-com-ia', 'roteiro', 'revisor-de-roteiro', 'APROVADO', '9de832d18d9e', '2026-10-31 20:00:00+00', 2, 0, 0, 0, 'videos/2026-11-06-planilha-com-ia/qa/portoes/roteiro-v2.md', NULL, NULL, 2);
INSERT INTO public.veredictos VALUES ('videos/2026-11-06-planilha-com-ia', '2026-11-06-planilha-com-ia', 'imagem', 'portao-imagem', 'APROVADO', '9b2957e759f7', '2026-11-08 14:00:00+00', 1, 0, 0, 0, 'videos/2026-11-06-planilha-com-ia/qa/portoes/imagem-v1.md', NULL, NULL, 3);
INSERT INTO public.veredictos VALUES ('videos/2026-11-06-planilha-com-ia', '2026-11-06-planilha-com-ia', 'corte', 'revisor-de-video', 'APROVADO', '4a343dd3e409', '2026-11-08 19:00:00+00', 1, 0, 0, 0, 'videos/2026-11-06-planilha-com-ia/qa/portoes/corte-v1.md', NULL, NULL, 4);
INSERT INTO public.veredictos VALUES ('videos/2026-11-10-prompt-claro', '2026-11-10-prompt-claro', 'pauta', 'portao-pauta', 'APROVADO', '71d9845b5e99', '2026-11-02 13:00:00+00', 1, 0, 0, 0, 'videos/2026-11-10-prompt-claro/qa/portoes/pauta-v1.md', NULL, NULL, 0);
INSERT INTO public.veredictos VALUES ('videos/2026-11-10-prompt-claro', '2026-11-10-prompt-claro', 'roteiro', 'revisor-de-roteiro', 'APROVADO', '245c3ef1840e', '2026-11-05 18:00:00+00', 1, 0, 0, 0, 'videos/2026-11-10-prompt-claro/qa/portoes/roteiro-v1.md', NULL, NULL, 1);
INSERT INTO public.veredictos VALUES ('videos/2026-11-10-prompt-claro', '2026-11-10-prompt-claro', 'imagem', 'portao-imagem', 'BLOQUEADO', '3830df2c4fdf', '2026-11-11 18:00:00+00', 1, 0, 1, 0, 'videos/2026-11-10-prompt-claro/qa/portoes/imagem-v1.md', 'S1: título da capa em cima do rosto', NULL, 2);
INSERT INTO public.veredictos VALUES ('videos/2026-11-19-ia-no-atendimento', '2026-11-19-ia-no-atendimento', 'pauta', 'portao-pauta', 'APROVADO', 'c246f559441e', '2026-11-11 12:00:00+00', 1, 0, 0, 0, 'videos/2026-11-19-ia-no-atendimento/qa/portoes/pauta-v1.md', NULL, NULL, 0);
INSERT INTO public.veredictos VALUES ('videos/2026-11-19-ia-no-atendimento', '2026-11-19-ia-no-atendimento', 'roteiro', 'revisor-de-roteiro', 'APROVADO', '3ca8d32a6d18', '2026-11-11 17:00:00+00', 1, 0, 0, 0, 'videos/2026-11-19-ia-no-atendimento/qa/portoes/roteiro-v1.md', NULL, NULL, 1);
INSERT INTO public.veredictos VALUES ('06-publicar/2026-11-06-planilha-com-ia', '2026-11-06-planilha-com-ia', 'publicacao', 'portao-publicacao', 'APROVADO', '9e64400f775c', '2026-11-10 13:00:00+00', 1, 0, 0, 0, '06-publicar/2026-11-06-planilha-com-ia/qa/portao-publicacao-v1.md', NULL, NULL, 0);


--
-- PostgreSQL database dump complete
--


COMMIT;

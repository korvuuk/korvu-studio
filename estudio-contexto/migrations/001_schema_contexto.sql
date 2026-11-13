-- estudio-contexto · migração 001 · schema `contexto` (ESPECIFICACAO.md §4, §5, §6)
--
-- Roda no Postgres local do painel (127.0.0.1:55322), num schema PRÓPRIO. Não toca em nenhuma tabela `public`.
-- Extensões: `vector` (pgvector) e `unaccent` ficam no schema `extensions`, o lugar padrão do Supabase.
-- Tudo aqui é DERIVADO dos arquivos e das tabelas do painel: pode ser apagado (drop schema contexto cascade) e
-- reconstruído do zero com `uv run python -m contexto.sincronizar`.

create schema if not exists extensions;   -- já existe no banco do painel; num banco de teste novo, não
create extension if not exists vector with schema extensions;
create extension if not exists unaccent with schema extensions;

create schema if not exists contexto;

-- busca textual em português sem acento ("decisao" acha "decisão")
do $$
begin
  if not exists (select 1 from pg_ts_config c join pg_namespace n on n.oid = c.cfgnamespace
                 where n.nspname = 'contexto' and c.cfgname = 'pt') then
    create text search configuration contexto.pt (copy = pg_catalog.portuguese);
    alter text search configuration contexto.pt
      alter mapping for hword, hword_part, word with extensions.unaccent, portuguese_stem;
  end if;
end $$;

create table contexto.migracoes (
  versao      text primary key,
  aplicada_em timestamptz not null default now()
);

-- Nós do grafo. id = '<tipo>:<chave>' (ex.: 'video:2026-01-15-exemplo', 'decisao:PD9').
create table contexto.nos (
  id       text primary key,
  tipo     text not null check (tipo in ('projeto', 'agente', 'departamento', 'video', 'publicacao', 'portao',
                                         'veredicto', 'decisao', 'documento', 'trecho')),
  nome     text not null,
  projeto  text,
  data     date,
  fonte    text not null,          -- de onde o nó saiu (caminho do arquivo ou 'painel.<tabela>')
  dados    jsonb not null default '{}'::jsonb
);
create index nos_tipo on contexto.nos (tipo);
create index nos_nome on contexto.nos (lower(nome));

-- Arestas. Recalculadas por completo a cada passagem do sincronizador (§5). Nenhuma edição manual.
create table contexto.arestas (
  origem   text not null references contexto.nos (id) on delete cascade,
  destino  text not null references contexto.nos (id) on delete cascade,
  tipo     text not null check (tipo in ('pertence_a', 'membro_de', 'gerencia', 'fiscaliza', 'avalia', 'emitiu',
                                         'bloqueou', 'aprovou', 'publicado_como', 'decide_sobre', 'depende_de',
                                         'menciona', 'contem')),
  fonte    text not null,
  dados    jsonb not null default '{}'::jsonb,
  primary key (origem, destino, tipo)
);
create index arestas_destino on contexto.arestas (destino, tipo);

-- Documentos indexados (um por arquivo do corpus).
create table contexto.documentos (
  caminho     text primary key,     -- relativo à raiz do Korvu Studio
  projeto     text not null,
  tipo        text not null,
  hash        text not null,        -- sha256 do arquivo inteiro
  bytes       integer not null,
  modificado  timestamptz not null,
  indexado_em timestamptz not null default now()
);

-- Trechos com embedding (multilingual-e5-small, 384 dimensões, normalizado → distância de cosseno).
create table contexto.trechos (
  id        text primary key,       -- '<caminho>#<hash curto>' (estável enquanto o texto não muda)
  caminho   text not null references contexto.documentos (caminho) on delete cascade,
  ordem     integer not null,
  secao     text not null default '',
  tipo      text not null,
  data      date,
  pds       text[] not null default '{}',
  entidades text[] not null default '{}',   -- ids de nós citados no trecho (vídeo, agente, decisão)
  hash      text not null,                  -- sha256 do texto do trecho (reindexação incremental)
  texto     text not null,
  embedding extensions.vector(384) not null,
  tsv       tsvector generated always as (
              setweight(to_tsvector('contexto.pt', coalesce(secao, '')), 'A') ||
              setweight(to_tsvector('contexto.pt', texto), 'B')) stored
);
create index trechos_caminho on contexto.trechos (caminho);
create index trechos_tsv on contexto.trechos using gin (tsv);
create index trechos_entidades on contexto.trechos using gin (entidades);
create index trechos_embedding on contexto.trechos using hnsw (embedding extensions.vector_cosine_ops);

-- Registro de cada passagem do sincronizador.
create table contexto.sincronizacoes (
  id          bigserial primary key,
  inicio      timestamptz not null default now(),
  fim         timestamptz,
  nos         integer,
  arestas     integer,
  documentos  integer,
  trechos     integer,
  embedados   integer,
  removidos   integer,
  excluidos   text[] not null default '{}',   -- arquivos recusados pela segurança (caminho, nunca conteúdo)
  ok          boolean not null default false,
  erro        text
);

-- Papel de leitura usado pelo servidor MCP (SET ROLE na conexão): só SELECT no schema contexto,
-- nada no `public` do painel. Sem senha (NOLOGIN): ninguém entra direto com ele.
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'contexto_leitor') then
    create role contexto_leitor nologin;
  end if;
  -- quem conecta (postgres) pode baixar para o papel de leitura com SET ROLE
  if not pg_has_role(current_user, 'contexto_leitor', 'SET') then
    execute format('grant contexto_leitor to %I with set true, inherit false', current_user);
  end if;
end $$;
grant usage on schema contexto to contexto_leitor;
grant usage on schema extensions to contexto_leitor;
grant select on all tables in schema contexto to contexto_leitor;

-- A API do Supabase (anon/authenticated) não enxerga este schema.
revoke all on schema contexto from public;
do $$
declare r text;
begin
  foreach r in array array['anon', 'authenticated', 'service_role'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke all on schema contexto from %I', r);
      execute format('revoke all on all tables in schema contexto from %I', r);
    end if;
  end loop;
end $$;

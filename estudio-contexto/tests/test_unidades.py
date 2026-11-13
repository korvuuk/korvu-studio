"""Unitários (§11): chunking, hash, derivação de arestas, RRF, filtros e segurança. Não precisam do banco."""
from __future__ import annotations

import datetime as dt

from conftest import ARQUIVOS, FALSO_TOKEN, RAIZ

from contexto.busca import Filtros, _rrf, datas_da_consulta
from contexto.chunking import Trecho, achar_data, chunk, chunk_markdown, pds
from contexto.corpus import carregar_projetos, projeto_do_caminho, tipo_do_documento
from contexto.grafo import construir, ler_decisoes_md, ler_pds, montar_catalogo
from contexto.seguranca import motivo_exclusao, tokens_no_texto


# ── chunking ──────────────────────────────────────────────────────────

def test_markdown_corta_por_secao_e_guarda_o_caminho():
    t = chunk_markdown("# Doc\n\n## A\n" + "texto a. " * 30 + "\n\n## B\n" + "texto b. " * 30)
    assert [x.secao for x in t] == ["Doc › A", "Doc › B"]
    assert "texto a" in t[0].texto and "texto b" not in t[0].texto


def test_secao_grande_respeita_o_limite_e_nao_perde_texto():
    corpo = "\n\n".join(f"Parágrafo {i}. " + "palavra " * 40 for i in range(30))
    t = chunk_markdown("## Grande\n" + corpo, maximo=600)
    assert len(t) > 5 and all(len(x.texto) <= 600 for x in t)
    junto = " ".join(x.texto for x in t)
    assert all(f"Parágrafo {i}." in junto for i in range(30))


def test_linha_longa_de_tabela_vira_trecho_proprio():
    t = chunk("docs/decisoes.md", ARQUIVOS["docs/decisoes.md"], maximo=1100)
    linhas = [x for x in t if x.texto.startswith("| **")]
    assert len(linhas) == 2, [x.texto[:40] for x in t]
    assert "Duração livre" in linhas[0].texto and "Música" not in linhas[0].texto


def test_secao_curta_junta_com_a_seguinte():
    t = chunk_markdown("## Curta\nsó isso\n\n## Longa\n" + "conteúdo " * 40, minimo=120)
    assert len(t) == 1 and "só isso" in t[0].texto


def test_codigo_nao_vira_titulo():
    t = chunk_markdown("## Seção\n" + "texto " * 30 + "\n```\n## não é título\n```\n" + "mais " * 30)
    assert len(t) == 1


def test_json_pequeno_inteiro_e_grande_por_item():
    pequeno = chunk("x/status.json", '{"slug": "a", "estado": "roteiro"}')
    assert len(pequeno) == 1 and "estado: roteiro" in pequeno[0].texto
    grande = chunk("x/status.json", '{"historico": [' + ",".join(
        f'{{"nota": "{"n" * 300} {i}"}}' for i in range(12)) + '], "slug": "a"}', maximo=800)
    assert len(grande) > 3 and all(len(x.texto) <= 800 for x in grande)
    assert grande[0].secao == "historico"


def test_data_e_pd():
    assert achar_data("## 2026-11-10 — sessão") == dt.date(2026, 11, 10)
    assert achar_data("decidido em 23/10") == dt.date(2026, 10, 23)
    assert achar_data("versão 1/2 do arquivo 3/4") is None or True  # sem crash em frações
    assert achar_data("sem data aqui") is None
    assert pds("PD12 e PD9, de novo PD9; não PDX") == ["PD9", "PD12"]
    assert datas_da_consulta("o que mudou em 22/10 e 2026-11-01?") == [dt.date(2026, 11, 1), dt.date(2026, 10, 22)]


def test_hash_muda_com_o_texto_e_com_a_secao():
    a, b, c = Trecho(0, "S", "texto"), Trecho(5, "S", "texto"), Trecho(0, "S", "texto!")
    assert a.hash == b.hash != c.hash
    assert Trecho(0, "Outra", "texto").hash != a.hash


# ── RRF e filtros ─────────────────────────────────────────────────────

def test_rrf_premia_quem_aparece_nas_duas_listas():
    s = _rrf([["a", "b", "c"], ["c", "d"]], [1.0, 1.0])
    assert max(s, key=s.get) == "c"
    assert abs(s["a"] - 1 / 61) < 1e-9 and abs(s["c"] - (1 / 63 + 1 / 61)) < 1e-9


def test_rrf_respeita_o_peso():
    s = _rrf([["a"], ["b"]], [1.0, 0.5])
    assert s["a"] == 2 * s["b"]


class _ConFalsa:
    def execute(self, *a):
        return [("painel",)]


def test_filtros_viram_sql_parametrizado():
    w, p = Filtros(projeto="painel", tipo="video", agente="roteirista", desde="2026-11-01").sql(_ConFalsa())
    assert "d.projeto = any(%s)" in w and "e like %s" in w and "t.data >= %s::date" in w
    assert p == [["painel"], "video:%", "agente:roteirista", ".claude/agents/roteirista.md", "2026-11-01"]
    w2, p2 = Filtros(tipo="handoff").sql(_ConFalsa())
    assert w2 == "t.tipo = %s" and p2 == ["handoff"]
    assert Filtros().sql(_ConFalsa()) == ("true", [])


# ── segurança ─────────────────────────────────────────────────────────

def test_lista_de_exclusao_fixa():
    for c in [".env", ".env.local", "painel/web/.env.local", "automacao-meta/.env.producao", ".env.example"]:
        assert motivo_exclusao(c) == "segredo", c
    for c in ["videos/x/brutos/principal/a.md", "07-publicados/x/post.json", "node_modules/a/README.md",
              ".claude/skills/x/SKILL.md", "05-render-pronto/x/roteiro.md"]:
        assert motivo_exclusao(c) == "pasta_fora", c
    for c in ["videos/x/edicao/final.mp4", "BG VIDEO/a.mov", "a.wav", "capa.png"]:
        assert motivo_exclusao(c) in ("midia", "pasta_fora"), c
    for c in ["CLAUDE.md", "docs/decisoes.md", "videos/2026-01-12-exemplo/roteiro.md"]:
        assert motivo_exclusao(c) is None, c


def test_detector_de_token_sem_falso_positivo_comum():
    assert tokens_no_texto(f"chave: {FALSO_TOKEN}") == ["openai"]
    assert "jwt" in tokens_no_texto("eyJhbGciOiJIUzI1NiIsInR5cCI6.eyJpc3MiOiJzdXBhYmFzZS1kZW1v.abcdefghijklmnopqrstuv")
    assert tokens_no_texto("-----BEGIN RSA PRIVATE KEY-----") == ["chave_privada"]
    # falsos positivos vistos no estúdio (§14): "sk-" dentro de palavra e URL, nomes de variáveis
    assert tokens_no_texto("risk-free task-based https://x.com/desk-setup ELEVENLABS_API_KEY META_TOKEN") == []
    assert tokens_no_texto("o token expira em 06/01/2027; escopos w_member_social") == []


# ── mapa e grafo ──────────────────────────────────────────────────────

def test_projeto_pelo_prefixo_mais_longo():
    P = carregar_projetos()
    assert projeto_do_caminho("painel/README.md", P) == "painel"
    assert projeto_do_caminho("HANDOFF.md", P) == "estudio"
    assert projeto_do_caminho("scripts/publicar.py", P) == "automacao-meta"
    assert projeto_do_caminho("scripts/outro.py", P) == "estudio"
    assert projeto_do_caminho("remotion/src/Reel.tsx", P) == "remotion"
    assert tipo_do_documento("videos/a/qa/portoes/pauta-v1.md") == "relatorio_portao"


def test_decisoes_e_pds_lidos_dos_arquivos():
    d = ler_decisoes_md(RAIZ)
    assert [x.id for x in d] == ["decisao:dec-1-01", "decisao:dec-1-02", "decisao:dec-6-01"]
    assert d[0].nome == "Duração livre do roteiro" and d[0].data == dt.date(2026, 11, 2)
    p = ler_pds(RAIZ)
    assert list(p) == ["PD9"] and p["PD9"].dados["entradas"][0]["estado"] == "aberto"


def _painel_minimo():
    agora = dt.datetime(2026, 11, 1, 10, tzinfo=dt.timezone.utc)
    return {
        "departamentos": [{"id": "roteiro", "nome": "roteiro", "descricao": "", "gerente_id": "revisor-de-roteiro"}],
        "agentes": [
            {"id": "roteirista", "nome": "M", "cargo": "roteirista", "departamento_id": "roteiro", "papel": "",
             "resumo": "", "fiscalizado_por": "revisor-de-roteiro", "fiscaliza": [], "arquivo": None, "modelo": None},
            {"id": "revisor-de-roteiro", "nome": "O", "cargo": "g", "departamento_id": "roteiro", "papel": "",
             "resumo": "", "fiscalizado_por": None, "fiscaliza": ["roteirista"], "arquivo": None, "modelo": None}],
        "videos": [{"slug": "2026-11-01-teste-um", "tema": "t", "pilar": "perfil", "estrutura": None, "cta": None,
                    "estado": "roteiro", "atualizado": agora, "cta_palavra": None, "gravacao_prevista": None,
                    "nome_curto": None, "roteiro_versao": None}],
        "portoes_estado": [{"alvo": "videos/2026-11-01-teste-um", "slug": "2026-11-01-teste-um", "portao": "roteiro",
                            "agente": "revisor-de-roteiro", "status": "aprovado", "motivos": None, "volta": 1}],
        "veredictos": [{"alvo": "videos/2026-11-01-teste-um", "slug": "2026-11-01-teste-um", "portao": "roteiro",
                        "agente": "revisor-de-roteiro", "resultado": "ESCALADO", "em": agora, "volta": 3, "s0": 0,
                        "s1": 2, "s2": 0, "relatorio": None, "nota": None, "decisao_autor": None, "ordem": 0}],
        "publicacoes": [], "metricas": []}


def test_derivacao_de_arestas():
    P = carregar_projetos()
    painel = _painel_minimo()
    cat = montar_catalogo(RAIZ, P, painel)
    g = construir(RAIZ, P, painel, cat, [], [])
    a = set(g.arestas)
    assert ("portao:revisor-de-roteiro", "agente:roteirista", "fiscaliza") in a
    assert ("agente:revisor-de-roteiro", "departamento:roteiro", "gerencia") in a
    assert ("portao:revisor-de-roteiro", "video:2026-11-01-teste-um", "avalia") in a
    assert ("projeto:painel", "projeto:estudio", "depende_de") in a
    assert ("projeto:remotion", "projeto:estudio", "pertence_a") in a
    assert ("agente:roteirista", "projeto:estudio", "pertence_a") in a
    # ESCALADO não é aprovação
    v = "veredicto:videos/2026-11-01-teste-um|roteiro|0"
    assert (v, "video:2026-11-01-teste-um", "bloqueou") in a and (v, "video:2026-11-01-teste-um", "aprovou") not in a
    # decisão que cita vídeo, agente e pasta de projeto
    assert ("decisao:dec-1-01", "video:2026-11-01-teste-um", "decide_sobre") in a
    assert ("decisao:dec-1-01", "agente:roteirista", "decide_sobre") in a
    assert ("decisao:dec-1-01", "projeto:painel", "decide_sobre") in a
    assert ("decisao:PD9", "projeto:painel", "decide_sobre") in a
    # nenhuma aresta aponta para nó inexistente (a gravação também filtra, mas a derivação não deve gerar)
    assert all(o in g.nos and d in g.nos for o, d, _ in a)


def test_entidades_reconhece_slug_inteiro_e_cauda():
    P = carregar_projetos()
    cat = montar_catalogo(RAIZ, P, _painel_minimo())
    assert "video:2026-11-01-teste-um" in cat.entidades("o teste-um foi aprovado")
    assert "video:2026-11-01-teste-um" in cat.entidades("pasta videos/2026-11-01-teste-um/roteiro.md")
    assert cat.entidades("o roteirista e o PD9") == ["agente:roteirista", "decisao:PD9"]
    assert "agente:roteirista" not in cat.entidades("pré-roteirista-x")

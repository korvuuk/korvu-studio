"""Teste do scripts/publicar.py com um pacote falso num ROOT temporário (CONTENT_AI_ROOT).

NUNCA usa a rede: os subprocessos têm proxy morto (127.0.0.1:9) e credenciais falsas; o fluxo
"real" corre em processo com requests/boto3 substituídos por uma Meta/R2 simulada.

Uso (da raiz do projeto):  uv run python tests/publicar/test_publicar.py [--manter]
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PROJETO = AQUI.parent.parent
SCRIPT = PROJETO / "scripts" / "publicar.py"
FIXTURE_GAUNTLET = PROJETO / "tests" / "portoes" / "fixture_gauntlet.py"
FFMPEG = os.environ.get("FFMPEG_BIN") or "ffmpeg"
MONTAR = PROJETO / "scripts" / "montar_pacote.py"
# Slides fictícios gerados na hora (o carrossel-modelo real não vem para o repositório); a palavra ESTUDO é de teste.
def _slides_ficticios() -> Path:
    """9 slides 3:4 de cores sólidas + a grade de prévia, gerados na hora (o repositório não guarda o carrossel real)."""
    from PIL import Image
    d = Path(tempfile.mkdtemp(prefix="korvu-slides-"))
    for i in range(1, 10):
        Image.new("RGB", (1080, 1440), (20 * i, 80, 160)).save(d / f"{i:02d}.png")
    Image.new("RGB", (1080, 1440), (240, 240, 240)).save(d / "grade.jpg")
    return d


MODELO_SLIDES = _slides_ficticios()

TOKEN_IG = "EAAGtesteIG1234567890SEGREDOabcdefXYZ"
TOKEN_PG = "EAAGpaginaPG0987654321SEGREDOqwertyUIO"
R2_SECRET = "r2segredo_abcdef0123456789ABCDEF"
APP_SECRET = "appsecret_0123456789abcdefFEDCBA"
SEGREDOS = [TOKEN_IG, TOKEN_PG, R2_SECRET, APP_SECRET]
IG_ID, PAGE_ID = "17841400000000000", "100000000000001"
AGORA_1 = "2026-09-15T17:00:00+01:00"  # terça
AGORA_2 = "2026-09-16T19:05:00+01:00"  # quarta, depois da vaga das 19:00

RES: list[tuple[str, bool, str]] = []


def ok(nome: str, cond, detalhe: str = "") -> None:
    RES.append((nome, bool(cond), detalhe))
    print(f"  [{'PASS' if cond else 'FAIL'}] {nome}" + (f" — {detalhe}" if detalhe else ""))


def env_teste(root: Path, agora: str, **extra) -> dict:
    e = {k: v for k, v in os.environ.items() if not k.startswith(("INSTAGRAM_", "META_", "R2_"))}
    e.update(CONTENT_AI_ROOT=str(root), CONTENT_AI_NO_DOTENV="1", CONTENT_AI_AGORA=agora,
             PUBLICAR_SEM_NOTIFICACAO="1", INSTAGRAM_USER_ID=IG_ID, INSTAGRAM_ACCESS_TOKEN=TOKEN_IG,
             META_PAGE_ID=PAGE_ID, META_PAGE_ACCESS_TOKEN=TOKEN_PG, META_APP_ID="123456",
             META_APP_SECRET=APP_SECRET, R2_ACCOUNT_ID="contafalsa", R2_ACCESS_KEY_ID="AKIAFALSO1234567",
             R2_SECRET_ACCESS_KEY=R2_SECRET, R2_BUCKET_NAME="korvu-teste",
             R2_PUBLIC_URL="https://media.exemplo.test",
             HTTP_PROXY="http://127.0.0.1:9", HTTPS_PROXY="http://127.0.0.1:9", NO_PROXY="",
             http_proxy="http://127.0.0.1:9", https_proxy="http://127.0.0.1:9")
    e.update(extra)
    return e


def rodar(env: dict, *args: str) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True, cwd=PROJETO)
    out = r.stdout + r.stderr
    ok(f"sem segredos no output de `{' '.join(args)}`", not any(s in out for s in SEGREDOS))
    return r.returncode, out


# ───────────────────────── fixture ─────────────────────────

def criar_root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="korvu-publicar-"))
    (root / "_controle").mkdir()
    for f in ("calendario.md", "tracker.md"):
        shutil.copy(Path(__file__).parent / "fixtures" / f, root / "_controle" / f)
    # O calendário real muda com o uso (confirmações gastas, trial_padrao): o teste parte de um estado fixo.
    cal = root / "_controle" / "calendario.md"
    txt = re.sub(r"(?m)^modo_confirmar_restantes:\s*\d+", "modo_confirmar_restantes: 2", cal.read_text())
    cal.write_text(re.sub(r"(?m)^trial_padrao:.*\n", "", txt))
    (root / "06-publicar").mkdir()
    (root / "07-publicados").mkdir()
    return root


_VIDEO = None


def gauntlet(root: Path, *args: str) -> None:
    subprocess.run([sys.executable, str(FIXTURE_GAUNTLET), *args], check=True, cwd=PROJETO,
                   env={**os.environ, "CONTENT_AI_ROOT": str(root)})


def aprovar_publicacao(root: Path, slug: str) -> None:
    """O PORTÃO-PUBLICACAO audita o post.json que o agendar escreve: aprovar de novo depois do agendar."""
    gauntlet(root, "aprovar", str(root / "06-publicar" / slug), "publicacao")


def criar_pacote(root: Path, slug: str, *, qa: str = "PASS", hashtags: int = 3, fb: bool = True,
                 legenda_extra: str = "", duracao: float | None = 3.5, selo: bool = True,
                 publicacao: bool = True, comentario: bool = True) -> Path:
    global _VIDEO
    p = root / "06-publicar" / slug
    for d in ("video", "capa", "legendas", "material"):
        (p / d).mkdir(parents=True, exist_ok=True)
    if _VIDEO is None:
        _VIDEO = root / "_video.mp4"
        subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=270x480:d=3.5:r=30",
                        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "3.5",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(_VIDEO)], check=True)
    shutil.copy(_VIDEO, p / "video" / "video-final.mp4")
    from PIL import Image

    Image.new("RGB", (540, 960), (20, 40, 90)).save(p / "capa" / "capa.png")
    (p / "legendas" / "legendas.srt").write_text("1\n00:00:00,000 --> 00:00:02,000\nVocê\n")
    (p / "material" / "guia.pdf").write_bytes(b"%PDF-1.4\n%falso para teste\n")
    # estudo que às vezes fica junto: NÃO pode subir para o R2 público (só o PDF de material.arquivo sobe)
    (p / "material" / "dossie.md").write_text("# dossiê de estudo\n")
    (p / "roteiro.md").write_text("# roteiro\n")
    (p / "qa-relatorio.md").write_text("QA PASS\n")
    pacote = {"slug": slug, "criado_em": "2026-09-15T12:00:00+01:00", "duracao": duracao, "qa": qa,
              "arquivos": {"video": "video/video-final.mp4", "variantes": [], "capa": "capa/capa.png",
                           "legendas": "legendas/legendas.srt", "material": "material/guia.pdf",
                           "roteiro": "roteiro.md", "qa": "qa-relatorio.md"},
              "cta_palavra": "PROMPT", "material_titulo": "o guia do prompt",
              "tema": "Você tá pedindo errado pro ChatGPT", "pilar": "mitos-e-erros"}
    if duracao is None:
        del pacote["duracao"]
    (p / "pacote.json").write_text(json.dumps(pacote, ensure_ascii=False, indent=2))
    tags = " ".join(f"#ia{i}" for i in range(hashtags))
    (p / "legenda-instagram.txt").write_text(
        f"ChatGPT: você tá usando errado 😬\n\nComenta PROMPT que eu te mando o guia.{legenda_extra}\n\n{tags}\n")
    if fb:
        (p / "legenda-facebook.txt").write_text("ChatGPT: você tá usando errado.\nComenta PROMPT e recebe o guia.\n")
    if comentario:
        (p / "primeiro-comentario.txt").write_text("Você já usa o ChatGPT no trabalho? Conta aqui o que mais te trava.\n")
    if selo:  # GAUNTLET: origem com os portões aprovados → pacote selado (como faz o montar_pacote.py)
        o = root / "videos" / slug
        for d in ("edicao", "capa", "material"):
            (o / d).mkdir(parents=True, exist_ok=True)
        shutil.copy(p / "video" / "video-final.mp4", o / "edicao" / "final.mp4")
        shutil.copy(p / "legendas" / "legendas.srt", o / "edicao" / "legendas.srt")
        shutil.copy(p / "capa" / "capa.png", o / "capa" / "capa.png")
        shutil.copy(p / "material" / "guia.pdf", o / "material" / "guia.pdf")
        shutil.copy(p / "roteiro.md", o / "roteiro.md")
        gauntlet(root, "aprovar", str(o), "roteiro", "imagem", "corte")
        gauntlet(root, "selar", str(p), str(o))
        if publicacao:
            aprovar_publicacao(root, slug)
    return p


def criar_carrossel(root: Path, slug: str, n: int | None = None) -> Path:
    """carrosseis/<slug> no ROOT temporário com os slides do modelo (todos, ou os n primeiros)."""
    o = root / "carrosseis" / slug
    (o / "slides").mkdir(parents=True)
    (o / "material").mkdir()
    for f in sorted(MODELO_SLIDES.glob("[0-9]*.png"))[:n]:
        shutil.copy(f, o / "slides" / f.name)
    shutil.copy(MODELO_SLIDES / "grade.jpg", o / "slides" / "grade.jpg")
    (o / "carrossel.md").write_text("---\npalavra: ESTUDO\nmaterial_titulo: a lista dos cursos\n"
                                    "tema: 6 cursos grátis de IA\npilar: carreira\n---\n=== capa\ntitulo: 6 cursos\n")
    (o / "material" / "cursos.pdf").write_bytes(b"%PDF-1.4\n%falso para teste\n")
    return o


def montar(root: Path, origem: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(MONTAR), str(origem)], capture_output=True, text=True, cwd=PROJETO,
                       env={**os.environ, "CONTENT_AI_ROOT": str(root)})
    return r.returncode, r.stdout + r.stderr


def para_fila(root: Path, slug: str, de: str | None = None) -> Path:
    """Como o /publicar: o pacote vai de 05-render-pronto/ para 06-publicar/ e o publicador escreve os textos."""
    p = root / "06-publicar" / slug
    shutil.copytree(root / "05-render-pronto" / (de or slug), p)
    (p / "legenda-instagram.txt").write_text("6 cursos grátis de IA 📚\n\nComenta ESTUDO que eu te mando a lista.\n\n#ia\n")
    (p / "legenda-facebook.txt").write_text("6 cursos grátis de IA.\nComenta ESTUDO e recebe a lista.\n")
    (p / "primeiro-comentario.txt").write_text("Qual desses você começaria primeiro?\n")
    return p


def post(root: Path, slug: str, fila: str = "06-publicar") -> dict:
    return json.loads((root / fila / slug / "post.json").read_text())


def agenda(root: Path) -> list[str]:
    txt = (root / "_controle" / "calendario.md").read_text()
    return [ln for ln in txt.split("## Agenda", 1)[1].splitlines() if ln.startswith("| 2")]


def cal_restantes(root: Path) -> int:
    return int(re.search(r"modo_confirmar_restantes:\s*(\d+)", (root / "_controle/calendario.md").read_text()).group(1))


def tracker_linha(root: Path, slug: str) -> str:
    return next((ln for ln in (root / "_controle/tracker.md").read_text().splitlines()
                 if ln.startswith(f"| {slug} |")), "")


# ───────────────────────── Meta / R2 simuladas ─────────────────────────

class Resp:
    def __init__(self, status: int, body: dict):
        self.status_code, self._b, self.ok, self.text = status, body, status < 400, json.dumps(body)

    def json(self):
        return self._b


class FakeMeta:
    def __init__(self, fb_falha: bool = False, comentario_falha: bool = False):
        self.chamadas: list[dict] = []
        self.polls = 0
        self.fb_falha = fb_falha
        self.comentario_falha = comentario_falha

    def __call__(self, sess, method, url, params=None, data=None, headers=None, **kw):
        c = {"m": method, "url": url, "params": dict(params or {}),
             "data": dict(data or {}) if not isinstance(data, bytes) else {"_bytes": len(data)},
             "headers": dict(headers or {}),
             "files": {k: (v[0], len(v[1]) if isinstance(v[1], bytes) else len(v[1].read()))
                       for k, v in (kw.get("files") or {}).items()}}
        self.chamadas.append(c)
        if method == "HEAD":
            return Resp(200, {})
        if url.endswith("/comments") and method == "POST":
            if self.comentario_falha:
                return Resp(400, {"error": {"message": "(#200) Permissions error", "code": 200}})
            return Resp(200, {"id": "COM-" + url.split("/")[-2]})
        if "rupload.facebook.com" in url:
            return Resp(200, {"success": True})
        if url.endswith(f"/{IG_ID}/media") and method == "POST":
            if c["data"].get("is_carousel_item") == "true":  # carrossel: um filho por slide
                return Resp(200, {"id": f"IGF{sum(1 for x in self.chamadas if x['data'].get('is_carousel_item'))}"})
            if c["data"].get("media_type") == "CAROUSEL":
                return Resp(200, {"id": "IGCAR1"})
            return Resp(200, {"id": "IGC1"})
        if re.search(r"/(IGF\d+|IGCAR1)$", url):
            return Resp(200, {"status_code": "FINISHED", "status": "ok"})
        if url.endswith(f"/{PAGE_ID}/photos") and method == "POST":
            n = sum(1 for x in self.chamadas if x["url"].endswith("/photos"))
            return Resp(200, {"id": f"FBF{n}"})
        if url.endswith(f"/{PAGE_ID}/feed") and method == "POST":
            return Resp(200, {"id": f"{PAGE_ID}_777"})
        if url.endswith(f"/{PAGE_ID}_777"):
            return Resp(200, {"permalink_url": f"https://www.facebook.com/{PAGE_ID}/posts/777"})
        if url.endswith("/IGC1"):
            self.polls += 1
            return Resp(200, {"status_code": "IN_PROGRESS" if self.polls < 3 else "FINISHED", "status": "ok"})
        if url.endswith("/media_publish"):
            return Resp(200, {"id": "IGM1"})
        if url.endswith("/IGM1"):
            return Resp(200, {"permalink": "https://www.instagram.com/reel/ABC123/"})
        if url.startswith("https://graph-video.facebook.com/") and url.endswith(f"/{PAGE_ID}/videos"):
            fase = (data or {}).get("upload_phase")
            if fase == "start":  # upload retomável: pedaços de 100 kB
                self.tam = int(data["file_size"])
                return Resp(200, {"video_id": "FBPV1", "upload_session_id": "S1", "start_offset": "0",
                                  "end_offset": str(min(100_000, self.tam))})
            if fase == "transfer":
                ini = int(data["start_offset"]) + c["files"]["video_file_chunk"][1]
                return Resp(200, {"start_offset": str(ini), "end_offset": str(min(ini + 100_000, self.tam))})
            if fase == "finish":
                return Resp(200, {"success": True})
            return Resp(413, {})  # envio num pedido só: o arquivo grande dá 413 (Hinton, 15/10)
        if url.endswith("/FBPV1"):
            return Resp(200, {"status": {"video_status": "ready"}, "permalink_url": "/korvu/videos/FBPV1/"})
        if url.endswith(f"/{PAGE_ID}/video_reels"):
            if self.fb_falha:
                return Resp(500, {"error": {"message": "An unexpected error has occurred.", "code": 2,
                                            "is_transient": True, "fbtrace_id": "XYZ"}})
            if c["data"].get("upload_phase") == "start":
                return Resp(200, {"video_id": "FBV1", "upload_url": "https://rupload.facebook.com/video-upload/v23.0/FBV1"})
            if c["data"].get("upload_phase") == "finish":
                return Resp(200, {"success": True})
        if url.endswith("/FBV1"):
            if c["params"].get("fields") == "status":
                return Resp(200, {"status": {"video_status": "upload_complete", "uploading_phase": {"status": "complete"}}})
            return Resp(200, {"status": {"video_status": "ready", "publishing_phase": {"status": "complete"}},
                              "permalink_url": "/reel/FBV1/"})
        return Resp(404, {"error": {"message": f"rota não simulada {method} {url}", "code": 100}})

    def achar(self, trecho: str, metodo: str | None = None) -> list[dict]:
        return [c for c in self.chamadas if trecho in c["url"] and (metodo is None or c["m"] == metodo)]


class FakeS3:
    def __init__(self):
        self.enviados: list[tuple[str, str, str]] = []

    def upload_file(self, f, bucket, key, ExtraArgs=None):
        assert Path(f).exists()
        self.enviados.append((bucket, key, (ExtraArgs or {}).get("ContentType")))

    def head_bucket(self, Bucket):
        return {}


# ───────────────────────── testes ─────────────────────────

def main() -> int:
    manter = "--manter" in sys.argv
    root = criar_root()
    print(f"ROOT temporário: {root}")
    env1 = env_teste(root, AGORA_1)
    try:
        print("\n== agendar ==")
        criar_pacote(root, "_teste")
        criar_pacote(root, "_teste2")
        rc, out = rodar(env1, "agendar", "_teste")
        ok("agendar _teste", rc == 0, out.strip().splitlines()[-1] if out.strip() else "")
        aprovar_publicacao(root, "_teste")
        p = post(root, "_teste")
        ok("próxima vaga = quarta 19:00 BST", p["publicar_em"] == "2026-09-16T19:00:00+01:00", p["publicar_em"])
        ok("estado agendado + confirmar (modo_confirmar_restantes=2)", p["estado"] == "agendado" and p["confirmar"] is True)
        ok("post.json segue o contrato §10",
           set(p) >= {"slug", "publicar_em", "plataformas", "estado", "confirmar", "instagram", "facebook",
                      "material", "publicado_em", "erros"}
           and p["material"] == {"palavra": "PROMPT", "arquivo": "material/guia.pdf", "titulo": "o guia do prompt",
                                 "url": None}
           and p["instagram"]["share_to_feed"] is True and p["plataformas"] == ["instagram", "facebook"])
        ok("linha na Agenda do calendário",
           "| 2026-09-16 19:00 | _teste | instagram, facebook | agendado (confirmar) |" in agenda(root), str(agenda(root)))
        ok("tracker com _teste agendado", "| agendado |" in tracker_linha(root, "_teste"), tracker_linha(root, "_teste"))
        rc, _ = rodar(env1, "agendar", "_teste2")
        aprovar_publicacao(root, "_teste2")
        ok("segundo pacote salta a vaga ocupada → sexta 19:00",
           rc == 0 and post(root, "_teste2")["publicar_em"] == "2026-09-18T19:00:00+01:00",
           post(root, "_teste2")["publicar_em"])
        rc, _ = rodar(env1, "agendar", "_teste")
        ok("reagendar sem --reagendar mantém a vaga", post(root, "_teste")["publicar_em"] == "2026-09-16T19:00:00+01:00")
        ok("sem linhas duplicadas na Agenda", sum("| _teste |" in ln for ln in agenda(root)) == 1)

        print("\n== validações ==")
        criar_pacote(root, "_hashtags", hashtags=6)
        rc, out = rodar(env1, "agendar", "_hashtags")
        ok("recusa >5 hashtags", rc == 1 and "6 hashtags" in out)
        criar_pacote(root, "_qa", qa="FAIL")
        rc, out = rodar(env1, "agendar", "_qa")
        ok("recusa QA ≠ PASS", rc == 1 and "QA não é PASS" in out)
        criar_pacote(root, "_semfb", fb=False)
        rc, out = rodar(env1, "agendar", "_semfb")
        ok("recusa sem legenda do Facebook", rc == 1 and "legenda-facebook.txt" in out)
        criar_pacote(root, "_longa", legenda_extra="x" * 2300)
        rc, out = rodar(env1, "agendar", "_longa")
        ok("recusa legenda IG > 2200", rc == 1 and "(máx. 2200)" in out)
        for s in ("_hashtags", "_qa", "_semfb", "_longa"):
            shutil.rmtree(root / "06-publicar" / s)

        print("\n== GAUNTLET (portões) ==")
        criar_pacote(root, "_semselo", selo=False)
        rc, out = rodar(env1, "agendar", "_semselo")
        ok("recusa pacote sem selo GAUNTLET", rc == 1 and "sem selo GAUNTLET" in out, out[-300:])
        (root / "_controle" / "gauntlet-legado.json").write_text(json.dumps({"slugs": ["_semselo"]}))
        rc, out = rodar(env1, "agendar", "_semselo", "--dry-run")
        ok("pacote da lista LEGADO congelada passa, com aviso", rc == 0 and "LEGADO" in out, out[-300:])
        (root / "_controle" / "gauntlet-legado.json").unlink()
        trocada = criar_pacote(root, "_trocada")
        from PIL import Image

        Image.new("RGB", (540, 960), (90, 40, 20)).save(trocada / "capa" / "capa.png")
        rc, out = rodar(env1, "agendar", "_trocada")
        ok("recusa capa trocada depois do selo (caso das capas de 21/10)",
           rc == 1 and "trocado depois do selo" in out, out[-300:])
        criar_pacote(root, "_semportao", publicacao=False)
        rc, out = rodar(env1, "agendar", "_semportao", "--dry-run")
        ok("agendar não exige o portão da publicação (ele audita o post.json do agendar)", rc == 0, out[-300:])
        rc, out = rodar(env1, "publicar", "_semportao", "--dry-run", "--sim")
        ok("publicar sem PORTÃO-PUBLICACAO aprovado é recusado", rc == 1 and "portão publicacao" in out, out[-300:])
        for s in ("_semselo", "_trocada", "_semportao"):
            shutil.rmtree(root / "06-publicar" / s)
        rc, out = rodar(env1, "agendar", "_nao_existe")
        ok("slug fora de 06-publicar é recusado", rc == 1 and "não está em 06-publicar" in out)

        print("\n== --due ==")
        env2 = env_teste(root, AGORA_2)
        antes = (root / "06-publicar/_teste/post.json").read_text()
        rc, out = rodar(env2, "--due", "--dry-run")
        ok("--due --dry-run: anuncia aguardando_confirmacao sem escrever",
           rc == 0 and "aguardando_confirmacao" in out and (root / "06-publicar/_teste/post.json").read_text() == antes)
        rc, out = rodar(env2, "--due")
        ok("--due: confirmar=true → aguardando_confirmacao (não publica)",
           rc == 0 and post(root, "_teste")["estado"] == "aguardando_confirmacao" and "[notificação]" in out)
        ok("--due não mexe no post futuro", post(root, "_teste2")["estado"] == "agendado")
        ok("Agenda → aguardando confirmação", any("_teste |" in ln and "aguardando confirmação" in ln for ln in agenda(root)))

        print("\n== publicar --dry-run ==")
        cal_antes = (root / "_controle/calendario.md").read_text()
        post_antes = (root / "06-publicar/_teste/post.json").read_text()
        rc, out = rodar(env2, "publicar", "_teste", "--dry-run", "--sim")
        print("\n".join("    │ " + ln for ln in out.splitlines()[:60]))
        esperado = [f"POST https://graph.facebook.com/v23.0/{IG_ID}/media", "media_type = REELS",
                    "video_url = https://media.exemplo.test/reels/_teste/video-final.mp4",
                    "cover_url = https://media.exemplo.test/reels/_teste/capa.jpg", "share_to_feed = true",
                    f"GET https://graph.facebook.com/v23.0/DRYRUN_IG_CONTAINER", "fields = status_code,status",
                    f"POST https://graph.facebook.com/v23.0/{IG_ID}/media_publish", "creation_id = DRYRUN_IG_CONTAINER",
                    f"POST https://graph.facebook.com/v23.0/{PAGE_ID}/video_reels", "upload_phase = start",
                    "POST https://rupload.facebook.com/video-upload/v23.0/DRYRUN_FB_VIDEO_ID",
                    "Authorization = OAuth EAAG…(", "offset = 0", "file_size = ", "(binário)",
                    "upload_phase = finish", "video_state = PUBLISHED", "access_token = EAAG…(",
                    "R2 PUT https://contafalsa.r2.cloudflarestorage.com/korvu-teste/reels/_teste/video-final.mp4",
                    "reels/_teste/material/guia.pdf", "dm-material.json", "07-publicados/_teste",
                    "modo_confirmar_restantes → 1", "→ REEL (/{page-id}/video_reels)",
                    "/comments", "message = Você já usa o ChatGPT no trabalho?"]
        faltam = [e for e in esperado if e not in out]
        ok("dry-run imprime todos os pedidos esperados", rc == 0 and not faltam, "faltam: " + str(faltam) if faltam else "")
        ok("dry-run não escreve nada local",
           (root / "06-publicar/_teste").is_dir() and (root / "_controle/calendario.md").read_text() == cal_antes
           and (root / "06-publicar/_teste/post.json").read_text() == post_antes)
        rc, out = rodar(env_teste(root, AGORA_2, META_GRAPH_VERSION="v24.0"), "publicar", "_teste", "--dry-run", "--sim")
        ok("META_GRAPH_VERSION muda a versão nas URLs", "graph.facebook.com/v24.0/" in out and "video-upload/v24.0/" in out)
        rc, out = rodar(env2, "publicar", "_teste")
        ok("sem --sim um post com confirmar=true é recusado", rc == 1 and "--sim" in out)
        rc, out = rodar(env2, "verificar-tokens", "--dry-run")
        ok("verificar-tokens --dry-run", rc == 0 and "debug_token" in out and "123456|apps…(" in out, out[-300:] if rc else "")

        print("\n== publicar (fluxo completo, Meta e R2 simuladas em processo) ==")
        os.environ.update(env2)
        spec = importlib.util.spec_from_file_location("publicar_mod", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        buf = io.StringIO()
        h = logging.StreamHandler(buf)
        mod.configurar_log()
        mod.log.addHandler(h)
        mod.dormir = lambda s: None
        import boto3
        import requests

        s3 = FakeS3()
        boto3.client = lambda *a, **k: s3
        fake = FakeMeta()
        requests.Session.request = lambda self, method, url, **kw: fake(self, method, url, **kw)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = mod.main(["publicar", "_teste", "--sim"])
        dest = root / "07-publicados" / "_teste"
        ok("publicar _teste --sim → rc 0 e pasta em 07-publicados", rc == 0 and dest.is_dir()
           and not (root / "06-publicar/_teste").exists())
        p = post(root, "_teste", "07-publicados")
        ok("post.json: estado publicado + ids + permalinks",
           p["estado"] == "publicado" and p["publicado_em"] and p["instagram"]["container_id"] == "IGC1"
           and p["instagram"]["media_id"] == "IGM1" and p["instagram"]["permalink"] == "https://www.instagram.com/reel/ABC123/"
           and p["facebook"]["video_id"] == "FBV1" and p["facebook"]["permalink"] == "https://www.facebook.com/reel/FBV1/",
           json.dumps({k: p[k] for k in ("estado", "instagram", "facebook")}, ensure_ascii=False)[:300])
        ok("material.url no R2", p["material"]["url"] == "https://media.exemplo.test/reels/_teste/material/guia.pdf")
        dm = json.loads((dest / "dm-material.json").read_text())
        ok("dm-material.json", dm == {"palavra": "PROMPT", "media_id_instagram": "IGM1",
                                      "material_url": "https://media.exemplo.test/reels/_teste/material/guia.pdf"})
        ok("só o PDF do material sobe (dossie.md fica fora do R2)",
           not any("dossie" in k for _, k, _ in s3.enviados) and "NÃO vão para o R2: dossie.md" in buf.getvalue())
        ok("uploads R2 em reels/_teste/", sorted(k for _, k, _ in s3.enviados) ==
           ["reels/_teste/capa.jpg", "reels/_teste/material/guia.pdf", "reels/_teste/video-final.mp4"],
           str(s3.enviados))
        cont = fake.achar(f"/{IG_ID}/media", "POST")[0]["data"]
        ok("container IG: REELS + video_url + cover_url + caption",
           cont["media_type"] == "REELS" and cont["video_url"].endswith("video-final.mp4")
           and cont["cover_url"].endswith("capa.jpg") and cont["caption"].startswith("ChatGPT") and "trial_params" not in cont)
        ok("polling do container até FINISHED", fake.polls == 3)
        rup_c = fake.achar("rupload.facebook.com")[0]
        rup = rup_c["headers"]
        ok("rupload com Authorization OAuth + vídeo enviado do disco (sem file_url)",
           rup["Authorization"] == f"OAuth {TOKEN_PG}" and "file_url" not in rup and rup["offset"] == "0"
           and int(rup["file_size"]) == rup_c["data"]["_bytes"] > 0)
        fin = [c for c in fake.achar("/video_reels") if c["data"].get("upload_phase") == "finish"][0]["data"]
        ok("finish FB com video_state=PUBLISHED + description", fin["video_state"] == "PUBLISHED" and fin["description"])
        ok("--sim desconta modo_confirmar_restantes (2 → 1)", cal_restantes(root) == 1)
        ok("Agenda → publicado", any("_teste |" in ln and ln.rstrip().endswith("| publicado |") for ln in agenda(root)))
        ok("tracker → publicado", "| publicado |" in tracker_linha(root, "_teste"))
        coms = fake.achar("/comments", "POST")
        ok("primeiro comentário no IG e no FB, com o texto do arquivo",
           [c["url"].split("/")[-2] for c in coms] == ["IGM1", "FBV1"]
           and all(c["data"]["message"].startswith("Você já usa o ChatGPT") for c in coms), str(coms)[:200])
        ok("ids do primeiro comentário no post.json",
           p["primeiro_comentario"]["instagram_id"] == "COM-IGM1" and p["primeiro_comentario"]["facebook_id"] == "COM-FBV1",
           str(p.get("primeiro_comentario")))

        print("\n== primeiro comentário falha → a publicação vale; `comentar` repete ==")
        criar_pacote(root, "_coment")
        fake_c = FakeMeta(comentario_falha=True)
        requests.Session.request = lambda self, method, url, **kw: fake_c(self, method, url, **kw)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = mod.main(["publicar", "_coment"])
        pc = post(root, "_coment", "07-publicados")
        ok("comentário recusado não impede a publicação", rc == 0 and pc["estado"] == "publicado"
           and any(e["plataforma"] == "instagram-comentario" for e in pc["erros"]), str(pc["erros"])[:200])
        fake_c2 = FakeMeta()
        requests.Session.request = lambda self, method, url, **kw: fake_c2(self, method, url, **kw)
        (root / "07-publicados/_coment/primeiro-comentario.txt").write_text("Texto trocado depois do portão.\n")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = mod.main(["comentar", "_coment"])
        ok("`comentar` recusa texto que o portão não aprovou (CGI-P5)", rc == 1 and not fake_c2.achar("/comments", "POST"))
        gauntlet(root, "aprovar", str(root / "07-publicados" / "_coment"), "publicacao")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = mod.main(["comentar", "_coment"])
        pc = post(root, "_coment", "07-publicados")
        ok("`comentar` faz o que faltou", rc == 0 and pc["primeiro_comentario"]["instagram_id"] == "COM-IGM1"
           and pc["primeiro_comentario"]["facebook_id"] == "COM-FBV1")
        with contextlib.redirect_stdout(io.StringIO()):
            mod.main(["comentar", "_coment"])
        ok("`comentar` de novo não duplica", len(fake_c2.achar("/comments", "POST")) == 2)

        print("\n== falha só no Facebook (IG mantém-se) + nova tentativa ==")
        fake2 = FakeMeta(fb_falha=True)
        requests.Session.request = lambda self, method, url, **kw: fake2(self, method, url, **kw)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = mod.main(["publicar", "_teste2", "--sim"])
        p2 = post(root, "_teste2")
        ok("FB falhou → rc 1, estado erro, fica em 06-publicar", rc == 1 and p2["estado"] == "erro")
        ok("IG publicado e guardado mesmo com erro no FB", p2["instagram"]["media_id"] == "IGM1"
           and (root / "06-publicar/_teste2/dm-material.json").exists())
        ok("erro do FB registado em PT-BR com dica", any(e["plataforma"] == "facebook" and "Meta 500" in e["mensagem"]
                                                         for e in p2["erros"]), str(p2["erros"])[:200])
        ok("5xx com retry/backoff (5 tentativas)", len(fake2.achar("/video_reels")) == 5)
        ok("sem desconto de confirmação quando falha", cal_restantes(root) == 1)
        fake3 = FakeMeta()
        requests.Session.request = lambda self, method, url, **kw: fake3(self, method, url, **kw)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = mod.main(["publicar", "_teste2", "--sim"])
        ok("nova tentativa só repete o Facebook", rc == 0 and not fake3.achar(f"/{IG_ID}/media", "POST")
           and fake3.achar("/video_reels"))
        ok("_teste2 publicado e movido", post(root, "_teste2", "07-publicados")["estado"] == "publicado")
        ok("modo_confirmar_restantes 1 → 0", cal_restantes(root) == 0)

        print("\n== Facebook: > 90 s vira vídeo da Página, ≤ 90 s continua Reel ==")
        criar_pacote(root, "_longo", duracao=120.0)
        rc, out = rodar(env2, "publicar", "_longo", "--dry-run")
        ok("dry-run 120 s: mostra o caminho de vídeo da Página (upload retomável start/finish, published=true)",
           rc == 0 and "VÍDEO DA PÁGINA" in out and f"POST https://graph-video.facebook.com/v23.0/{PAGE_ID}/videos" in out
           and "upload_phase = start" in out and "upload_phase = finish" in out and "published = true" in out
           and "/video_reels" not in out.split("VÍDEO DA PÁGINA", 1)[1], out[-600:] if rc else "")
        fake4 = FakeMeta()
        requests.Session.request = lambda self, method, url, **kw: fake4(self, method, url, **kw)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = mod.main(["publicar", "_longo"])
        pv = fake4.achar(f"/{PAGE_ID}/videos", "POST")
        fases = [c["data"].get("upload_phase") for c in pv]
        tam = (root / "06-publicar/_longo/video/video-final.mp4").stat().st_size if (root / "06-publicar/_longo/video/video-final.mp4").exists() else None
        enviados = sum(c["files"]["video_file_chunk"][1] for c in pv if c["data"].get("upload_phase") == "transfer")
        ok("120 s → upload retomável: start → transfer em pedaços (soma = arquivo) → finish com description e published=true",
           rc == 0 and fases[0] == "start" and fases[-1] == "finish" and fases.count("transfer") >= 2
           and all(c["url"].startswith("https://graph-video.facebook.com/v23.0/") for c in pv)
           and enviados == int(pv[0]["data"]["file_size"]) and (tam is None or enviados == tam)
           and pv[-1]["data"]["published"] == "true" and pv[-1]["data"]["description"].startswith("ChatGPT")
           and "file_url" not in pv[-1]["data"], str(fases))
        ok("120 s → nenhuma chamada à API de Reels do FB nem ao rupload",
           not fake4.achar("/video_reels") and not fake4.achar("rupload.facebook.com"))
        ok("120 s → Instagram continua Reel", fake4.achar(f"/{IG_ID}/media", "POST")[0]["data"]["media_type"] == "REELS")
        pl = post(root, "_longo", "07-publicados")
        ok("120 s → post.facebook = {tipo: video, video_id, permalink}",
           pl["facebook"]["tipo"] == "video" and pl["facebook"]["video_id"] == "FBPV1"
           and pl["facebook"]["permalink"] == "https://www.facebook.com/korvu/videos/FBPV1/", str(pl["facebook"]))
        ok("token mascarado no log do vídeo da Página", not any(sg in buf.getvalue() for sg in SEGREDOS))

        criar_pacote(root, "_curto", duracao=60.0)
        fake5 = FakeMeta()
        requests.Session.request = lambda self, method, url, **kw: fake5(self, method, url, **kw)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = mod.main(["publicar", "_curto"])
        pc = post(root, "_curto", "07-publicados")
        ok("60 s → Reel (video_reels start/finish + rupload), sem /videos",
           rc == 0 and len(fake5.achar("/video_reels")) == 2 and fake5.achar("rupload.facebook.com")
           and not fake5.achar(f"/{PAGE_ID}/videos"))
        ok("60 s → post.facebook = {tipo: reel, video_id FBV1, permalink /reel/}",
           pc["facebook"]["tipo"] == "reel" and pc["facebook"]["video_id"] == "FBV1"
           and pc["facebook"]["permalink"] == "https://www.facebook.com/reel/FBV1/", str(pc["facebook"]))
        sem_dur = criar_pacote(root, "_semdur", duracao=None)
        d = mod.duracao_video(json.loads((sem_dur / "pacote.json").read_text()), sem_dur / "video/video-final.mp4")
        ok("sem pacote.duracao → mede com ffprobe (3,5 s → Reel)", d is not None and abs(d - 3.5) < 0.1, str(d))
        ok("pacote.duracao tem prioridade sobre o ffprobe",
           mod.duracao_video({"duracao": 120}, sem_dur / "video/video-final.mp4") == 120.0)
        shutil.rmtree(sem_dur)

        print("\n== carrossel: montar → agendar → portão → publicar (09/11) ==")
        cs = "_carrossel"
        origem = criar_carrossel(root, cs)
        rc, out = montar(root, origem)
        ok("montar_pacote recusa carrossel sem portões", rc == 1 and "portões GAUNTLET" in out, out[-200:])
        gauntlet(root, "aprovar", str(origem), "roteiro", "imagem")
        rc, out = montar(root, origem)
        pac_c = json.loads((root / "05-render-pronto" / cs / "pacote.json").read_text()) if rc == 0 else {}
        ok("montar_pacote: formato carrossel, 9 slides, PDF, selo", rc == 0 and pac_c.get("formato") == "carrossel"
           and pac_c["arquivos"]["slides"] == [f"slides/{i:02d}.png" for i in range(1, 10)]
           and pac_c["arquivos"]["material"] == "material/cursos.pdf" and pac_c["cta_palavra"] == "ESTUDO"
           and pac_c["gauntlet"]["origem"] == f"carrosseis/{cs}" and len(pac_c["gauntlet"]["arquivos"]) == 10,
           out[-300:])
        ok("a grade de prévia não entra nos slides do pacote",
           not (root / "05-render-pronto" / cs / "slides" / "grade.jpg").exists())
        curto = criar_carrossel(root, "_carrossel_curto", n=2)
        gauntlet(root, "aprovar", str(curto), "roteiro", "imagem")
        rc, out = montar(root, curto)
        ok("montar_pacote recusa carrossel com 2 slides", rc == 1 and "2 slides" in out, out[-200:])
        pasta_c = para_fila(root, cs)
        rc, out = rodar(env2, "agendar", cs, "--em", "2026-10-07 12:00")
        pc = post(root, cs)
        ok("agendar carrossel → post.json formato carrossel, sem capa e sem Trial",
           rc == 0 and pc.get("formato") == "carrossel" and "capa" not in pc["instagram"]
           and "trial" not in pc["instagram"] and pc["facebook"]["tipo"] == "fotos", out[-300:])
        rc, out = rodar(env2, "publicar", cs, "--dry-run", "--sim")
        ok("publicar carrossel sem PORTÃO-PUBLICACAO é recusado", rc == 1 and "portão publicacao" in out)
        aprovar_publicacao(root, cs)
        rc, out = rodar(env2, "publicar", cs, "--dry-run", "--sim")
        ok("dry-run do carrossel: 9 filhos IG + CAROUSEL + media_publish",
           rc == 0 and out.count("is_carousel_item = true") == 9 and "media_type = CAROUSEL" in out
           and "children = DRYRUN_IG_FILHO_01,DRYRUN_IG_FILHO_02" in out and "/media_publish" in out, out[-400:])
        ok("dry-run do carrossel: 9 fotos FB não publicadas + post /feed com attached_media",
           out.count(f"/{PAGE_ID}/photos") == 9 and "published = false" in out and f"/{PAGE_ID}/feed" in out
           and "attached_media[8]" in out and "video_reels" not in out and "rupload" not in out)
        ok("dry-run do carrossel: slides em JPEG no R2 + PDF + 1.º comentário + dm-material",
           f"carrosseis/{cs}/01.jpg" in out and "image/jpeg" in out and f"carrosseis/{cs}/material/cursos.pdf" in out
           and out.count("/comments") == 2 and "dm-material.json" in out)
        ok("dry-run do carrossel não escreve nada", post(root, cs) == pc and (root / "06-publicar" / cs).is_dir())
        troca = para_fila(root, "_carrossel_troca", de=cs)
        from PIL import Image

        Image.new("RGB", (1080, 1440), (200, 0, 0)).save(troca / "slides" / "03.png")
        rc, out = rodar(env2, "publicar", "_carrossel_troca", "--dry-run")
        ok("slide trocado na fila (não aprovado pelo PORTÃO-IMAGEM) é recusado",
           rc == 1 and "slides/03.png: trocado depois do selo" in out, out[-300:])
        shutil.rmtree(troca)

        s3c = FakeS3()
        boto3.client = lambda *a, **k: s3c
        fake_car = FakeMeta()
        requests.Session.request = lambda self, method, url, **kw: fake_car(self, method, url, **kw)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = mod.main(["publicar", cs, "--sim"])
        dest_c = root / "07-publicados" / cs
        pcar = post(root, cs, "07-publicados") if dest_c.is_dir() else {}
        ok("carrossel publicado → 07-publicados", rc == 0 and pcar.get("estado") == "publicado"
           and not (root / "06-publicar" / cs).exists())
        filhos = [c for c in fake_car.achar(f"/{IG_ID}/media", "POST") if c["data"].get("is_carousel_item")]
        pai = [c for c in fake_car.achar(f"/{IG_ID}/media", "POST") if c["data"].get("media_type") == "CAROUSEL"]
        ok("IG: 9 filhos com image_url JPEG, na ordem", len(filhos) == 9 and all(
            c["data"]["image_url"] == f"https://media.exemplo.test/carrosseis/{cs}/{i:02d}.jpg"
            for i, c in enumerate(filhos, 1)))
        ok("IG: contêiner CAROUSEL com children na ordem + legenda", len(pai) == 1
           and pai[0]["data"]["children"] == ",".join(f"IGF{i}" for i in range(1, 10))
           and pai[0]["data"]["caption"].startswith("6 cursos"))
        ok("post.json IG: filhos, contêiner, media e permalink",
           pcar["instagram"]["filhos"] == [f"IGF{i}" for i in range(1, 10)]
           and pcar["instagram"]["container_id"] == "IGCAR1" and pcar["instagram"]["media_id"] == "IGM1"
           and pcar["instagram"]["permalink"])
        fotos = fake_car.achar(f"/{PAGE_ID}/photos", "POST")
        feed = fake_car.achar(f"/{PAGE_ID}/feed", "POST")
        ok("FB: 9 fotos do disco (multipart source PNG, published=false)", len(fotos) == 9
           and all(c["data"]["published"] == "false" and c["files"]["source"][0] == f"{i:02d}.png"
                   for i, c in enumerate(fotos, 1)))
        ok("FB: um post /feed com as 9 fotos em ordem + legenda", len(feed) == 1
           and [json.loads(feed[0]["data"][f"attached_media[{i}]"])["media_fbid"] for i in range(9)]
           == [f"FBF{i}" for i in range(1, 10)] and feed[0]["data"]["message"].startswith("6 cursos"))
        ok("post.json FB: tipo fotos, post_id, permalink", pcar["facebook"]["tipo"] == "fotos"
           and pcar["facebook"]["post_id"] == f"{PAGE_ID}_777"
           and pcar["facebook"]["permalink"] == f"https://www.facebook.com/{PAGE_ID}/posts/777")
        ok("R2: 9 JPEG + o PDF, em carrosseis/<slug>/", sorted(k for _, k, _ in s3c.enviados)
           == [f"carrosseis/{cs}/{i:02d}.jpg" for i in range(1, 10)] + [f"carrosseis/{cs}/material/cursos.pdf"]
           and all(ct == "image/jpeg" for _, k, ct in s3c.enviados if k.endswith(".jpg")))
        coms_c = fake_car.achar("/comments", "POST")
        ok("primeiro comentário no IG (media) e no FB (post da Página)",
           [c["url"].split("/")[-2] for c in coms_c] == ["IGM1", f"{PAGE_ID}_777"]
           and pcar["primeiro_comentario"]["facebook_id"] == f"COM-{PAGE_ID}_777")
        dm_c = json.loads((dest_c / "dm-material.json").read_text())
        ok("dm-material.json do carrossel", dm_c == {"palavra": "ESTUDO", "media_id_instagram": "IGM1",
                                                     "formato": "carrossel",
                                                     "material_url": f"https://media.exemplo.test/carrosseis/{cs}/material/cursos.pdf"})

        print("\n== trava contra execuções simultâneas ==")
        with mod.trava():
            rc, out = rodar(env2, "--due")
        ok("segunda execução sai sem fazer nada", rc == 0 and "Outra execução" in out)

        ok("nenhum segredo no log em processo", not any(s in buf.getvalue() for s in SEGREDOS))

        print("\n== trial_padrao ==")
        cfg_trial = {"plataformas_padrao": ["instagram"], "trial_padrao": "SS_PERFORMANCE"}
        ok("trial_padrao no calendário → post.json com instagram.trial",
           mod.post_padrao("_x", {}, cfg_trial)["instagram"]["trial"] == {"graduation_strategy": "SS_PERFORMANCE"}
           and mod.post_padrao("_x", {}, {})["instagram"]["trial"] is None)

        print("\n== launchd ==")
        _pl = Path.home() / "Library/LaunchAgents/uk.korvu.publicar.plist"
        plist_antes = _pl.stat().st_mtime if _pl.exists() else None
        gerado = root / "uk.korvu.publicar.plist"
        r = subprocess.run(["bash", str(PROJETO / "scripts/launchd/instalar.sh"), "--so-gerar", str(gerado)],
                           capture_output=True, text=True)
        txt = gerado.read_text() if gerado.exists() else ""
        ok("plist gerado e válido (plutil -lint), sem instalar",
           r.returncode == 0 and "__" not in txt and f"<string>{PROJETO}</string>" in txt
           and "<integer>900</integer>" in txt and "_controle/logs/publicar.log" in txt, r.stderr.strip())
        instalado = Path.home() / "Library/LaunchAgents/uk.korvu.publicar.plist"
        ok("não instalou nada em ~/Library/LaunchAgents",
           (not instalado.exists()) or instalado.stat().st_mtime == plist_antes)
    finally:
        if manter:
            print(f"\n(ROOT mantido em {root})")
        else:
            shutil.rmtree(root, ignore_errors=True)

    falhas = [n for n, c, _ in RES if not c]
    print(f"\n{len(RES) - len(falhas)}/{len(RES)} verificações OK")
    for n in falhas:
        print(f"  FALHOU: {n}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())

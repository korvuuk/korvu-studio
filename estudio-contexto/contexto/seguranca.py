"""Lista de exclusão FIXA (no código) e detector de tokens — ESPECIFICACAO.md §2 e §7.

Esta lista não pode ser desligada pelo corpus.yaml: ela vence qualquer `incluir`. Vale na indexação E nas respostas
do servidor MCP (um trecho de arquivo excluído nunca é devolvido, mesmo que esteja no banco por engano).
"""
from __future__ import annotations

import fnmatch
import re
from pathlib import PurePosixPath

# Segredos: nunca indexar, nunca devolver.
SEGREDOS = (".env", ".env.*", "**/.env", "**/.env.*", "painel/web/.env.local", "**/*.pem", "**/*.key",
            "**/credentials*.json", "**/token*.json", "**/client_secret*.json", "**/*.secret")

# Mídia e pastas de mídia (§2 "Fora").
MIDIA_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".wav", ".mp3", ".m4a", ".aac", ".braw", ".r3d", ".png", ".jpg",
             ".jpeg", ".gif", ".webp", ".heic", ".pdf", ".cube", ".zip"}
PASTAS_FORA = ("07-publicados/", "05-render-pronto/", "06-publicar/", "BG VIDEO/", "node_modules/", ".venv/",
               ".git/", ".claude/skills/", "02-calibracao/amostras/")
PADROES_FORA = ("**/node_modules/**", "**/.venv/**", "**/.git/**", "**/.next*/**", "videos/*/brutos/**",
                "videos/*/edicao/**", "videos/*/fontes/**", "videos/*/animacoes/**")

# Só texto entra no índice.
TEXTO_EXT = {".md", ".yaml", ".yml", ".json", ".txt"}

# Padrões de token/chave. Um arquivo com qualquer um deles é recusado inteiro (§2: "qualquer arquivo cujo conteúdo
# traga token ou chave"). Pensados para não pegar "sk-" dentro de palavras (falso positivo visto em 01-ideias/, §14).
PADROES_TOKEN = [
    ("chave_privada", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("openai", re.compile(r"(?<![A-Za-z0-9])sk-(?:proj-|ant-)?[A-Za-z0-9_\-]{32,}")),
    ("meta", re.compile(r"(?<![A-Za-z0-9])EAA[A-Za-z0-9]{60,}")),
    ("github", re.compile(r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{30,}")),
    ("aws", re.compile(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])")),
    ("slack", re.compile(r"(?<![A-Za-z0-9])xox[abprs]-[A-Za-z0-9\-]{20,}")),
    ("google", re.compile(r"(?<![A-Za-z0-9])AIza[0-9A-Za-z_\-]{35}")),
    ("linkedin", re.compile(r"(?<![A-Za-z0-9])AQ[A-Za-z0-9_\-]{150,}")),
    ("jwt", re.compile(r"(?<![A-Za-z0-9])eyJ[A-Za-z0-9_\-]{15,}\.eyJ[A-Za-z0-9_\-]{15,}\.[A-Za-z0-9_\-]{20,}")),
    ("supabase", re.compile(r"(?<![A-Za-z0-9])sb_(?:secret|publishable)_[A-Za-z0-9_\-]{20,}")),
    ("elevenlabs", re.compile(r"(?<![A-Za-z0-9])sk_[a-f0-9]{40,}")),
    ("atribuicao", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|access[_-]?token|client[_-]?secret|password|senha)\b\s*[:=]\s*['\"]?"
        r"(?=[A-Za-z0-9/+_\-]*\d)(?=[A-Za-z0-9/+_\-]*[A-Za-z])[A-Za-z0-9/+_\-]{24,}")),
]


# Identificadores de conta que aparecem nos documentos (não são credenciais, mas são valores do .env): o texto é
# indexado com eles mascarados. Mudou a lista? Suba VERSAO_MASCARA (os arquivos são redivididos).
VERSAO_MASCARA = "4"
MASCARAS = [
    (re.compile(r"\burn:li:(person|member|organization):[A-Za-z0-9_\-]+"), r"urn:li:\1:[oculto]"),
    (re.compile(r"(?i)(\bbucket\s+[`'\"]?)([a-z0-9][a-z0-9.\-]{2,62})([`'\"]?)"), r"\1[oculto]\3"),
    (re.compile(r"\bpub-[a-f0-9]{32}\.r2\.dev\b"), "[oculto].r2.dev"),
    (re.compile(r"\b[a-f0-9]{32}\.r2\.cloudflarestorage\.com\b"), "[oculto].r2.cloudflarestorage.com"),
    (re.compile(r"(?i)(\b(?:act|ig|page|business|app)[_ ]?id\s*[:=]\s*`?)(\d{8,})"), r"\1[oculto]"),
]


RX_LINHA_R2 = re.compile(r"(?i)\bR2\b|bucket")
RX_NOME_BUCKET = re.compile(r"`([a-z0-9][a-z0-9._-]{2,62})`")


def mascarar(texto: str) -> str:
    for rx, troca in MASCARAS:
        texto = rx.sub(troca, texto)
    # num parágrafo que fala de R2/bucket, nome entre crases com formato de bucket (minúsculas, sem barra) é mascarado
    if RX_LINHA_R2.search(texto):
        texto = "\n\n".join(RX_NOME_BUCKET.sub(_bucket, p) if RX_LINHA_R2.search(p) else p
                             for p in texto.split("\n\n"))
    return texto


def _bucket(m: re.Match) -> str:
    nome = m[1]
    # nomes de arquivo, agente ou script não são bucket
    if re.search(r"\.(py|md|json|sh|ya?ml|mjs|ts|tsx|pdf|png|txt|plist|env)$", nome) or nome.isdigit() \
            or nome in {"true", "false", "null", "none", "public", "private"} or nome.startswith(("portao-", "revisor-")):
        return m[0]
    return "`[oculto]`"


def _casa(caminho: str, padroes) -> bool:
    p = PurePosixPath(caminho)
    for pad in padroes:
        if fnmatch.fnmatch(caminho, pad) or p.match(pad):
            return True
        # "**/x" também casa "x" na raiz
        if pad.startswith("**/") and (fnmatch.fnmatch(caminho, pad[3:]) or p.match(pad[3:])):
            return True
    return False


def motivo_exclusao(caminho: str) -> str | None:
    """Motivo para recusar o caminho (relativo à raiz, com '/'), ou None se pode entrar."""
    c = caminho.removeprefix("./")
    nome = PurePosixPath(c).name
    # .env, .env.local, .env.example (este também fica fora: não há por que indexar nomes de chaves)
    if nome.startswith(".env") or _casa(c, SEGREDOS):
        return "segredo"
    if PurePosixPath(c).suffix.lower() in MIDIA_EXT:
        return "midia"
    if any(c.startswith(p) or f"/{p}" in f"/{c}" for p in PASTAS_FORA):
        return "pasta_fora"
    if _casa(c, PADROES_FORA):
        return "pasta_fora"
    if PurePosixPath(c).suffix.lower() not in TEXTO_EXT:
        return "nao_texto"
    return None


def excluido(caminho: str) -> bool:
    return motivo_exclusao(caminho) is not None


def tokens_no_texto(texto: str) -> list[str]:
    """Nomes dos padrões de token encontrados (nunca o valor)."""
    return [nome for nome, rx in PADROES_TOKEN if rx.search(texto)]

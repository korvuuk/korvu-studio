#!/usr/bin/env python3
"""Gera uma imagem por IA para o estúdio — Gemini (via OpenRouter) ou OpenAI (gpt-image).

Integrado ao estúdio em 12/11, unindo duas integrações que já eram usadas em outros projetos.

Motores:
  teste   OpenRouter `sourceful/riverflow-v2-fast`        barato, para validar composição       OPENROUTER_API_KEY
  gemini  OpenRouter `google/gemini-3.1-flash-image-preview` final                                OPENROUTER_API_KEY
  openai  OpenAI `gpt-image-2` (images/generations | images/edits com --ref)  final                OPENAI_API_KEY

As chaves vêm do ambiente ou do `.env` da raiz (python-dotenv). Nunca são impressas, nem passadas em linha de
comando. Cada imagem gerada acrescenta uma linha em `<pasta da saída>/imagens-geradas.jsonl` (data, motor,
modelo, prompt, referências, saída) — para saber o que foi gerado, com quê, e conferir o gasto.

Regras do estúdio (CLAUDE.md regra 3): nunca imagem realista de pessoa real além do autor; logo de terceiro só
identificando a ferramenta. Antes de gerar, procure material livre (skill `gerar-imagem`, SKILL.md).

Uso:
  uv run python .claude/skills/gerar-imagem/scripts/gerar_imagem.py --saida <arquivo.png> --prompt "…" [--motor teste]
  … --prompt-arquivo prompt.txt --motor gemini --ref logo.png --ref estilo.png
  … --motor openai --tamanho 1024x1536 --qualidade high
  … --seco      mostra o que seria enviado (sem chave, sem rede, sem custo)
Saída: código 0 e "ok <arquivo>"; código 1 com o motivo do erro (sem a chave).
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
OPENROUTER = "https://openrouter.ai/api/v1/chat/completions"
OPENAI_GEN = "https://api.openai.com/v1/images/generations"
OPENAI_EDIT = "https://api.openai.com/v1/images/edits"

MOTORES = {
    "teste": {"api": "openrouter", "modelo": "sourceful/riverflow-v2-fast", "chave": "OPENROUTER_API_KEY"},
    "gemini": {"api": "openrouter", "modelo": "google/gemini-3.1-flash-image-preview", "chave": "OPENROUTER_API_KEY"},
    "openai": {"api": "openai", "modelo": "gpt-image-2", "chave": "OPENAI_API_KEY"},
}
TIMEOUT = 600


def erro(msg: str) -> None:
    print(f"[erro] {msg}", file=sys.stderr)
    sys.exit(1)


def chave(nome: str) -> str:
    if not os.environ.get(nome):
        try:
            from dotenv import load_dotenv
            load_dotenv(RAIZ / ".env", override=False)
        except ImportError:
            pass
    valor = os.environ.get(nome, "").strip()
    if not valor:
        erro(f"{nome} não está definida. O autor põe a chave no .env da raiz ({nome}=...) — "
             "não leia nem edite o .env por ele.")
    return valor


def data_url(caminho: Path) -> str:
    mime = mimetypes.guess_type(caminho.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(caminho.read_bytes()).decode()}"


def pedir(url: str, corpo: bytes, cabecalhos: dict) -> dict:
    req = urllib.request.Request(url, data=corpo, headers=cabecalhos, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        corpo_erro = e.read().decode(errors="replace")[:400]
        erro(f"a API respondeu {e.code}: {corpo_erro}")
    except (urllib.error.URLError, TimeoutError) as e:
        erro(f"sem resposta da API: {e}")
    return {}


def via_openrouter(modelo: str, prompt: str, refs: list[Path], k: str | None) -> tuple[bytes | None, dict]:
    texto = f"Generate an image: {prompt}. Only output the image, no text."
    if refs:
        conteudo = [{"type": "image_url", "image_url": {"url": data_url(r)}} for r in refs]
        conteudo.append({"type": "text", "text": "Use the reference image(s) above for brand and style. " + texto})
    else:
        conteudo = texto
    corpo = {"model": modelo, "messages": [{"role": "user", "content": conteudo}], "modalities": ["image", "text"]}
    if k is None:
        return None, {"url": OPENROUTER, "model": modelo, "referencias": len(refs)}
    dados = pedir(OPENROUTER, json.dumps(corpo).encode(),
                  {"Authorization": f"Bearer {k}", "Content-Type": "application/json"})
    msg = (dados.get("choices") or [{}])[0].get("message", {})
    imgs = msg.get("images") or []
    url = imgs[0].get("image_url", {}).get("url", "") if imgs else msg.get("content") or ""
    if not isinstance(url, str) or not url.startswith("data:image"):
        erro(f"o modelo {modelo} não devolveu imagem (resposta: {json.dumps(dados)[:300]})")
    return base64.b64decode(url.split(",", 1)[1]), dados.get("usage") or {}


def multipart(campos: dict, arquivos: list[tuple[str, Path]]) -> tuple[bytes, str]:
    limite = uuid.uuid4().hex
    partes: list[bytes] = []
    for nome, valor in campos.items():
        partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="{nome}"\r\n\r\n{valor}\r\n'.encode())
    for nome, caminho in arquivos:
        mime = mimetypes.guess_type(caminho.name)[0] or "image/png"
        partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="{nome}"; filename="{caminho.name}"\r\n'
                      f"Content-Type: {mime}\r\n\r\n".encode() + caminho.read_bytes() + b"\r\n")
    partes.append(f"--{limite}--\r\n".encode())
    return b"".join(partes), f"multipart/form-data; boundary={limite}"


def via_openai(modelo: str, prompt: str, refs: list[Path], tamanho: str, qualidade: str,
               k: str | None) -> tuple[bytes | None, dict]:
    url = OPENAI_EDIT if refs else OPENAI_GEN
    if k is None:
        return None, {"url": url, "model": modelo, "size": tamanho, "quality": qualidade, "referencias": len(refs)}
    if refs:
        corpo, tipo = multipart({"model": modelo, "prompt": prompt, "size": tamanho, "quality": qualidade},
                                [("image[]", r) for r in refs])
    else:
        corpo = json.dumps({"model": modelo, "prompt": prompt, "size": tamanho, "quality": qualidade}).encode()
        tipo = "application/json"
    dados = pedir(url, corpo, {"Authorization": f"Bearer {k}", "Content-Type": tipo})
    try:
        b64 = dados["data"][0]["b64_json"]
    except (KeyError, IndexError, TypeError):
        erro(f"a OpenAI não devolveu imagem (resposta: {json.dumps(dados)[:300]})")
    return base64.b64decode(b64), dados.get("usage") or {}


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera uma imagem por IA (Gemini via OpenRouter ou OpenAI).")
    ap.add_argument("--saida", required=True, type=Path)
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--prompt")
    grupo.add_argument("--prompt-arquivo", type=Path)
    ap.add_argument("--motor", choices=sorted(MOTORES), default="teste",
                    help="teste (barato, padrão) · gemini · openai")
    ap.add_argument("--ref", action="append", type=Path, default=[], help="imagem de referência (pode repetir)")
    ap.add_argument("--tamanho", default="1024x1536", help="só openai (ex.: 1024x1536, 1536x1024, 1024x1024)")
    ap.add_argument("--qualidade", default="high", help="só openai: low · medium · high")
    ap.add_argument("--seco", action="store_true", help="não chama a API: mostra o pedido e sai")
    a = ap.parse_args()

    prompt = (a.prompt if a.prompt is not None else a.prompt_arquivo.read_text(encoding="utf-8")).strip()
    if not prompt:
        erro("prompt vazio")
    for r in a.ref:
        if not r.is_file():
            erro(f"referência não encontrada: {r}")
    m = MOTORES[a.motor]

    k = None if a.seco else chave(m["chave"])
    if m["api"] == "openrouter":
        imagem, info = via_openrouter(m["modelo"], prompt, a.ref, k)
    else:
        imagem, info = via_openai(m["modelo"], prompt, a.ref, a.tamanho, a.qualidade, k)

    if a.seco:
        print(json.dumps({"seco": True, "motor": a.motor, "chave_usada": m["chave"], "saida": str(a.saida),
                          "prompt": prompt[:200], **info}, ensure_ascii=False, indent=2))
        return

    a.saida.parent.mkdir(parents=True, exist_ok=True)
    a.saida.write_bytes(imagem)
    registro = {
        "data": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "motor": a.motor, "modelo": m["modelo"], "prompt": prompt,
        "referencias": [r.name for r in a.ref], "saida": a.saida.name,
        "bytes": len(imagem), "uso": info,
    }
    with open(a.saida.parent / "imagens-geradas.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    print(f"ok {a.saida} ({len(imagem) // 1024} KB, {a.motor} · {m['modelo']})")


if __name__ == "__main__":
    main()

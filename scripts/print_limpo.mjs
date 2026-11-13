#!/usr/bin/env node
/**
 * Print de página oficial SEM banner de cookies/aviso (para os slides de carrossel).
 *
 * O `print_pagina.py` fotografa a página como ela abre — e quase todo site abre com um aviso de cookies, às vezes
 * no meio da tela (NVIDIA, Databricks), que nenhum recorte tira. Este script abre a página no Chrome do sistema
 * via DevTools, espera carregar, REMOVE os elementos fixos que falam de cookie/privacidade/consentimento e
 * fotografa. Não clica em "aceitar" nem grava nada no perfil (Chrome temporário).
 *
 * Uso: node scripts/print_limpo.mjs <url> <saida.png> [--espera 6000] [--largura 1440] [--altura 900]
 * Saída em 2× (1440×900 lógicos → 2880×1800 px). Conferir o PNG olhando.
 * Requer o Chrome do sistema; não instala nada (Node ≥ 22 já tem WebSocket).
 */
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const args = process.argv.slice(2);
const opt = (k, d) => (args.includes(k) ? Number(args[args.indexOf(k) + 1]) : d);
const [url, saida] = args.filter((a, i) => !a.startsWith("--") && !(i > 0 && args[i - 1].startsWith("--")));
if (!url || !saida) {
  console.error("uso: node scripts/print_limpo.mjs <url> <saida.png> [--espera ms] [--largura px] [--altura px]");
  process.exit(2);
}
const ESPERA = opt("--espera", 6000), LARG = opt("--largura", 1440), ALT = opt("--altura", 900);
const PORTA = 9300 + Math.floor(Math.random() * 500);
const perfil = mkdtempSync(join(tmpdir(), "print-limpo-"));
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--mute-audio",
  `--remote-debugging-port=${PORTA}`, `--user-data-dir=${perfil}`, `--window-size=${LARG},${ALT}`, "about:blank"],
  { stdio: "ignore" });
const dormir = (ms) => new Promise((r) => setTimeout(r, ms));

// remove o que estiver fixo/por cima e falar de cookie/privacidade/consentimento; destrava o scroll
const LIMPAR = `(() => {
  const re = /cookie|privacidade|privacy|consent|gdpr|lgpd/i;
  let n = 0;
  for (const el of document.querySelectorAll('body *')) {
    const st = getComputedStyle(el);
    if (!['fixed', 'sticky'].includes(st.position) && !(st.position === 'absolute' && +st.zIndex > 999)) continue;
    if (re.test(el.innerText || '') || re.test(el.id + ' ' + el.className)) { el.remove(); n++; }
  }
  for (const id of ['onetrust-consent-sdk', 'truste-consent-track', 'CybotCookiebotDialog']) document.getElementById(id)?.remove();
  for (const el of [document.documentElement, document.body]) { el.style.overflow = 'visible'; el.classList.remove('modal-open'); }
  return n;
})()`;

try {
  let alvo;
  for (let i = 0; i < 50 && !alvo; i++) {
    await dormir(200);
    try {
      alvo = (await (await fetch(`http://127.0.0.1:${PORTA}/json`)).json()).find((t) => t.type === "page");
    } catch {}
  }
  if (!alvo) throw new Error("Chrome não abriu o DevTools");
  const ws = new WebSocket(alvo.webSocketDebuggerUrl);
  await new Promise((r, e) => { ws.onopen = r; ws.onerror = e; });
  let seq = 0;
  const pend = new Map();
  ws.onmessage = (m) => { const d = JSON.parse(m.data); pend.get(d.id)?.(d); pend.delete(d.id); };
  const cdp = (method, params = {}) => new Promise((r) => { const id = ++seq; pend.set(id, r); ws.send(JSON.stringify({ id, method, params })); });

  await cdp("Emulation.setDeviceMetricsOverride", { width: LARG, height: ALT, deviceScaleFactor: 2, mobile: false });
  await cdp("Page.enable");
  await cdp("Page.navigate", { url });
  await dormir(ESPERA);
  const r1 = await cdp("Runtime.evaluate", { expression: LIMPAR, returnByValue: true });
  await dormir(800); // aviso que reaparece depois de removido
  const r2 = await cdp("Runtime.evaluate", { expression: LIMPAR, returnByValue: true });
  await dormir(500);
  const shot = await cdp("Page.captureScreenshot", { format: "png" });
  if (!shot.result?.data) throw new Error("sem imagem: " + JSON.stringify(shot.error ?? shot));
  writeFileSync(resolve(saida), Buffer.from(shot.result.data, "base64"));
  console.log(`Print: ${resolve(saida)} (${LARG * 2}×${ALT * 2}) — ${r1.result?.result?.value ?? 0}+${r2.result?.result?.value ?? 0} avisos removidos`);
  ws.close();
} catch (e) {
  console.error("ERRO:", e.message);
  process.exitCode = 1;
} finally {
  chrome.kill("SIGKILL");
  await dormir(300);
  rmSync(perfil, { recursive: true, force: true });
}

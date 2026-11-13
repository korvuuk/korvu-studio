"use client";

import { useLayoutEffect, useRef, useState, useSyncExternalStore } from "react";

// Número que conta até o valor (Movimento v2, design-system.md §7.2): recebe o texto JÁ formatado em pt-BR ("1.493",
// "8,4", "−12") e sobe de zero até ele quando entra na tela, na curva que só desacelera. Mantém as casas decimais e o
// ponto de milhar do original. Texto que não é só número ("23 out", "—") sai como veio. O servidor manda o valor final
// (sem JavaScript e no leitor de tela é sempre ele); com "menos movimento", nada conta. Número que JÁ apareceu pronto
// (o 1.º carregamento hidrata o HTML do servidor) não zera na frente de quem leu: só conta se nasceu no navegador
// (entrar pelo menu) ou se ainda estava abaixo da dobra.

const NUMERO = /^([+−-]?)(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?$/;
const DURACAO = 700;
const nada = () => () => {};

function escrever(v: number, casas: number, milhar: boolean) {
  const [int, dec] = v.toFixed(casas).split(".");
  const inteiro = milhar ? int.replace(/\B(?=(\d{3})+(?!\d))/g, ".") : int;
  return dec ? `${inteiro},${dec}` : inteiro;
}

export default function Contador({ texto }: { texto: string }) {
  const m = NUMERO.exec(texto);
  const el = useRef<HTMLSpanElement>(null);
  const [agora, setAgora] = useState<string | null>(null);
  // false na hidratação (o valor do servidor já está na tela), true quando o React monta no navegador
  const noNavegador = useSyncExternalStore(nada, () => true, () => false);
  const nasceuNoNavegador = useRef(noNavegador);

  // antes da pintura: quem nasce no navegador já entra no zero, sem mostrar o valor final por um quadro
  useLayoutEffect(() => {
    if (!m || !el.current) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const [, sinal, inteiro, dec = ""] = m;
    const alvo = Number(`${inteiro.replace(/\./g, "")}.${dec || "0"}`);
    if (alvo === 0) return;
    const milhar = inteiro.includes(".");
    let quadro = 0;
    const contar = () => {
      const inicio = performance.now();
      const passo = (t: number) => {
        const p = Math.min(1, Math.max(0, (t - inicio) / DURACAO)); // o 1.º quadro pode vir carimbado antes do início
        const e = 1 - (1 - p) ** 3;
        setAgora(p < 1 ? `${sinal}${escrever(alvo * e, dec.length, milhar)}` : null);
        if (p < 1) quadro = requestAnimationFrame(passo);
      };
      quadro = requestAnimationFrame(passo);
    };
    // já na tela ao nascer: conta junto com a entrada do cartão (se ninguém o viu pronto); abaixo da dobra, quando chegar
    const naTela = el.current.getBoundingClientRect().top < window.innerHeight;
    if (naTela && !nasceuNoNavegador.current) return;
    setAgora(`${sinal}${escrever(0, dec.length, milhar)}`);
    const io = new IntersectionObserver((vistos) => {
      if (vistos.some((v) => v.isIntersecting)) { io.disconnect(); contar(); }
    });
    if (naTela) contar();
    else io.observe(el.current);
    return () => { io.disconnect(); cancelAnimationFrame(quadro); };
    // conta de novo só se o número mudar
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [texto]);

  if (!m) return <>{texto}</>;
  return (
    <span ref={el} className="k-contador">
      <span aria-hidden="true">{agora ?? texto}</span>
      <span className="k-sr-only">{texto}</span>
    </span>
  );
}

"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

// Entrada pela rolagem (Movimento v2, design-system.md §7.2): os cartões nascem com a animação de entrada do
// movimento.css. Quem nasce ABAIXO da dobra tem as animações (as dele e as de dentro) pausadas no quadro zero — o
// `from` da entrada o deixa transparente — e elas só tocam quando ele chega à tela; assim o gráfico lá de baixo não
// desenha sem ninguém ver. Nada aqui mexe em atributo do DOM: o React ainda pode estar hidratando esses cartões
// (Suspense), e atributo a mais quebraria a hidratação. Sem JavaScript, tudo entra ao carregar; com "menos
// movimento", não há animação para pausar.

const ALVO = ".k-card:not([aria-hidden='true'])";

export default function Revelar() {
  const caminho = usePathname();

  useEffect(() => {
    const area = document.getElementById("conteudo");
    if (!area || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const vistos = new WeakSet<Element>();
    const esperando = new Set<Element>();

    const pausar = (el: Element) => el.getAnimations({ subtree: true }).forEach((a) => { a.pause(); a.currentTime = 0; });

    const io = new IntersectionObserver((entradas) => {
      for (const v of entradas) {
        if (!v.isIntersecting) continue;
        esperando.delete(v.target);
        io.unobserve(v.target);
        v.target.getAnimations({ subtree: true }).forEach((a) => a.play());
      }
    }, { rootMargin: "0px 0px -8% 0px" });

    const examinar = (raiz: Element) => {
      // peça nova dentro de um cartão que ainda espera (ex.: o SVG da linha, que nasce depois de medir a largura)
      for (const c of esperando) if (c.contains(raiz)) { pausar(raiz); return; }
      const cards = [...(raiz.matches(ALVO) ? [raiz] : []), ...raiz.querySelectorAll(ALVO)];
      for (const c of cards) {
        if (vistos.has(c)) continue;
        vistos.add(c);
        // um cartão dentro de outro segue o de fora
        if (c.parentElement?.closest(".k-card")) continue;
        if (c.getBoundingClientRect().top > window.innerHeight) {
          esperando.add(c);
          pausar(c);
          io.observe(c);
        }
      }
    };

    examinar(area);
    const mo = new MutationObserver((mudancas) => {
      for (const m of mudancas) m.addedNodes.forEach((n) => { if (n instanceof Element) examinar(n); });
    });
    mo.observe(area, { childList: true, subtree: true });
    return () => { mo.disconnect(); io.disconnect(); };
  }, [caminho]);

  return null;
}

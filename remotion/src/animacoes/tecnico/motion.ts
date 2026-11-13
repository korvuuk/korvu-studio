/**
 * Estilos de motion da série AI Engineer (proposta de 05/11, `00-marca/design-system/korvu-motion.md`).
 *
 * Dois temas com o MESMO vocabulário de formas, para o autor comparar:
 * - `obsidiana`: base preta, luz em degradê que respira, formas flat com degradê do laranja Korvu.
 * - `vidro` (PADRÃO, escolhido em 05/11): fundo preto com luzes laranja que passeiam, cartões de vidro translúcido
 *   com borda clara (molde da referência D5qpBbEWTxo; lá o campo é azul elétrico).
 * As cores derivam de `COR` (brand.ts) — nenhuma cor de marca nova.
 */
import type React from "react";
import { createContext, useContext } from "react";
import { Easing, spring } from "remotion";
import { COR, FONTE } from "../../brand";

const DEGRADE_LARANJA = `linear-gradient(145deg, #FF9A4D 0%, ${COR.acento} 52%, #B33A00 100%)`;

export type Tema = {
  nome: "obsidiana" | "vidro";
  /** Fonte dos títulos de etapa e da sigla. */
  fonteTitulo: string;
  pesoTitulo: number;
  cartao: string;
  cartaoBorda: string;
  /** Desfoque do que está atrás do cartão (vidro). */
  desfoque: number;
  /** Brilho de borda superior do vidro. */
  realce: string;
  texto: string;
  textoApagado: string;
  /** Folha de documento e pedaço (chunk). */
  papel: string;
  linhaPapel: string;
  /** Pedaço/ponto escolhido pela busca. */
  destaque: string;
  linhaDestaque: string;
  ponto: string;
  rotulo: string;
  rotuloAtivo: string;
  /** Linhas e ondas da busca. */
  traco: string;
  brilho: string;
  /** Forma do modelo (llm) e pílula do número da etapa. */
  forma: string;
  formaBorda: string;
  formaTexto: string;
  siglaTitulo: string;
  siglaLetra: string;
  resposta: string;
  respostaTexto: string;
  chip: string;
  chipBorda: string;
  chipTexto: string;
  cursor: string;
  erro: string;
};

export const TEMAS: Record<Tema["nome"], Tema> = {
  obsidiana: {
    nome: "obsidiana",
    fonteTitulo: FONTE.display,
    pesoTitulo: 800,
    cartao: "#131318",
    cartaoBorda: "rgba(255,255,255,0.08)",
    desfoque: 0,
    realce: "rgba(255,255,255,0.0)",
    texto: COR.texto,
    textoApagado: "#8A8A93",
    papel: "#EFEBE3",
    linhaPapel: "rgba(20,20,20,0.28)",
    destaque: DEGRADE_LARANJA,
    linhaDestaque: "rgba(255,255,255,0.75)",
    ponto: COR.nude,
    rotulo: COR.nude,
    rotuloAtivo: COR.acento,
    traco: COR.acento,
    brilho: "rgba(232,80,2,0.45)",
    forma: DEGRADE_LARANJA,
    formaBorda: "transparent",
    formaTexto: "#FFFFFF",
    siglaTitulo: `linear-gradient(100deg, #FF7A1A 0%, ${COR.acento} 40%, ${COR.nude} 100%)`,
    siglaLetra: COR.acento,
    resposta: "#EFEBE3",
    respostaTexto: "#141414",
    chip: DEGRADE_LARANJA,
    chipBorda: "transparent",
    chipTexto: "#FFFFFF",
    cursor: COR.acento,
    erro: "#FF6B5B",
  },
  vidro: {
    // 05/11 (2.ª volta): fundo PRETO com luzes laranja — "o laranja de ponta a ponta fica muito laranja".
    nome: "vidro",
    fonteTitulo: FONTE.motion,
    pesoTitulo: 600,
    cartao: "rgba(255,255,255,0.07)",
    cartaoBorda: "rgba(255,255,255,0.20)",
    desfoque: 28,
    realce: "inset 0 1.5px 0 rgba(255,255,255,0.28)",
    texto: "#FFFFFF",
    textoApagado: "rgba(255,255,255,0.62)",
    papel: "rgba(255,255,255,0.90)",
    linhaPapel: "rgba(30,20,10,0.25)",
    destaque: DEGRADE_LARANJA,
    linhaDestaque: "rgba(255,255,255,0.80)",
    ponto: "rgba(255,255,255,0.70)",
    rotulo: "rgba(255,255,255,0.78)",
    rotuloAtivo: "#FF8A3D",
    traco: "#FF7A1A",
    brilho: "rgba(232,80,2,0.55)",
    forma: "linear-gradient(145deg, rgba(255,154,77,0.92) 0%, rgba(232,80,2,0.88) 60%, rgba(179,58,0,0.9) 100%)",
    formaBorda: "rgba(255,200,160,0.55)",
    formaTexto: "#FFFFFF",
    siglaTitulo: "linear-gradient(180deg, #FFFFFF 0%, #FFFFFF 45%, #FF9A4D 100%)",
    siglaLetra: "#FF8A3D",
    resposta: "#FFFFFF",
    respostaTexto: "#1A1A1A",
    chip: "linear-gradient(145deg, rgba(255,154,77,0.9), rgba(232,80,2,0.9))",
    chipBorda: "rgba(255,200,160,0.55)",
    chipTexto: "#FFFFFF",
    cursor: "#FF7A1A",
    erro: "#FF8A75",
  },
};

export const TemaCtx = createContext<Tema>(TEMAS.obsidiana);
export const useTema = () => useContext(TemaCtx);

/** Estilo de superfície de cartão do tema (vidro ganha desfoque e realce). */
export const superficie = (t: Tema): React.CSSProperties => ({
  background: t.cartao,
  border: `1.5px solid ${t.cartaoBorda}`,
  backdropFilter: t.desfoque ? `blur(${t.desfoque}px) saturate(140%)` : undefined,
  boxShadow: t.desfoque ? `${t.realce}, 0 20px 60px rgba(90,25,0,0.25)` : undefined,
});

export const RAIO = { cartao: 36, bolha: 40, pilula: 999 } as const;

/** Mola sem quique — movimento de câmera e de cena. */
export const MOLA_SUAVE = { damping: 200, mass: 1, stiffness: 120 } as const;
/** Mola com um quique curto — elemento que "nasce" (pop). */
export const MOLA_POP = { damping: 13, mass: 0.6, stiffness: 160 } as const;

export const EASE_FLUIDO = Easing.bezier(0.65, 0, 0.35, 1);

export const progresso = (
  frame: number,
  inicio: number,
  fps: number,
  config: typeof MOLA_SUAVE | typeof MOLA_POP = MOLA_SUAVE,
  duracao?: number,
) => spring({ frame: frame - inicio, fps, config, durationInFrames: duracao });

export const mix = (a: number, b: number, p: number) => a + (b - a) * p;

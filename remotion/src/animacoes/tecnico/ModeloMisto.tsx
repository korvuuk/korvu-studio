/**
 * MODELO MISTO da série AI Engineer (05/11): animação + VÍDEO EXTRA + IMAGEM na mesma cena.
 * Pedido do autor: "não ficar só animações… usar animação e interagir animação com vídeos extra e imagens".
 * Não é episódio — é o teste dos padrões de mistura (`00-marca/design-system/korvu-motion.md` §6), contado com as
 * três camadas do #01 (usar → treinar → construir). Sem narração: a fala entra quando o episódio for gravado.
 *
 * Padrões mostrados, na ordem:
 *  A. vídeo extra em cartão de vidro SOBRE o autor, abaixo do queixo;
 *  B. o cartão CRESCE e vira o palco (a mídia é a transição, sem corte);
 *  C. anotação por cima do vídeo (etiquetas presas ao que acontece na tela dele);
 *  D. fotos em leque com Ken Burns → a foto do meio VIRA vídeo;
 *  E. dado animado por cima do vídeo (barra e número que conta);
 *  F. o vídeo encolhe e VIRA peça do diagrama (nó "modelo" com o vídeo tocando dentro);
 *  G. as mídias viram miniaturas vivas dentro do resumo final.
 * Um elemento de mídia é o MESMO de ponta a ponta (a janela do data center é foto → janela → nó → miniatura).
 */
import { Video } from "@remotion/media";
import { Audio } from "@remotion/media";
import React from "react";
import { fitText } from "@remotion/layout-utils";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { FONTE, useFontesProntas } from "../../brand";
import { EASE_FLUIDO, MOLA_POP, MOLA_SUAVE, TEMAS, TemaCtx, mix, progresso } from "./motion";
import { FundoVidro, vidroSobreVideo } from "./ModeloRAG";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const PASTA = "_demo/ai-engineer/misto";

// ---------------------------------------------------------------------------
// Linha do tempo (frames a 25 fps)
// ---------------------------------------------------------------------------
const T = {
  selo: 6,
  cartao: 40, // A: vídeo do ChatGPT nasce abaixo do queixo
  expande: 84, // B: o cartão vira o palco
  s1: 120, // camada 1: usar
  s2: 330, // camada 3: treinar (fotos)
  vira: 440, // D: foto do meio vira vídeo
  conta: 495, // E: barra "treinando"
  s3: 600, // camada 2: construir (F)
  s4: 840, // G: as três camadas
  fecha: 945,
  fim: 1075,
} as const;

export const MODELO_MISTO_DURACAO = T.fim;

/** A bola abre a partir do centro do cartão (sob o queixo) e fecha no mesmo ponto. */
const CENTRO_TRANSICAO = { x: 540, y: 1105 };
const RAIO_MAX = 1500;
/** Curva da bola: começa e termina devagar (nada de "seco"). */
const EASE_BOLA = Easing.bezier(0.65, 0, 0.35, 1);
const DUR_ABRE = 30;
const DUR_FECHA = 34;

type Caixa = { x: number; y: number; w: number; h: number; r: number };
const lerpCaixa = (a: Caixa, b: Caixa, p: number): Caixa => ({
  x: mix(a.x, b.x, p),
  y: mix(a.y, b.y, p),
  w: mix(a.w, b.w, p),
  h: mix(a.h, b.h, p),
  r: mix(a.r, b.r, p),
});

/** Faixa abaixo do queixo (rosto deste corte vai até y 909 — korvu-motion §4). */
const CARTAO_USAR: Caixa = { x: 282, y: 960, w: 516, h: 290, r: 30 };
const JANELA: Caixa = { x: 70, y: 570, w: 940, h: 530, r: 40 };
const NO_APP: Caixa = { x: 80, y: 640, w: 300, h: 300, r: 70 };
const NO_MODELO: Caixa = { x: 700, y: 640, w: 300, h: 300, r: 70 };
const BARRA_Y = [560, 750, 940];
const BARRA = { x: 70, w: 940, h: 160, r: 44 };
const MINI = (i: number): Caixa => ({ x: BARRA.x + 18, y: BARRA_Y[i] + 18, w: 220, h: 124, r: 28 });
const ICONE_BARRA2: Caixa = { x: BARRA.x + 66, y: BARRA_Y[1] + 18, w: 124, h: 124, r: 34 };

const FOTOS: Array<{ arquivo: string; caixa: Caixa; rot: number; de: number }> = [
  { arquivo: "placa.jpg", caixa: { x: 50, y: 720, w: 430, h: 300, r: 30 }, rot: -8, de: T.s2 + 16 },
  { arquivo: "chip.jpg", caixa: { x: 600, y: 760, w: 430, h: 300, r: 30 }, rot: 7, de: T.s2 + 22 },
  { arquivo: "computador.jpg", caixa: { x: 270, y: 580, w: 540, h: 406, r: 34 }, rot: -1.5, de: T.s2 + 28 },
];

// ---------------------------------------------------------------------------
// Som — cada efeito no frame do movimento
// ---------------------------------------------------------------------------
const SONS: Array<[number, string, number]> = [
  [T.selo, "pop", 0.45],
  [T.cartao - 4, "swipe", 0.4],
  [T.cartao + 4, "pop", 0.5],
  [T.expande - 4, "whoosh-entra", 0.85],
  [T.s1 + 6, "pop", 0.55],
  [T.s1 + 30, "digitar", 0.3],
  [165, "pop", 0.5],
  [205, "pop", 0.5],
  [240, "pop", 0.4],
  [246, "pop", 0.4],
  [252, "pop", 0.4],
  [T.s2 - 2, "whoosh-sai", 0.5],
  [T.s2 + 6, "pop", 0.55],
  [T.s2 + 14, "swipe", 0.35],
  [T.s2 + 20, "swipe", 0.35],
  [T.s2 + 26, "swipe", 0.4],
  [T.vira - 26, "riser", 0.4],
  [T.vira + 2, "whoosh-entra", 0.65],
  [T.vira + 30, "pop", 0.45],
  [T.vira + 36, "pop", 0.45],
  [T.vira + 42, "pop", 0.45],
  ...Array.from({ length: 8 }, (_, k) => [T.conta + 6 + k * 9, "tick", 0.32] as [number, string, number]),
  [T.conta + 80, "brilho", 0.6],
  [T.s3 - 2, "swipe", 0.5],
  [T.s3 + 6, "pop", 0.55],
  [T.s3 + 40, "pop", 0.5],
  [T.s3 + 55, "pop", 0.5],
  [T.s3 + 65, "conectar", 0.55],
  [T.s3 + 90, "conectar", 0.55],
  [T.s3 + 120, "swipe", 0.45],
  [T.s3 + 160, "swipe", 0.4],
  [T.s3 + 198, "pop", 0.55],
  [T.s3 + 205, "brilho", 0.65],
  [T.s4 - 2, "whoosh-entra", 0.55],
  [T.s4 + 8, "pop", 0.4],
  [T.s4 + 14, "pop", 0.4],
  [T.s4 + 20, "pop", 0.4],
  [T.s4 + 46, "brilho", 0.6],
  [T.fecha - 6, "whoosh-sai", 0.9],
  [T.fecha + 44, "swipe", 0.45],
  [T.fecha + 54, "pop", 0.45],
  [T.fecha + 60, "pop", 0.45],
  [T.fecha + 66, "pop", 0.45],
];

// ---------------------------------------------------------------------------
// Composição
// ---------------------------------------------------------------------------
export const ModeloMisto: React.FC = () => {
  const prontas = useFontesProntas();
  const frame = useCurrentFrame();
  if (!prontas) return null;

  // Transição BOLA (referência D5qpBbEWTxo, 16:13): borda macia, anel branco desfocado com halo laranja e vermelho,
  // e tudo o que está atrás sai de foco enquanto a bola anda. Abre no centro do cartão; na volta fecha, e antes de
  // virar um ponto se DISSOLVE (brilho que abre e some) — nunca encolhe seco até o peito.
  const abre = interpolate(frame, [T.expande - 2, T.expande - 2 + DUR_ABRE], [0, 1], { ...clamp, easing: EASE_BOLA });
  const fecha = interpolate(frame, [T.fecha, T.fecha + DUR_FECHA], [0, 1], { ...clamp, easing: EASE_BOLA });
  const palcoVisivel = frame >= T.expande - 2 && frame < T.fecha + DUR_FECHA;
  const naVolta = frame >= T.fecha;
  const raio = naVolta ? mix(RAIO_MAX, 0, fecha) : mix(0, RAIO_MAX, abre);
  // some entre r 560 e 260: a bola vira luz em vez de fechar até o fim
  const dissolve = naVolta ? interpolate(raio, [260, 560], [1, 0], clamp) : 0;
  // o autor: foco e zoom acompanham a bola (sai de foco quando ela cobre, volta nítido quando ela some)
  const cobre = naVolta ? 1 - fecha : abre;
  const zoomApresentador = mix(1, 1.12, cobre);
  const focoApresentador = 18 * cobre;
  const pena = mix(40, 140, Math.min(1, raio / 900));
  const mascara = `radial-gradient(circle at ${CENTRO_TRANSICAO.x}px ${CENTRO_TRANSICAO.y}px, #000 ${Math.max(0, raio - pena)}px, transparent ${raio}px)`;
  const emTransicao = (frame >= T.expande - 2 && abre < 1) || (naVolta && fecha < 1);
  // o palco também anda: na volta afunda e sai de foco junto com a bola
  const palcoEscala = naVolta ? mix(1, 1.06, fecha) : mix(1.1, 1, abre);
  const palcoFoco = naVolta ? 10 * fecha : 10 * (1 - abre);

  return (
    <TemaCtx.Provider value={TEMAS.vidro}>
      <AbsoluteFill style={{ backgroundColor: "#000" }}>
        <Sequence durationInFrames={T.expande + DUR_ABRE + 4}>
          <Apresentador zoom={zoomApresentador} foco={focoApresentador} inicio={0} />
        </Sequence>
        <Sequence from={T.fecha - 4}>
          <Apresentador zoom={zoomApresentador} foco={focoApresentador} inicio={160} />
        </Sequence>
        <SeloSerie />

        {palcoVisivel ? (
          <AbsoluteFill
            style={{
              maskImage: abre >= 1 && !naVolta ? undefined : mascara,
              WebkitMaskImage: abre >= 1 && !naVolta ? undefined : mascara,
              opacity: 1 - dissolve,
            }}
          >
            <AbsoluteFill
              style={{
                scale: String(palcoEscala),
                transformOrigin: `${CENTRO_TRANSICAO.x}px ${CENTRO_TRANSICAO.y}px`,
                filter: palcoFoco > 0.2 ? `blur(${palcoFoco}px)` : undefined,
              }}
            >
              <Palco />
            </AbsoluteFill>
          </AbsoluteFill>
        ) : null}
        {emTransicao && raio > 20 ? <AnelBola raio={raio} dissolve={dissolve} /> : null}

        {/* A + B + C: a janela do ChatGPT fica por cima de tudo, do cartão sobre o autor até sair na camada 3. */}
        <JanelaUsar />
        <ResumoFinal />

        {SONS.map(([f, nome, vol], i) => (
          <Sequence key={i} from={f} durationInFrames={90}>
            <Audio src={staticFile(`_marca/sfx/${nome}.mp3`)} volume={vol} />
          </Sequence>
        ))}
      </AbsoluteFill>
    </TemaCtx.Provider>
  );
};

const Apresentador: React.FC<{ zoom: number; foco: number; inicio: number }> = ({ zoom, foco, inicio }) => (
  <AbsoluteFill
    style={{ scale: String(zoom), transformOrigin: "50% 45%", filter: foco > 0.2 ? `blur(${foco}px)` : undefined }}
  >
    <Video
      src={staticFile("_demo/ai-engineer/apresentador.mp4")}
      trimBefore={inicio}
      muted
      objectFit="cover"
      style={{ width: "100%", height: "100%" }}
    />
  </AbsoluteFill>
);

/** Vídeo extra que toca dentro de uma caixa (sempre mudo, em loop se acabar). */
const Midia: React.FC<{ arquivo: string; de: number; corte?: number }> = ({ arquivo, de, corte = 0 }) => (
  <Sequence from={de} layout="none">
    <Video
      src={staticFile(`${PASTA}/${arquivo}`)}
      trimBefore={corte}
      muted
      loop
      objectFit="cover"
      style={{ width: "100%", height: "100%" }}
    />
  </Sequence>
);

/** Moldura de vidro (janela): borda clara, desfoque, barra de cima com 3 pontos que aparece com `barra`. */
const Moldura: React.FC<{
  c: Caixa;
  barra: number;
  estilo?: React.CSSProperties;
  children: React.ReactNode;
  sobre?: React.ReactNode;
}> = ({ c, barra, estilo, children, sobre }) => {
  const pad = mix(8, 14, barra);
  return (
    <div
      style={{
        position: "absolute",
        left: c.x,
        top: c.y,
        width: c.w,
        height: c.h,
        borderRadius: c.r,
        padding: pad,
        paddingTop: pad + 40 * barra,
        background: "rgba(255,255,255,0.09)",
        border: "1.5px solid rgba(255,255,255,0.28)",
        backdropFilter: "blur(24px) saturate(150%)",
        boxShadow: "inset 0 1.5px 0 rgba(255,255,255,0.45), 0 30px 80px rgba(0,0,0,0.55)",
        boxSizing: "border-box",
        ...estilo,
      }}
    >
      {barra > 0.05 ? (
        <div style={{ position: "absolute", top: pad + 4, left: pad + 10, display: "flex", gap: 10, opacity: barra }}>
          {[0, 1, 2].map((i) => (
            <span key={i} style={{ width: 16, height: 16, borderRadius: 99, background: "rgba(255,255,255,0.45)" }} />
          ))}
        </div>
      ) : null}
      <div
        style={{
          position: "relative",
          width: "100%",
          height: "100%",
          borderRadius: Math.max(8, c.r - pad),
          overflow: "hidden",
          background: "#111",
        }}
      >
        {children}
        {sobre}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Sobre o autor — abaixo do queixo
// ---------------------------------------------------------------------------
const SeloSerie: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame > T.cartao + 10 && frame < T.fecha + 10) return null;
  const volta = frame > T.fecha;
  const entra = progresso(frame, volta ? T.fecha + 14 : T.selo, fps, MOLA_POP);
  const sai = volta ? 0 : interpolate(frame, [T.cartao - 6, T.cartao + 4], [0, 1], { ...clamp, easing: EASE_FLUIDO });
  return (
    <div
      style={{
        position: "absolute",
        top: 960,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        opacity: entra * (1 - sai),
        translate: `0 ${mix(24, 0, entra) - 30 * sai}px`,
      }}
    >
      {/* Título da série em CAIXA ALTA grande, sem pílula de vidro (Autor, 05/11: a pílula sumia sobre o vídeo). */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
        <span
          style={{
            padding: "6px 20px",
            borderRadius: 99,
            fontFamily: FONTE.motion,
            fontWeight: 600,
            fontSize: 30,
            letterSpacing: "0.04em",
            color: "#fff",
            background: "linear-gradient(145deg, #FF9A4D, #E85002)",
            boxShadow: "0 6px 24px rgba(232,80,2,0.55)",
          }}
        >
          #01
        </span>
        <div
          style={{
            display: "flex",
            fontFamily: FONTE.motion,
            fontWeight: 600,
            fontSize: 124,
            lineHeight: 1,
            letterSpacing: "-0.035em",
            color: "#fff",
            whiteSpace: "pre",
            textShadow: "0 4px 30px rgba(0,0,0,0.55), 0 1px 3px rgba(0,0,0,0.4)",
          }}
        >
          {Array.from("AI ENGINEER").map((l, i) => {
            const p = volta ? entra : progresso(frame, T.selo + 3 + i * 1.4, fps, MOLA_SUAVE, 18);
            return (
              <span
                key={i}
                style={{
                  display: "inline-block",
                  opacity: Math.min(1, p * 1.3),
                  translate: `0 ${mix(50, 0, p)}px`,
                  filter: p < 0.98 ? `blur(${mix(14, 0, p)}px)` : undefined,
                }}
              >
                {l}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
};

/** A–C: vídeo do ChatGPT. Nasce como cartão sob o queixo, cresce até a janela do palco, ganha etiquetas e sai. */
const JanelaUsar: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < T.cartao - 2 || frame > T.s2 + 20) return null;
  const nasce = progresso(frame, T.cartao, fps, MOLA_POP);
  const cresce = progresso(frame, T.expande, fps, MOLA_SUAVE, 30);
  const sai = interpolate(frame, [T.s2 - 4, T.s2 + 14], [0, 1], { ...clamp, easing: EASE_FLUIDO });
  const c = lerpCaixa(CARTAO_USAR, JANELA, cresce);
  return (
    <Moldura
      c={c}
      barra={cresce}
      estilo={{
        opacity: Math.min(1, nasce * 1.4) * (1 - sai),
        scale: String(mix(0.86, 1, nasce) * mix(1, 0.8, sai)),
        translate: `${-640 * sai}px ${mix(30, 0, nasce)}px`,
        filter: `blur(${10 * sai}px)`,
      }}
      sobre={
        <>
          <Etiqueta de={165} ate={T.s2} x={0.62} y={0.24} texto="você pergunta" />
          <Contorno de={196} ate={T.s2} x={0.08} y={0.42} w={0.86} h={0.24} />
          <Etiqueta de={205} ate={T.s2} x={0.5} y={0.74} texto="a ia responde" quente />
        </>
      }
    >
      <Midia arquivo="chatgpt-conversa.mp4" de={T.cartao - 2} />
    </Moldura>
  );
};

/** C: etiqueta presa a um ponto do vídeo (coordenadas em fração da caixa do vídeo). */
const Etiqueta: React.FC<{ de: number; ate: number; x: number; y: number; texto: string; quente?: boolean }> = ({
  de,
  ate,
  x,
  y,
  texto,
  quente,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < de) return null;
  const e = progresso(frame, de, fps, MOLA_POP);
  const sai = interpolate(frame, [ate - 8, ate], [0, 1], clamp);
  const flutua = 4 * Math.sin((frame - de) / 14);
  return (
    <div
      style={{
        position: "absolute",
        left: `${x * 100}%`,
        top: `${y * 100}%`,
        translate: `-50% ${-50 + flutua}%`,
        scale: String(e),
        opacity: Math.min(1, e * 1.5) * (1 - sai),
        padding: "10px 24px",
        borderRadius: 99,
        fontFamily: FONTE.motion,
        fontWeight: 600,
        fontSize: 36,
        whiteSpace: "nowrap",
        color: "#fff",
        background: quente
          ? "linear-gradient(145deg, rgba(255,154,77,0.95), rgba(232,80,2,0.95))"
          : "rgba(20,20,24,0.72)",
        border: quente ? "1.5px solid rgba(255,200,160,0.7)" : "1.5px solid rgba(255,255,255,0.3)",
        backdropFilter: "blur(14px)",
        boxShadow: quente ? "0 10px 40px rgba(232,80,2,0.55)" : "0 10px 30px rgba(0,0,0,0.35)",
      }}
    >
      {texto}
    </div>
  );
};

/** C: contorno laranja que se desenha em volta de uma área do vídeo. */
const Contorno: React.FC<{ de: number; ate: number; x: number; y: number; w: number; h: number }> = ({
  de,
  ate,
  x,
  y,
  w,
  h,
}) => {
  const frame = useCurrentFrame();
  if (frame < de) return null;
  const desenha = interpolate(frame, [de, de + 18], [0, 1], { ...clamp, easing: EASE_FLUIDO });
  const sai = interpolate(frame, [ate - 8, ate], [0, 1], clamp);
  return (
    <svg
      style={{ position: "absolute", left: `${x * 100}%`, top: `${y * 100}%`, width: `${w * 100}%`, height: `${h * 100}%`, overflow: "visible", opacity: 1 - sai }}
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
    >
      <rect
        x={0}
        y={0}
        width={100}
        height={100}
        rx={6}
        fill="rgba(255,122,26,0.08)"
        stroke="#FF7A1A"
        strokeWidth={4}
        vectorEffect="non-scaling-stroke"
        pathLength={1}
        strokeDasharray={1}
        strokeDashoffset={1 - desenha}
        style={{ filter: "drop-shadow(0 0 10px rgba(255,122,26,0.8))" }}
      />
    </svg>
  );
};

/**
 * Anel da bola: núcleo branco desfocado + halo laranja + halo vermelho por fora (como na referência).
 * Ao dissolver, o anel engrossa, desfoca e some — vira luz.
 */
const AnelBola: React.FC<{ raio: number; dissolve: number }> = ({ raio, dissolve }) => {
  const camadas: Array<{ cor: string; esp: number; foco: number; desloca: number; alfa: number }> = [
    { cor: "rgba(200,30,20,1)", esp: 90, foco: 40, desloca: 34, alfa: 0.55 },
    { cor: "rgba(255,110,26,1)", esp: 46, foco: 18, desloca: 6, alfa: 0.9 },
    { cor: "rgba(255,246,236,1)", esp: 22, foco: 8, desloca: -10, alfa: 0.95 },
  ];
  const abre = 1 + 0.6 * dissolve;
  return (
    <>
      {camadas.map((c, i) => {
        const esp = c.esp * abre;
        const r = raio + c.desloca + esp / 2;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: CENTRO_TRANSICAO.x - r,
              top: CENTRO_TRANSICAO.y - r,
              width: r * 2,
              height: r * 2,
              borderRadius: "50%",
              border: `${esp}px solid ${c.cor}`,
              boxSizing: "border-box",
              filter: `blur(${c.foco * (1 + 1.5 * dissolve)}px)`,
              opacity: c.alfa * (1 - dissolve),
              mixBlendMode: "screen",
            }}
          />
        );
      })}
    </>
  );
};

/**
 * Texto GRANDE (Autor, 05/11: "fontes grandes em algum momento… experiência profissional"), como o
 * "Two Options" da referência: palavra que ocupa a largura, branco que esmaece para baixo, letras entrando uma a
 * uma (sobe + foco), atrás do conteúdo. Pílula com o número da etapa em cima.
 */
const TituloGigante: React.FC<{ de: number; ate: number; texto: string; numero?: number; rotulo?: string }> = ({
  de,
  ate,
  texto,
  numero,
  rotulo,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < de - 2 || frame > ate + 16) return null;
  const { fontSize } = fitText({
    text: texto,
    withinWidth: 960,
    fontFamily: FONTE.motion,
    fontWeight: 600,
    letterSpacing: "-0.05em",
  });
  const tam = Math.min(260, fontSize);
  const sai = interpolate(frame, [ate, ate + 14], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  const pPilula = progresso(frame, de, fps, MOLA_SUAVE, 16);
  const letras = Array.from(texto);
  return (
    <div
      style={{
        position: "absolute",
        top: 236,
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        opacity: 1 - sai,
        translate: `0 ${-50 * sai}px`,
        filter: sai > 0.01 ? `blur(${14 * sai}px)` : undefined,
      }}
    >
      {numero || rotulo ? (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            padding: "8px 24px 8px 8px",
            borderRadius: 99,
            background: "rgba(255,255,255,0.08)",
            border: "1.5px solid rgba(255,255,255,0.22)",
            backdropFilter: "blur(18px)",
            fontFamily: FONTE.motion,
            fontWeight: 500,
            fontSize: 36,
            letterSpacing: "-0.01em",
            color: "rgba(255,255,255,0.85)",
            opacity: pPilula,
            translate: `0 ${mix(20, 0, pPilula)}px`,
            filter: `blur(${mix(8, 0, pPilula)}px)`,
          }}
        >
          {numero ? (
            <span
              style={{
                width: 52,
                height: 52,
                borderRadius: 99,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 600,
                fontSize: 26,
                color: "#fff",
                background: "linear-gradient(145deg, #FF9A4D, #E85002)",
                boxShadow: "0 6px 24px rgba(232,80,2,0.55)",
              }}
            >
              {String(numero).padStart(2, "0")}
            </span>
          ) : null}
          {rotulo}
        </div>
      ) : null}
      <div
        style={{
          marginTop: 6,
          display: "flex",
          fontFamily: FONTE.motion,
          fontWeight: 600,
          fontSize: tam,
          lineHeight: 1,
          letterSpacing: "-0.05em",
          whiteSpace: "pre",
        }}
      >
        {letras.map((l, i) => {
          const p = progresso(frame, de + 4 + i * 1.6, fps, MOLA_SUAVE, 20);
          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                paddingBottom: "0.12em",
                backgroundImage: "linear-gradient(180deg, #FFFFFF 38%, rgba(255,214,186,0.55) 78%, rgba(255,255,255,0.08) 100%)",
                WebkitBackgroundClip: "text",
                backgroundClip: "text",
                color: "transparent",
                opacity: Math.min(1, p * 1.3),
                translate: `0 ${mix(0.45 * tam, 0, p)}px`,
                filter: p < 0.98 ? `blur(${mix(16, 0, p)}px)` : undefined,
              }}
            >
              {l}
            </span>
          );
        })}
      </div>
    </div>
  );
};

/** Volta do autor: barra de vidro com as três camadas, a do meio acesa. */
const ResumoFinal: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const inicio = T.fecha + 44;
  if (frame < inicio) return null;
  const e = progresso(frame, inicio, fps, MOLA_SUAVE, 20);
  const itens = ["usar", "construir", "treinar"];
  return (
    <div
      style={{
        ...vidroSobreVideo,
        position: "absolute",
        left: 70,
        right: 70,
        top: 1200,
        height: 130,
        padding: "0 18px",
        borderRadius: 40,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        opacity: e,
        translate: `0 ${mix(40, 0, e)}px`,
        filter: `blur(${mix(12, 0, e)}px)`,
        fontFamily: FONTE.motion,
        color: "#fff",
      }}
    >
      {itens.map((txt, i) => {
        const p = progresso(frame, inicio + 10 + i * 6, fps, MOLA_POP);
        const meio = i === 1;
        return (
          <div
            key={txt}
            style={{
              padding: "14px 28px",
              borderRadius: 99,
              fontSize: 40,
              fontWeight: 600,
              opacity: Math.min(1, p * 1.4),
              scale: String(mix(0.7, 1, p)),
              background: meio ? "linear-gradient(145deg, rgba(255,154,77,0.95), rgba(232,80,2,0.95))" : "transparent",
              boxShadow: meio ? "0 10px 40px rgba(232,80,2,0.55)" : undefined,
            }}
          >
            {txt}
          </div>
        );
      })}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Palco
// ---------------------------------------------------------------------------
const Palco: React.FC = () => {
  const frame = useCurrentFrame();
  const respira = 1 + 0.01 * Math.sin(frame / 38);
  const deriva = 5 * Math.sin(frame / 52);
  return (
    <AbsoluteFill>
      <FundoVidro />
      <AbsoluteFill style={{ scale: String(respira), translate: `0 ${deriva}px` }}>
        <TituloGigante de={T.s1 + 4} ate={T.s2 - 6} numero={1} rotulo="a ia pronta" texto="usar" />
        <TituloGigante de={T.s2 + 4} ate={T.s3 - 6} numero={3} rotulo="o modelo" texto="treinar" />
        <TituloGigante de={T.s3 + 4} ate={T.s4 - 6} numero={2} rotulo="com ia" texto="construir" />
        <TituloGigante de={T.s4 + 4} ate={T.fecha + 30} rotulo="onde cada um trabalha" texto="3 camadas" />

        <Chip x={300} y={1150} de={240} ate={T.s2 - 4} texto="chatgpt" />
        <Chip x={540} y={1150} de={246} ate={T.s2 - 4} texto="claude" />
        <Chip x={780} y={1150} de={252} ate={T.s2 - 4} texto="gemini" />

        <Fotos />
        <Chip x={260} y={1150} de={T.vira + 30} ate={T.s3 - 4} texto="dados" />
        <Chip x={540} y={1150} de={T.vira + 36} ate={T.s3 - 4} texto="gpus" />
        <Chip x={820} y={1150} de={T.vira + 42} ate={T.s3 - 4} texto="meses" />

        {/* as barras ficam ATRÁS: o ícone do app e a miniatura do data center pousam dentro delas */}
        <Camadas />
        <Construir />
        <JanelaTreino />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Chip: React.FC<{ x: number; y: number; de: number; ate: number; texto: string; quente?: boolean }> = ({
  x,
  y,
  de,
  ate,
  texto,
  quente,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < de || frame > ate + 12) return null;
  const e = progresso(frame, de, fps, MOLA_POP);
  const sai = interpolate(frame, [ate, ate + 10], [0, 1], { ...clamp, easing: EASE_FLUIDO });
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        translate: `-50% ${mix(30, 0, e) - 20 * sai}px`,
        opacity: Math.min(1, e * 1.5) * (1 - sai),
        scale: String(mix(0.7, 1, e)),
        padding: "16px 34px",
        borderRadius: 99,
        fontFamily: FONTE.motion,
        fontWeight: 600,
        fontSize: 40,
        color: "#fff",
        whiteSpace: "nowrap",
        background: quente
          ? "linear-gradient(145deg, rgba(255,154,77,0.95), rgba(232,80,2,0.95))"
          : "rgba(255,255,255,0.08)",
        border: quente ? "1.5px solid rgba(255,200,160,0.7)" : "1.5px solid rgba(255,255,255,0.24)",
        backdropFilter: "blur(20px)",
        boxShadow: quente ? "0 12px 44px rgba(232,80,2,0.6)" : "inset 0 1.5px 0 rgba(255,255,255,0.3)",
      }}
    >
      {texto}
    </div>
  );
};

/** D: três fotos em leque com Ken Burns. A do meio (computador) é substituída pela janela do data center. */
const Fotos: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < T.s2 || frame > T.vira + 30) return null;
  const abreLados = interpolate(frame, [T.vira - 2, T.vira + 14], [0, 1], {
    ...clamp,
    easing: EASE_FLUIDO,
  });
  return (
    <>
      {FOTOS.map((f, i) => {
        const e = progresso(frame, f.de, fps, MOLA_SUAVE, 24);
        const meio = i === 2;
        if (meio && frame >= T.vira) return null; // a janela do data center assume daqui
        const lado = i === 0 ? -1 : 1;
        const kb = 1.04 + 0.1 * interpolate(frame, [f.de, T.vira + 20], [0, 1], clamp);
        const flutua = 5 * Math.sin((frame + i * 17) / 20);
        return (
          <div
            key={f.arquivo}
            style={{
              position: "absolute",
              left: f.caixa.x + (meio ? 0 : lado * 620 * abreLados),
              top: f.caixa.y + mix(700, 0, e) + flutua,
              width: f.caixa.w,
              height: f.caixa.h,
              rotate: `${mix(f.rot * 2.2, f.rot, e)}deg`,
              opacity: Math.min(1, e * 1.4) * (1 - (meio ? 0 : abreLados)),
              filter: `blur(${meio ? 0 : 10 * abreLados}px)`,
              borderRadius: f.caixa.r,
              padding: 12,
              boxSizing: "border-box",
              background: "rgba(255,255,255,0.10)",
              border: "1.5px solid rgba(255,255,255,0.3)",
              backdropFilter: "blur(20px)",
              boxShadow: "inset 0 1.5px 0 rgba(255,255,255,0.45), 0 30px 70px rgba(0,0,0,0.6)",
            }}
          >
            <div style={{ width: "100%", height: "100%", borderRadius: f.caixa.r - 12, overflow: "hidden" }}>
              <Img
                src={staticFile(`${PASTA}/${f.arquivo}`)}
                style={{ width: "100%", height: "100%", objectFit: "cover", scale: String(kb) }}
              />
            </div>
          </div>
        );
      })}
    </>
  );
};

/**
 * D → E → F → G: UM elemento só. Começa exatamente no lugar da foto do meio, vira a janela do data center
 * (com a barra "treinando"), encolhe até o nó "modelo" e termina como miniatura da camada 3.
 */
const JanelaTreino: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < T.vira || frame > T.fecha + 24) return null;
  const fotoMeio = FOTOS[2].caixa;
  const p1 = progresso(frame, T.vira, fps, MOLA_SUAVE, 28);
  const p2 = progresso(frame, T.s3, fps, MOLA_SUAVE, 30);
  const p3 = progresso(frame, T.s4, fps, MOLA_SUAVE, 30);
  let c = lerpCaixa({ ...fotoMeio }, JANELA, p1);
  c = lerpCaixa(c, NO_MODELO, p2);
  c = lerpCaixa(c, MINI(2), p3);
  const rot = mix(FOTOS[2].rot, 0, p1);
  // a foto do computador se dissolve no vídeo nos primeiros frames
  const foto = interpolate(frame, [T.vira, T.vira + 16], [1, 0], clamp);
  return (
    <>
      <Moldura c={c} barra={p1 * (1 - p2)} estilo={{ rotate: `${rot}deg` }} sobre={<BarraTreinando />}>
        <Midia arquivo="datacenter.mp4" de={T.vira - 10} />
        {foto > 0 ? (
          <Img
            src={staticFile(`${PASTA}/computador.jpg`)}
            style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", opacity: foto, scale: "1.14" }}
          />
        ) : null}
      </Moldura>
      <Rotulo x={NO_MODELO.x + NO_MODELO.w / 2} y={NO_MODELO.y + NO_MODELO.h + 24} de={T.s3 + 30} ate={T.s4} texto="modelo" />
    </>
  );
};

/** E: dado animado por cima do vídeo — barra de vidro com número que conta. */
const BarraTreinando: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < T.conta || frame > T.s3 + 10) return null;
  const e = progresso(frame, T.conta, fps, MOLA_SUAVE, 16);
  const enche = interpolate(frame, [T.conta + 6, T.conta + 78], [0, 1], { ...clamp, easing: EASE_FLUIDO });
  const sai = interpolate(frame, [T.s3 - 8, T.s3 + 4], [0, 1], clamp);
  const pronto = frame >= T.conta + 80;
  return (
    <div
      style={{
        position: "absolute",
        left: 22,
        right: 22,
        bottom: 22,
        padding: "18px 26px",
        borderRadius: 26,
        background: "rgba(10,10,12,0.55)",
        border: "1.5px solid rgba(255,255,255,0.28)",
        backdropFilter: "blur(18px)",
        opacity: e * (1 - sai),
        translate: `0 ${mix(30, 0, e)}px`,
        fontFamily: FONTE.motion,
        color: "#fff",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 38, fontWeight: 600 }}>
        <span>{pronto ? "modelo pronto" : "treinando"}</span>
        <span style={{ fontVariantNumeric: "tabular-nums", color: "#FF9A4D" }}>{Math.round(enche * 100)}%</span>
      </div>
      <div style={{ marginTop: 14, height: 14, borderRadius: 99, background: "rgba(255,255,255,0.16)", overflow: "hidden" }}>
        <div
          style={{
            width: `${enche * 100}%`,
            height: "100%",
            borderRadius: 99,
            background: "linear-gradient(90deg, #FF9A4D, #E85002)",
            boxShadow: "0 0 20px rgba(255,122,26,0.9)",
          }}
        />
      </div>
    </div>
  );
};

const Rotulo: React.FC<{ x: number; y: number; de: number; ate: number; texto: string }> = ({ x, y, de, ate, texto }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < de || frame > ate + 10) return null;
  const e = progresso(frame, de, fps, MOLA_SUAVE, 14);
  const sai = interpolate(frame, [ate - 4, ate + 6], [0, 1], clamp);
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        translate: `-50% ${mix(16, 0, e)}px`,
        opacity: e * (1 - sai),
        fontFamily: FONTE.motion,
        fontWeight: 600,
        fontSize: 38,
        color: "rgba(255,255,255,0.85)",
        whiteSpace: "nowrap",
      }}
    >
      {texto}
    </div>
  );
};

// ---------------------------------------------------------------------------
// F — construir: app → api → modelo (o nó do modelo é o vídeo do data center)
// ---------------------------------------------------------------------------
const LINHA_Y = NO_APP.y + NO_APP.h / 2;
const API = { x: 440, w: 200, h: 84 };

const Construir: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < T.s3 + 30 || frame > T.fecha + 24) return null;
  const app = progresso(frame, T.s3 + 40, fps, MOLA_POP);
  const api = progresso(frame, T.s3 + 55, fps, MOLA_POP);
  const l1 = interpolate(frame, [T.s3 + 65, T.s3 + 85], [0, 1], { ...clamp, easing: EASE_FLUIDO });
  const l2 = interpolate(frame, [T.s3 + 90, T.s3 + 110], [0, 1], { ...clamp, easing: EASE_FLUIDO });
  const ida = interpolate(frame, [T.s3 + 120, T.s3 + 152], [0, 1], { ...clamp, easing: EASE_FLUIDO });
  const volta = interpolate(frame, [T.s3 + 160, T.s3 + 194], [0, 1], { ...clamp, easing: EASE_FLUIDO });
  const resposta = progresso(frame, T.s3 + 198, fps, MOLA_POP);
  const vaiCamadas = progresso(frame, T.s4, fps, MOLA_SUAVE, 30);
  const some = interpolate(frame, [T.s4 - 4, T.s4 + 10], [0, 1], clamp);
  const xA = NO_APP.x + NO_APP.w;
  const xM = NO_MODELO.x;
  const cApp = lerpCaixa(NO_APP, ICONE_BARRA2, vaiCamadas);
  const ponto = (p: number, dir: 1 | -1) => {
    const x = dir === 1 ? mix(xA, xM, p) : mix(xM, xA, p);
    const arco = -46 * Math.sin(Math.PI * p);
    return { x, y: LINHA_Y + arco };
  };
  const pIda = ponto(ida, 1);
  const pVolta = ponto(volta, -1);
  return (
    <>
      {/* linhas */}
      <div style={{ opacity: 1 - some }}>
        <div style={{ position: "absolute", left: xA, top: LINHA_Y - 3, width: (API.x - xA) * l1, height: 6, borderRadius: 3, background: "linear-gradient(90deg, rgba(255,255,255,0.3), #FF7A1A)" }} />
        <div style={{ position: "absolute", left: API.x + API.w, top: LINHA_Y - 3, width: (xM - API.x - API.w) * l2, height: 6, borderRadius: 3, background: "linear-gradient(90deg, #FF7A1A, rgba(255,255,255,0.3))" }} />
        <div
          style={{
            position: "absolute",
            left: API.x,
            top: LINHA_Y - API.h / 2,
            width: API.w,
            height: API.h,
            borderRadius: 99,
            scale: String(api),
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: FONTE.motion,
            fontWeight: 600,
            fontSize: 42,
            color: "#fff",
            background: "linear-gradient(145deg, rgba(255,154,77,0.92), rgba(232,80,2,0.9))",
            border: "1.5px solid rgba(255,200,160,0.6)",
            boxShadow: "0 12px 44px rgba(232,80,2,0.55)",
          }}
        >
          api
        </div>
        {ida > 0 && ida < 1 ? <Pulso x={pIda.x} y={pIda.y} /> : null}
        {volta > 0 && volta < 1 ? <Pulso x={pVolta.x} y={pVolta.y} branco /> : null}
        <Rotulo x={NO_APP.x + NO_APP.w / 2} y={NO_APP.y + NO_APP.h + 24} de={T.s3 + 46} ate={T.s4} texto="seu app" />
      </div>
      {/* nó do app — continua até a barra do meio */}
      <div
        style={{
          position: "absolute",
          left: cApp.x,
          top: cApp.y,
          width: cApp.w,
          height: cApp.h,
          borderRadius: cApp.r,
          scale: String(app),
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "rgba(255,255,255,0.10)",
          border: "1.5px solid rgba(255,255,255,0.3)",
          backdropFilter: "blur(22px)",
          boxShadow: "inset 0 1.5px 0 rgba(255,255,255,0.45), 0 30px 70px rgba(0,0,0,0.5)",
        }}
      >
        <IconeApp tamanho={mix(150, 76, vaiCamadas)} resposta={resposta} />
      </div>
      <Chip x={540} y={1090} de={T.s3 + 205} ate={T.s4 - 4} texto="o ai engineer trabalha aqui" quente />
    </>
  );
};

const Pulso: React.FC<{ x: number; y: number; branco?: boolean }> = ({ x, y, branco }) => (
  <div
    style={{
      position: "absolute",
      left: x - 18,
      top: y - 18,
      width: 36,
      height: 36,
      borderRadius: 99,
      background: branco ? "#fff" : "#FF7A1A",
      boxShadow: branco ? "0 0 30px rgba(255,255,255,0.9)" : "0 0 34px rgba(255,122,26,1)",
    }}
  />
);

const IconeApp: React.FC<{ tamanho: number; resposta: number }> = ({ tamanho, resposta }) => (
  <svg width={tamanho} height={tamanho * 1.25} viewBox="0 0 80 100" fill="none">
    <rect x={8} y={4} width={64} height={92} rx={14} stroke="#fff" strokeWidth={5} />
    <rect x={18} y={22} width={34} height={12} rx={6} fill="rgba(255,255,255,0.75)" />
    <g style={{ transformOrigin: "62px 52px", transform: `scale(${resposta})` }}>
      <rect x={28} y={44} width={36} height={12} rx={6} fill="#FF7A1A" />
    </g>
    <rect x={18} y={64} width={26} height={12} rx={6} fill="rgba(255,255,255,0.45)" />
  </svg>
);

// ---------------------------------------------------------------------------
// G — as três camadas (as mídias viram miniaturas vivas)
// ---------------------------------------------------------------------------
const Camadas: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < T.s4) return null;
  const itens = [
    { txt: "usar", sub: "apps prontos" },
    { txt: "construir", sub: "produto com ia" },
    { txt: "treinar", sub: "o modelo" },
  ];
  const acende = progresso(frame, T.s4 + 46, fps, MOLA_SUAVE, 20);
  const miniUsar = progresso(frame, T.s4 + 6, fps, MOLA_SUAVE, 24);
  return (
    <>
      {itens.map((it, i) => {
        const e = progresso(frame, T.s4 + 4 + i * 6, fps, MOLA_SUAVE, 22);
        const meio = i === 1;
        return (
          <div
            key={it.txt}
            style={{
              position: "absolute",
              left: BARRA.x,
              top: BARRA_Y[i],
              width: BARRA.w,
              height: BARRA.h,
              borderRadius: BARRA.r,
              opacity: e,
              translate: `0 ${mix(60, 0, e)}px`,
              background: meio
                ? `linear-gradient(145deg, rgba(255,154,77,${0.18 + 0.7 * acende}), rgba(232,80,2,${0.15 + 0.7 * acende}))`
                : "rgba(255,255,255,0.07)",
              border: meio ? "1.5px solid rgba(255,200,160,0.6)" : "1.5px solid rgba(255,255,255,0.22)",
              backdropFilter: "blur(24px)",
              boxShadow: meio ? `0 16px ${30 + 40 * acende}px rgba(232,80,2,${0.6 * acende})` : "inset 0 1.5px 0 rgba(255,255,255,0.3)",
            }}
          >
            <div style={{ position: "absolute", left: 270, top: 30, fontFamily: FONTE.motion, color: "#fff" }}>
              <div style={{ fontSize: 50, fontWeight: 600, lineHeight: 1 }}>{it.txt}</div>
              <div style={{ fontSize: 36, fontWeight: 500, opacity: 0.78, marginTop: 10 }}>{it.sub}</div>
            </div>
          </div>
        );
      })}
      {/* miniatura viva do ChatGPT entra pela esquerda na camada 1 */}
      <Moldura
        c={MINI(0)}
        barra={0}
        estilo={{ opacity: miniUsar, translate: `${mix(-300, 0, miniUsar)}px 0`, padding: 6 }}
      >
        <Midia arquivo="chatgpt-conversa.mp4" de={T.s4} corte={175} />
      </Moldura>
      <Chip x={850} y={BARRA_Y[1] + 52} de={T.s4 + 50} ate={T.fecha + 20} texto="ai engineer" quente />
    </>
  );
};

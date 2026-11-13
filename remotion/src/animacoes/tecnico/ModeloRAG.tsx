/**
 * MODELO da série AI Engineer — "o que é RAG" (05/11). Não é episódio: é o teste do estilo de motion,
 * do formato tela cheia (Autor fala com animação por cima → sai → animação → volta, sem dividir a tela)
 * e do sound design (`00-marca/som/`). Sem narração: a fala do autor entra quando o episódio for gravado.
 *
 * Tema padrão: `vidro` (escolhido pelo autor em 05/11). `obsidiana` fica só como alternativa (`motion.ts`).
 *
 * Os 9 pedaços (chunks) são os MESMOS elementos do começo ao fim — documento → pedaço → ponto no mapa →
 * pedaço no contexto — e é isso que deixa a explicação fluida, sem corte entre cenas.
 */
import { Audio, Video } from "@remotion/media";
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { COR, FONTE, useFontesProntas } from "../../brand";
import {
  EASE_FLUIDO,
  MOLA_POP,
  MOLA_SUAVE,
  RAIO,
  TEMAS,
  TemaCtx,
  mix,
  progresso,
  superficie,
  useTema,
  type Tema,
} from "./motion";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// ---------------------------------------------------------------------------
// Linha do tempo (frames a 25 fps)
// ---------------------------------------------------------------------------
const T = {
  revela: 100, // círculo abre: Autor → animação
  s1: 108, // problema: o modelo não conhece os seus dados
  s2: 260, // rag
  s3: 363, // 1 corta os documentos
  s4: 498, // 2 cada pedaço vira ponto
  s5: 628, // 3 a pergunta busca
  s6: 750, // 4 junta no contexto
  s7: 860, // 5 responde com fonte
  fecha: 938, // círculo fecha: animação → Autor
  fim: 1075,
} as const;

export const MODELO_RAG_DURACAO = T.fim;

/** Centro do círculo de transição (no peito do autor). */
const CENTRO_TRANSICAO = { x: 540, y: 1180 };

const MAPA = { x: 540, y: 900, w: 880, h: 660 };
const PONTOS: Array<[number, number]> = [
  [330, 720], [395, 792], [300, 818], // trocas.pdf
  [742, 700], [806, 772], [716, 806], // frete.pdf
  [470, 1080], [572, 1122], [652, 1052], // faq.pdf
];
const PERGUNTA_ALVO = { x: 410, y: 742 };
const DOCS = ["trocas.pdf", "frete.pdf", "faq.pdf"];
const PERGUNTA_TXT = "qual o prazo de troca da minha loja";

// ---------------------------------------------------------------------------
// Som — cada efeito no frame do movimento que ele acompanha
// ---------------------------------------------------------------------------
const SONS: Array<[number, string, number]> = [
  [8, "swipe", 0.4],
  [24, "pop", 0.5],
  [36, "pop", 0.5],
  [48, "pop", 0.5],
  [T.revela - 22, "swipe", 0.45],
  [T.revela - 6, "whoosh-entra", 0.9],
  [T.s1 + 10, "pop", 0.7],
  [T.s1 + 26, "digitar", 0.55],
  [T.s1 + 92, "erro", 0.6],
  [T.s2 - 18, "riser", 0.5],
  [T.s2 + 2, "impacto", 0.9],
  [T.s2 + 24, "pop", 0.5],
  [T.s2 + 38, "pop", 0.5],
  [T.s2 + 52, "pop", 0.5],
  [T.s3 + 10, "swipe", 0.5],
  [T.s3 + 20, "pop", 0.45],
  [T.s3 + 30, "pop", 0.45],
  [T.s3 + 65, "corte-papel", 0.7],
  [T.s3 + 73, "corte-papel", 0.6],
  [T.s3 + 81, "corte-papel", 0.6],
  ...Array.from({ length: 9 }, (_, k) => [T.s4 + 10 + k * 4, "tick", 0.5] as [number, string, number]),
  [T.s5 + 4, "pop", 0.6],
  [T.s5 + 28, "swipe", 0.5],
  [T.s5 + 46, "conectar", 0.7],
  [T.s6 + 18, "swipe", 0.6],
  [T.s6 + 74, "whoosh-entra", 0.45],
  [T.s7 + 2, "brilho", 0.7],
  [T.s7 + 24, "pop", 0.5],
  [T.fecha - 6, "whoosh-sai", 0.9],
  [T.fecha + 40, "swipe", 0.45],
  [T.fecha + 52, "pop", 0.45],
  [T.fecha + 60, "pop", 0.45],
  [T.fecha + 68, "pop", 0.45],
];

// ---------------------------------------------------------------------------
// Composição
// ---------------------------------------------------------------------------
export const ModeloRAG: React.FC<{ tema?: Tema["nome"] }> = ({ tema = "vidro" }) => {
  const prontas = useFontesProntas();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!prontas) return null;

  const abre = progresso(frame, T.revela, fps, MOLA_SUAVE, 34);
  const fecha = progresso(frame, T.fecha, fps, MOLA_SUAVE, 22);
  const raio = 2300 * abre * (1 - fecha);
  const animacaoVisivel = frame >= T.revela && frame < T.fecha + 24;
  const zoomApresentador = frame < T.fecha ? mix(1, 1.12, abre) : mix(1.12, 1, fecha);

  return (
    <TemaCtx.Provider value={TEMAS[tema]}>
      <AbsoluteFill style={{ backgroundColor: "#000" }}>
        {/* o autor (fala) — no episódio real é o vídeo principal; aqui, um corte já gravado, sem som. */}
        <Sequence durationInFrames={T.revela + 36}>
          <Apresentador zoom={zoomApresentador} inicio={0} />
        </Sequence>
        <Sequence from={T.fecha - 4}>
          <Apresentador zoom={zoomApresentador} inicio={160} />
        </Sequence>
        <SeloSerie />
        <IconesSobreApresentador />
        <ResumoSobreApresentador />

        {animacaoVisivel ? (
          <AbsoluteFill
            style={{ clipPath: `circle(${raio}px at ${CENTRO_TRANSICAO.x}px ${CENTRO_TRANSICAO.y}px)` }}
          >
            <Palco />
          </AbsoluteFill>
        ) : null}
        {animacaoVisivel && raio > 60 && raio < 2200 ? <AnelTransicao raio={raio} /> : null}

        {SONS.map(([f, nome, vol], i) => (
          <Sequence key={i} from={f} durationInFrames={90}>
            <Audio src={staticFile(`_marca/sfx/${nome}.mp3`)} volume={vol} />
          </Sequence>
        ))}
      </AbsoluteFill>
    </TemaCtx.Provider>
  );
};

const Apresentador: React.FC<{ zoom: number; inicio: number }> = ({ zoom, inicio }) => (
  <AbsoluteFill style={{ scale: String(zoom), transformOrigin: "50% 45%" }}>
    <Video
      src={staticFile("_demo/ai-engineer/apresentador.mp4")}
      trimBefore={inicio}
      muted
      objectFit="cover"
      style={{ width: "100%", height: "100%" }}
    />
  </AbsoluteFill>
);

/** Vidro sobre o vídeo do autor: sempre translúcido e desfocado, em qualquer tema. */
export const vidroSobreVideo: React.CSSProperties = {
  background: "rgba(255,255,255,0.14)",
  border: "1.5px solid rgba(255,255,255,0.42)",
  backdropFilter: "blur(22px) saturate(150%)",
  boxShadow: "inset 0 1.5px 0 rgba(255,255,255,0.55), 0 20px 50px rgba(0,0,0,0.30)",
};

/**
 * NADA sobre o rosto do autor (decisão de 05/11): tudo o que entra por cima do vídeo dele fica do QUEIXO PARA
 * BAIXO (ou acima da cabeça, onde quase nunca sobra espaço por causa da interface do Instagram).
 * Faixa livre = do queixo até a base da área segura (y 1250). Neste corte o rosto vai de y 166 a y 909 (medido
 * com o detector de rosto da skill capa-reels, amostra a cada 10 frames); em episódio real, medir por take.
 */
const ZONA_SOB_QUEIXO = { topo: 950, base: 1250 } as const;

const SeloSerie: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entra = progresso(frame, 6, fps, MOLA_POP);
  const visivel = frame < T.revela + 10 || frame > T.fecha + 10;
  if (!visivel) return null;
  return (
    <div
      style={{
        position: "absolute",
        top: ZONA_SOB_QUEIXO.topo,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        opacity: entra,
        translate: `0 ${mix(24, 0, entra)}px`,
      }}
    >
      <div
        style={{
          ...vidroSobreVideo,
          display: "flex",
          alignItems: "center",
          gap: 16,
          padding: "12px 28px 12px 12px",
          borderRadius: RAIO.pilula,
          fontFamily: FONTE.familia,
          fontWeight: 600,
          fontSize: 36,
          color: "#fff",
        }}
      >
        <span
          style={{
            width: 50,
            height: 50,
            borderRadius: 99,
            background: "rgba(255,255,255,0.25)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 24,
            fontWeight: 700,
          }}
        >
          10
        </span>
        ai engineer · rag
      </div>
    </div>
  );
};

/** Entrada: 3 peças de vidro nascem em fila, abaixo do queixo, e são "sugadas" para o círculo da transição. */
const IconesSobreApresentador: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame > T.revela + 20) return null;
  const y = 1130;
  const pecas: Array<{ x: number; rot: string; icone: React.ReactNode; inicio: number }> = [
    { x: 250, rot: "documentos", icone: <IconeDoc />, inicio: 24 },
    { x: 540, rot: "busca", icone: <IconeLupa tamanho={54} />, inicio: 32 },
    { x: 830, rot: "modelo", icone: <span style={{ fontSize: 36, fontWeight: 800 }}>llm</span>, inicio: 40 },
  ];
  const vai = progresso(frame, T.revela - 22, fps, MOLA_SUAVE, 22);
  return (
    <>
      {pecas.map((p, i) => {
        const e = progresso(frame, p.inicio, fps, MOLA_POP);
        const flutua = 5 * Math.sin((frame + i * 20) / 18);
        const x = mix(p.x, CENTRO_TRANSICAO.x, vai);
        const yy = mix(y + flutua, CENTRO_TRANSICAO.y, vai);
        return (
          <div
            key={p.rot}
            style={{
              position: "absolute",
              left: x - 110,
              top: yy - 60,
              width: 220,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 8,
              scale: String(e * mix(1, 0.2, vai)),
              opacity: Math.min(1, e * 1.5) * (1 - vai * 0.6),
            }}
          >
            <div
              style={{
                ...vidroSobreVideo,
                width: 116,
                height: 116,
                borderRadius: 34,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontFamily: FONTE.familia,
              }}
            >
              {p.icone}
            </div>
            <span
              style={{
                fontFamily: FONTE.familia,
                fontWeight: 600,
                fontSize: 36,
                color: "#fff",
                textShadow: "0 2px 16px rgba(0,0,0,0.6)",
                opacity: 1 - vai,
              }}
            >
              {p.rot}
            </span>
          </div>
        );
      })}
    </>
  );
};

/** Saída: barra de vidro com o resumo, abaixo do queixo, enquanto ele fecha o assunto. */
const ResumoSobreApresentador: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const inicio = T.fecha + 40;
  if (frame < inicio) return null;
  const e = progresso(frame, inicio, fps, MOLA_SUAVE, 20);
  const itens: Array<[string, React.ReactNode]> = [
    ["buscar", <IconeLupa key="l" tamanho={30} />],
    ["juntar", <IconeJuntar key="j" />],
    ["responder", <IconeBalao key="b" />],
  ];
  return (
    <div
      style={{
        ...vidroSobreVideo,
        position: "absolute",
        left: 70,
        right: 70,
        top: 1060,
        height: 150,
        padding: "0 26px",
        borderRadius: 40,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        opacity: e,
        translate: `0 ${mix(40, 0, e)}px`,
        filter: `blur(${mix(12, 0, e)}px)`,
        fontFamily: FONTE.familia,
        color: "#fff",
      }}
    >
      {itens.map(([txt, icone], i) => {
        const p = progresso(frame, inicio + 10 + i * 6, fps, MOLA_POP);
        return (
          <div
            key={txt}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 14,
              opacity: Math.min(1, p * 1.4),
              translate: `0 ${mix(20, 0, p)}px`,
            }}
          >
            <span
              style={{
                width: 56,
                height: 56,
                borderRadius: 18,
                background: "rgba(255,255,255,0.22)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {icone}
            </span>
            <span style={{ fontSize: 40, fontWeight: 700 }}>{txt}</span>
          </div>
        );
      })}
    </div>
  );
};

const IconeDoc: React.FC = () => (
  <svg width={64} height={76} viewBox="0 0 64 76" fill="none" stroke="#fff" strokeWidth={5} strokeLinejoin="round">
    <path d="M6 6h34l18 18v46H6z" />
    <path d="M40 6v18h18" />
    <path d="M16 42h32M16 54h22" strokeLinecap="round" />
  </svg>
);
const IconeLupa: React.FC<{ tamanho?: number }> = ({ tamanho = 66 }) => (
  <svg width={tamanho} height={tamanho} viewBox="0 0 64 64" fill="none" stroke="#fff" strokeWidth={6} strokeLinecap="round">
    <circle cx={27} cy={27} r={18} />
    <path d="M41 41l15 15" />
  </svg>
);
const IconeJuntar: React.FC = () => (
  <svg width={34} height={34} viewBox="0 0 64 64" fill="none" stroke="#fff" strokeWidth={6} strokeLinecap="round">
    <path d="M8 12h22M8 32h22M8 52h22M38 32h18M48 22l10 10-10 10" />
  </svg>
);
const IconeBalao: React.FC = () => (
  <svg width={34} height={34} viewBox="0 0 64 64" fill="none" stroke="#fff" strokeWidth={6} strokeLinejoin="round">
    <path d="M8 10h48v34H28L14 56V44H8z" />
  </svg>
);
const IconeDocPequeno: React.FC = () => (
  <svg width={26} height={32} viewBox="0 0 64 76" fill="none" stroke="#fff" strokeWidth={7} strokeLinejoin="round">
    <path d="M6 6h34l18 18v46H6z" />
  </svg>
);

const AnelTransicao: React.FC<{ raio: number }> = ({ raio }) => {
  const t = useTema();
  const vidro = t.nome === "vidro";
  return (
    <div
      style={{
        position: "absolute",
        left: CENTRO_TRANSICAO.x - raio,
        top: CENTRO_TRANSICAO.y - raio,
        width: raio * 2,
        height: raio * 2,
        borderRadius: "50%",
        border: vidro ? "6px solid rgba(255,170,110,0.9)" : `10px solid ${COR.acento}`,
        boxShadow: vidro ? `0 0 70px ${t.brilho}` : `0 0 80px ${t.brilho}`,
      }}
    />
  );
};

// ---------------------------------------------------------------------------
// Palco da animação
// ---------------------------------------------------------------------------
const Palco: React.FC = () => {
  const frame = useCurrentFrame();
  const t = useTema();
  // Câmera que respira: nada fica 100 % parado (decisão de 19/10).
  const respira = 1 + 0.012 * Math.sin(frame / 38);
  const deriva = 6 * Math.sin(frame / 52);
  return (
    <AbsoluteFill>
      {t.nome === "vidro" ? <FundoVidro /> : <FundoObsidiana />}
      <AbsoluteFill style={{ scale: String(respira), translate: `0 ${deriva}px` }}>
        <TituloEtapa de={T.s1 + 4} ate={T.s2 - 6} texto="o modelo não conhece os seus dados" />
        <TituloEtapa de={T.s3 + 2} ate={T.s4 - 4} numero={1} texto="corta os documentos em pedaços" />
        <TituloEtapa de={T.s4 + 2} ate={T.s5 - 4} numero={2} texto="cada pedaço vira um ponto no mapa" />
        <TituloEtapa de={T.s5 + 2} ate={T.s6 - 4} numero={3} texto="a pergunta busca os pontos mais perto" />
        <TituloEtapa de={T.s6 + 2} ate={T.s7 - 4} numero={4} texto="junta os pedaços com a pergunta" />
        <TituloEtapa de={T.s7 + 2} ate={T.fecha + 30} numero={5} texto="o modelo responde com fonte" />

        <CenaProblema />
        <CenaSigla />
        <Mapa />
        <Documentos />
        <Pergunta />
        <Contexto />
        <Modelo />
        <Resposta />
        <Pedacos />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const GRAO =
  "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)' opacity='0.55'/></svg>\")";

const FundoObsidiana: React.FC = () => {
  const frame = useCurrentFrame();
  const a = frame / 90;
  return (
    <AbsoluteFill style={{ backgroundColor: "#060608" }}>
      <AbsoluteFill
        style={{
          background: [
            `radial-gradient(48% 30% at ${50 + 18 * Math.sin(a)}% ${30 + 8 * Math.cos(a * 0.8)}%, rgba(232,80,2,0.30), transparent 70%)`,
            `radial-gradient(40% 26% at ${30 + 14 * Math.cos(a * 0.7)}% ${78 + 6 * Math.sin(a)}%, rgba(193,8,209,0.12), transparent 70%)`,
            `radial-gradient(36% 22% at ${78 + 10 * Math.sin(a * 0.6)}% ${62 + 8 * Math.cos(a)}%, rgba(217,195,171,0.10), transparent 70%)`,
          ].join(","),
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage: "radial-gradient(rgba(255,255,255,0.07) 1.5px, transparent 1.5px)",
          backgroundSize: "54px 54px",
          maskImage: "radial-gradient(70% 55% at 50% 50%, black, transparent)",
        }}
      />
      <AbsoluteFill style={{ backgroundImage: GRAO, opacity: 0.08, mixBlendMode: "overlay" }} />
      <AbsoluteFill
        style={{ background: "radial-gradient(120% 80% at 50% 45%, transparent 55%, rgba(0,0,0,0.75))" }}
      />
    </AbsoluteFill>
  );
};

/** Fundo do vidro: preto profundo com luzes laranja que passeiam devagar e anéis muito finos (05/11). */
export const FundoVidro: React.FC = () => {
  const frame = useCurrentFrame();
  const a = frame / 85;
  return (
    <AbsoluteFill style={{ backgroundColor: "#050506" }}>
      <AbsoluteFill
        style={{
          background: [
            `radial-gradient(52% 30% at ${62 + 16 * Math.sin(a)}% ${22 + 7 * Math.cos(a * 0.8)}%, rgba(232,80,2,0.55), transparent 70%)`,
            `radial-gradient(44% 26% at ${22 + 12 * Math.cos(a * 0.7)}% ${80 + 5 * Math.sin(a)}%, rgba(255,122,26,0.32), transparent 70%)`,
            `radial-gradient(30% 18% at ${80 + 8 * Math.sin(a * 0.5)}% ${66 + 6 * Math.cos(a)}%, rgba(217,195,171,0.10), transparent 70%)`,
          ].join(","),
          filter: "blur(20px)",
        }}
      />
      <AbsoluteFill
        style={{
          background:
            "repeating-radial-gradient(circle at 50% 46%, rgba(255,255,255,0) 0px, rgba(255,255,255,0) 150px, rgba(255,255,255,0.045) 151px, rgba(255,255,255,0) 154px)",
          scale: String(1 + 0.04 * Math.sin(frame / 50)),
          maskImage: "radial-gradient(75% 60% at 50% 46%, black, transparent)",
        }}
      />
      <AbsoluteFill style={{ backgroundImage: GRAO, opacity: 0.07, mixBlendMode: "overlay" }} />
      <AbsoluteFill
        style={{ background: "radial-gradient(120% 80% at 50% 45%, transparent 60%, rgba(0,0,0,0.7))" }}
      />
    </AbsoluteFill>
  );
};

/** Título de etapa: número em pílula + frase; as palavras sobem uma a uma. */
export const TituloEtapa: React.FC<{ de: number; ate: number; texto: string; numero?: number }> = ({
  de,
  ate,
  texto,
  numero,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = useTema();
  if (frame < de - 2 || frame > ate + 14) return null;
  const sai = interpolate(frame, [ate, ate + 12], [0, 1], { ...clamp, easing: EASE_FLUIDO });
  const palavras = texto.split(" ");
  const pNum = progresso(frame, de, fps, MOLA_POP);
  return (
    <div
      style={{
        position: "absolute",
        top: 300,
        left: 110,
        right: 110,
        display: "flex",
        alignItems: "flex-start",
        gap: 22,
        opacity: 1 - sai,
        translate: `0 ${-40 * sai}px`,
        filter: `blur(${8 * sai}px)`,
      }}
    >
      {numero ? (
        <div
          style={{
            flex: "0 0 auto",
            width: 72,
            height: 72,
            borderRadius: t.nome === "vidro" ? 99 : 24,
            background: t.forma,
            border: `1.5px solid ${t.formaBorda}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: t.fonteTitulo,
            fontWeight: t.pesoTitulo,
            fontSize: 34,
            color: t.formaTexto,
            scale: String(pNum),
            boxShadow: `0 10px 40px ${t.brilho}`,
          }}
        >
          {String(numero).padStart(2, "0")}
        </div>
      ) : null}
      <div
        style={{
          fontFamily: t.fonteTitulo,
          fontWeight: t.pesoTitulo,
          fontSize: 58,
          lineHeight: 1.04,
          letterSpacing: "-0.02em",
          color: t.texto,
          display: "flex",
          flexWrap: "wrap",
          columnGap: 16,
        }}
      >
        {palavras.map((p, i) => {
          const e = progresso(frame, de + 3 + i * 2.5, fps, MOLA_SUAVE, 16);
          return (
            <span key={i} style={{ opacity: e, translate: `0 ${mix(34, 0, e)}px`, filter: `blur(${mix(10, 0, e)}px)` }}>
              {p}
            </span>
          );
        })}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Cena 1 — o problema
// ---------------------------------------------------------------------------
const CenaProblema: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = useTema();
  if (frame > T.s2 + 20) return null;
  const sai = interpolate(frame, [T.s2 - 10, T.s2 + 8], [0, 1], { ...clamp, easing: EASE_FLUIDO });
  const bolha = progresso(frame, T.s1 + 22, fps, MOLA_POP);
  const letras = Math.floor(interpolate(frame, [T.s1 + 26, T.s1 + 70], [0, PERGUNTA_TXT.length], clamp));
  const resp = progresso(frame, T.s1 + 92, fps, MOLA_POP);
  const tremor = frame > T.s1 + 92 && frame < T.s1 + 104 ? 7 * Math.sin((frame - T.s1) * 2.4) : 0;
  return (
    <AbsoluteFill style={{ opacity: 1 - sai, translate: `0 ${-60 * sai}px` }}>
      <Bolha x={600} y={900} lado="dir" escala={bolha}>
        {PERGUNTA_TXT.slice(0, letras)}
        {letras < PERGUNTA_TXT.length && frame % 12 < 7 ? (
          <span style={{ display: "inline-block", width: 4, height: 44, marginLeft: 6, background: t.cursor, verticalAlign: -6 }} />
        ) : null}
      </Bolha>
      <Bolha x={470} y={1095} lado="esq" escala={resp} apagada desloca={tremor}>
        <span style={{ color: t.erro, fontWeight: 700, marginRight: 14 }}>×</span>
        não sei as regras da sua loja
      </Bolha>
    </AbsoluteFill>
  );
};

const Bolha: React.FC<{
  x: number;
  y: number;
  lado: "esq" | "dir";
  escala: number;
  apagada?: boolean;
  desloca?: number;
  children: React.ReactNode;
}> = ({ x, y, lado, escala, apagada, desloca = 0, children }) => {
  const t = useTema();
  return (
    <div
      style={{
        position: "absolute",
        left: x - 400,
        top: y - 60,
        width: 800,
        display: "flex",
        justifyContent: lado === "dir" ? "flex-end" : "flex-start",
        translate: `${desloca}px 0`,
      }}
    >
      <div
        style={{
          ...superficie(t),
          ...(t.nome === "obsidiana" && !apagada ? { background: "rgba(255,255,255,0.09)" } : {}),
          maxWidth: 720,
          padding: "28px 36px",
          borderRadius: RAIO.bolha,
          borderBottomRightRadius: lado === "dir" ? 10 : RAIO.bolha,
          borderBottomLeftRadius: lado === "esq" ? 10 : RAIO.bolha,
          fontFamily: FONTE.texto,
          fontWeight: 500,
          fontSize: 42,
          lineHeight: 1.25,
          color: apagada ? t.textoApagado : t.texto,
          scale: String(escala),
          opacity: Math.min(1, escala * 1.4),
          transformOrigin: lado === "dir" ? "100% 100%" : "0% 100%",
        }}
      >
        {children}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Cena 2 — a sigla
// ---------------------------------------------------------------------------
const CenaSigla: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = useTema();
  if (frame < T.s2 - 4 || frame > T.s3 + 16) return null;
  const e = progresso(frame, T.s2, fps, MOLA_POP);
  const sai = interpolate(frame, [T.s3 - 12, T.s3 + 6], [0, 1], { ...clamp, easing: EASE_FLUIDO });
  const linhas: Array<[string, string]> = [
    ["retrieval", "buscar"],
    ["augmented", "juntar"],
    ["generation", "responder"],
  ];
  return (
    <AbsoluteFill
      style={{
        alignItems: "center",
        justifyContent: "center",
        opacity: 1 - sai,
        scale: String(mix(1, 0.86, sai)),
        filter: `blur(${10 * sai}px)`,
      }}
    >
      <div
        style={{
          fontFamily: t.fonteTitulo,
          fontWeight: 800,
          fontSize: 300,
          lineHeight: 0.9,
          letterSpacing: "-0.04em",
          backgroundImage: t.siglaTitulo,
          backgroundClip: "text",
          WebkitBackgroundClip: "text",
          color: "transparent",
          scale: String(mix(0.6, 1, e)),
          opacity: Math.min(1, e * 1.5),
          marginTop: -120,
        }}
      >
        rag
      </div>
      <div style={{ marginTop: 40, display: "flex", flexDirection: "column", gap: 20, width: 760 }}>
        {linhas.map(([en, pt], i) => {
          const p = progresso(frame, T.s2 + 24 + i * 14, fps, MOLA_SUAVE, 18);
          return (
            <div
              key={en}
              style={{
                ...superficie(t),
                display: "flex",
                alignItems: "baseline",
                justifyContent: "space-between",
                padding: "18px 30px",
                borderRadius: 24,
                opacity: p,
                translate: `${mix(80, 0, p)}px 0`,
              }}
            >
              <span style={{ fontFamily: FONTE.texto, fontWeight: 500, fontSize: 40, color: t.textoApagado }}>
                <span style={{ color: t.siglaLetra, fontWeight: 700 }}>{en[0]}</span>
                {en.slice(1)}
              </span>
              <span style={{ fontFamily: t.fonteTitulo, fontWeight: 800, fontSize: 48, color: t.texto }}>{pt}</span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Documentos, mapa e os 9 pedaços (os mesmos elementos de ponta a ponta)
// ---------------------------------------------------------------------------
const DOC = { w: 270, h: 380, y: 900 };
const docX = (d: number) => 220 + d * 320;

const Documentos: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = useTema();
  if (frame < T.s3 || frame > T.s4 + 10) return null;
  return (
    <>
      {DOCS.map((nome, d) => {
        const e = progresso(frame, T.s3 + 10 + d * 10, fps, MOLA_POP);
        const corta = progresso(frame, T.s3 + 65 + d * 8, fps, MOLA_SUAVE, 16);
        return (
          <div
            key={nome}
            style={{
              ...(t.nome === "vidro" ? superficie(t) : { background: t.papel, boxShadow: "0 30px 60px rgba(0,0,0,0.5)" }),
              position: "absolute",
              left: docX(d) - DOC.w / 2,
              top: DOC.y - DOC.h / 2,
              width: DOC.w,
              height: DOC.h,
              borderRadius: 26,
              opacity: e * (1 - corta),
              scale: String(mix(0.7, 1, e) * mix(1, 1.08, corta)),
              translate: `0 ${mix(120, 0, e)}px`,
            }}
          >
            <div
              style={{
                position: "absolute",
                bottom: -64,
                left: 0,
                right: 0,
                textAlign: "center",
                fontFamily: FONTE.texto,
                fontWeight: 600,
                fontSize: 36,
                color: t.textoApagado,
              }}
            >
              {nome}
            </div>
          </div>
        );
      })}
    </>
  );
};

const Mapa: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = useTema();
  if (frame < T.s4 - 4 || frame > T.s6 + 50) return null;
  const e = progresso(frame, T.s4, fps, MOLA_SUAVE, 20);
  const sai = interpolate(frame, [T.s6, T.s6 + 16], [0, 1], { ...clamp, easing: EASE_FLUIDO });
  const rotulos: Array<[string, number, number]> = [
    ["trocas", 345, 640],
    ["frete", 760, 622],
    ["faq", 565, 1190],
  ];
  const linhaGrade = t.nome === "vidro" ? "rgba(255,255,255,0.10)" : "rgba(255,255,255,0.04)";
  return (
    <div
      style={{
        ...superficie(t),
        ...(t.nome === "obsidiana" ? { background: "rgba(19,19,24,0.75)" } : {}),
        position: "absolute",
        left: MAPA.x - MAPA.w / 2,
        top: MAPA.y - MAPA.h / 2,
        width: MAPA.w,
        height: MAPA.h,
        borderRadius: 44,
        opacity: e * (1 - sai),
        scale: String(mix(0.92, 1, e)),
        backgroundImage: `linear-gradient(${linhaGrade} 1px, transparent 1px), linear-gradient(90deg, ${linhaGrade} 1px, transparent 1px)`,
        backgroundSize: "88px 88px",
      }}
    >
      <div
        style={{
          position: "absolute",
          bottom: 24,
          right: 34,
          fontFamily: FONTE.texto,
          fontWeight: 500,
          fontSize: 36,
          color: t.textoApagado,
        }}
      >
        embeddings
      </div>
      {rotulos.map(([txt, x, y], i) => {
        const p = progresso(frame, T.s4 + 50 + i * 6, fps, MOLA_SUAVE, 16);
        return (
          <div
            key={txt}
            style={{
              position: "absolute",
              left: x - (MAPA.x - MAPA.w / 2) - 100,
              top: y - (MAPA.y - MAPA.h / 2) - 24,
              width: 200,
              textAlign: "center",
              fontFamily: FONTE.texto,
              fontWeight: 600,
              fontSize: 36,
              color: i === 0 && frame > T.s5 + 46 ? t.rotuloAtivo : t.rotulo,
              opacity: p,
            }}
          >
            {txt}
          </div>
        );
      })}
    </div>
  );
};

type Caixa = { x: number; y: number; w: number; h: number; r: number };

const lerpCaixa = (a: Caixa, b: Caixa, p: number): Caixa => ({
  x: mix(a.x, b.x, p),
  y: mix(a.y, b.y, p),
  w: mix(a.w, b.w, p),
  h: mix(a.h, b.h, p),
  r: mix(a.r, b.r, p),
});

const Pedacos: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = useTema();
  if (frame < T.s3 + 60 || frame > T.s6 + 100) return null;
  const vaiProModelo = progresso(frame, T.s6 + 72, fps, MOLA_SUAVE, 20);
  return (
    <>
      {Array.from({ length: 9 }, (_, k) => {
        const d = Math.floor(k / 3);
        const j = k % 3;
        const escolhido = d === 0;
        const naFolha: Caixa = { x: docX(d), y: DOC.y - 90 + j * 90, w: 210, h: 70, r: 14 };
        const separado: Caixa = { ...naFolha, y: DOC.y - 130 + j * 130, w: 230, h: 84, r: 20 };
        const ponto: Caixa = { x: PONTOS[k][0], y: PONTOS[k][1], w: 34, h: 34, r: 17 };
        const noContexto: Caixa = { x: 540, y: 902 + j * 88, w: 760, h: 72, r: 18 };

        const pSepara = progresso(frame, T.s3 + 65 + d * 8, fps, MOLA_POP);
        const pPonto = progresso(frame, T.s4 + 10 + k * 4, fps, MOLA_SUAVE, 24);
        const pContexto = progresso(frame, T.s6 + 18 + j * 7, fps, MOLA_SUAVE, 24);

        let c = lerpCaixa(naFolha, separado, pSepara);
        c = lerpCaixa(c, ponto, pPonto);
        if (escolhido) c = lerpCaixa(c, noContexto, pContexto);

        // destaque na busca: os 3 de "trocas" acendem, os outros apagam
        const busca = interpolate(frame, [T.s5 + 46, T.s5 + 60], [0, 1], clamp);
        const pulso = escolhido ? 1 + 0.5 * busca * (1 - pContexto) * (0.85 + 0.15 * Math.sin(frame / 3)) : 1;
        const opacidadeSobra = escolhido
          ? 1
          : (1 - 0.7 * busca) * interpolate(frame, [T.s6 - 4, T.s6 + 12], [1, 0], clamp);
        const alvoModelo = { x: 540, y: 560 };
        const x = mix(c.x, alvoModelo.x, escolhido ? vaiProModelo : 0);
        const y = mix(c.y, alvoModelo.y, escolhido ? vaiProModelo : 0);
        const escalaModelo = escolhido ? mix(1, 0.15, vaiProModelo) : 1;

        const formaDePonto = pPonto * (escolhido ? 1 - pContexto : 1);
        const acesa = escolhido && busca > 0;
        const fundo = acesa ? t.destaque : formaDePonto > 0.5 ? t.ponto : t.papel;
        return (
          <div
            key={k}
            style={{
              position: "absolute",
              left: x - c.w / 2,
              top: y - c.h / 2,
              width: c.w,
              height: c.h,
              borderRadius: c.r,
              background: fundo,
              opacity: opacidadeSobra * (1 - (escolhido ? vaiProModelo : 0)),
              scale: String(pulso * escalaModelo),
              boxShadow: acesa ? `0 0 ${40 * busca}px ${t.brilho}` : "0 12px 30px rgba(0,0,0,0.25)",
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              gap: 10,
              padding: `0 ${mix(22, 0, formaDePonto)}px`,
            }}
          >
            {/* linhas de texto do pedaço — somem quando vira ponto */}
            {[0.92, 0.64].map((larg, i) => (
              <div
                key={i}
                style={{
                  height: 10,
                  width: `${larg * 100}%`,
                  borderRadius: 6,
                  background: acesa ? t.linhaDestaque : t.linhaPapel,
                  opacity: 1 - formaDePonto,
                }}
              />
            ))}
          </div>
        );
      })}
    </>
  );
};

/** A pergunta vira um ponto que cai no mapa; ondas mostram a busca; linhas ligam aos vizinhos. */
const Pergunta: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = useTema();
  if (frame < T.s5 || frame > T.s6 + 30) return null;
  const e = progresso(frame, T.s5 + 4, fps, MOLA_POP);
  const cai = progresso(frame, T.s5 + 28, fps, MOLA_SUAVE, 22);
  const sai = interpolate(frame, [T.s6 - 4, T.s6 + 12], [0, 1], clamp);
  const pilula = { x: 540, y: 500 };
  const x = mix(pilula.x, PERGUNTA_ALVO.x, cai);
  const y = mix(pilula.y, PERGUNTA_ALVO.y, cai);
  const w = mix(700, 44, cai);
  const h = mix(92, 44, cai);
  const linhas = interpolate(frame, [T.s5 + 44, T.s5 + 62], [0, 1], { ...clamp, easing: EASE_FLUIDO });
  const ponto = t.destaque;
  return (
    <AbsoluteFill style={{ opacity: 1 - sai }}>
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        {[0, 1, 2].map((k) => {
          const [px, py] = PONTOS[k];
          return (
            <line
              key={k}
              x1={PERGUNTA_ALVO.x}
              y1={PERGUNTA_ALVO.y}
              x2={mix(PERGUNTA_ALVO.x, px, linhas)}
              y2={mix(PERGUNTA_ALVO.y, py, linhas)}
              stroke={t.traco}
              strokeWidth={4}
              strokeLinecap="round"
              opacity={0.9}
            />
          );
        })}
        {[0, 1, 2].map((i) => {
          const r = interpolate(frame, [T.s5 + 40 + i * 7, T.s5 + 70 + i * 7], [10, 190], clamp);
          const o = interpolate(frame, [T.s5 + 40 + i * 7, T.s5 + 70 + i * 7], [0.7, 0], clamp);
          return (
            <circle
              key={i}
              cx={PERGUNTA_ALVO.x}
              cy={PERGUNTA_ALVO.y}
              r={r}
              fill="none"
              stroke={t.traco}
              strokeWidth={3}
              opacity={frame >= T.s5 + 40 ? o : 0}
            />
          );
        })}
      </svg>
      <div
        style={{
          ...(cai > 0.6 ? { background: ponto } : superficie(t)),
          position: "absolute",
          left: x - w / 2,
          top: y - h / 2,
          width: w,
          height: h,
          borderRadius: RAIO.pilula,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: FONTE.texto,
          fontWeight: 500,
          fontSize: 38,
          color: t.texto,
          whiteSpace: "nowrap",
          overflow: "hidden",
          scale: String(e),
          boxShadow: cai > 0.6 ? `0 0 40px ${t.brilho}` : superficie(t).boxShadow,
        }}
      >
        <span style={{ opacity: 1 - cai * 2 }}>{PERGUNTA_TXT}</span>
      </div>
    </AbsoluteFill>
  );
};

/** Cartão do contexto: a pergunta em cima, os 3 pedaços entram embaixo; depois tudo vai para o modelo. */
const Contexto: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = useTema();
  if (frame < T.s6 || frame > T.s7 + 10) return null;
  const e = progresso(frame, T.s6 + 12, fps, MOLA_SUAVE, 18);
  const vai = progresso(frame, T.s6 + 72, fps, MOLA_SUAVE, 20);
  const cy = 950;
  return (
    <div
      style={{
        ...superficie(t),
        ...(t.nome === "obsidiana"
          ? { background: "rgba(19,19,24,0.92)", border: `2px solid rgba(232,80,2,${0.25 + 0.35 * e})` }
          : {}),
        position: "absolute",
        left: 540 - 440,
        top: cy - 240,
        width: 880,
        height: 480,
        borderRadius: 40,
        opacity: e * (1 - vai),
        translate: `0 ${mix(60, 0, e) + mix(0, 560 - cy, vai)}px`,
        scale: String(mix(1, 0.2, vai)),
      }}
    >
      <div style={{ position: "absolute", top: 26, left: 40, fontFamily: FONTE.texto, fontSize: 36, fontWeight: 600, color: t.texto }}>
        {PERGUNTA_TXT}
      </div>
      <div
        style={{
          position: "absolute",
          top: 78,
          left: 40,
          fontFamily: FONTE.texto,
          fontSize: 36,
          fontWeight: 500,
          color: t.nome === "vidro" ? t.textoApagado : COR.acento,
        }}
      >
        + 3 pedaços de trocas.pdf
      </div>
    </div>
  );
};

/** O modelo (LLM): mesma forma em toda a série. */
const Modelo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = useTema();
  const naCena1 = frame >= T.s1 && frame < T.s2 + 10;
  const naCena6 = frame >= T.s6 + 30 && frame < T.fecha + 30;
  if (!naCena1 && !naCena6) return null;
  const entra1 = progresso(frame, T.s1 + 10, fps, MOLA_POP);
  const sai1 = interpolate(frame, [T.s2 - 10, T.s2 + 6], [0, 1], clamp);
  const entra6 = progresso(frame, T.s6 + 32, fps, MOLA_POP);
  // ao receber o contexto, o modelo "engole" e pulsa
  const recebe = progresso(frame, T.s6 + 88, fps, MOLA_POP);
  const desce = progresso(frame, T.s7, fps, MOLA_SUAVE, 22);
  const pensando = naCena1 && frame > T.s1 + 72 && frame < T.s1 + 92;
  const escala = naCena1 ? entra1 * (1 - sai1) : entra6 * (1 + 0.12 * Math.sin(Math.PI * Math.min(1, recebe)));
  const cy = naCena1 ? 600 : mix(560, 600, desce);
  const lado = naCena1 ? 260 : 230;
  return (
    <div
      style={{
        ...(t.nome === "vidro" ? superficie(t) : {}),
        position: "absolute",
        left: 540 - lado / 2,
        top: cy - lado / 2,
        width: lado,
        height: lado,
        borderRadius: 60,
        background: t.forma,
        border: `2px solid ${t.formaBorda}`,
        boxShadow: `0 0 ${110 + 30 * Math.sin(frame / 8)}px ${t.brilho}, inset 0 2px 0 rgba(255,255,255,0.45)`,
        scale: String(escala),
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        gap: 8,
      }}
    >
      <span style={{ fontFamily: t.fonteTitulo, fontWeight: 800, fontSize: 76, color: t.formaTexto, letterSpacing: "-0.03em" }}>
        llm
      </span>
      <div style={{ display: "flex", gap: 12, height: 16, opacity: pensando ? 1 : 0 }}>
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            style={{
              width: 14,
              height: 14,
              borderRadius: 99,
              background: "#fff",
              opacity: 0.4 + 0.6 * Math.max(0, Math.sin(frame / 3 - i)),
            }}
          />
        ))}
      </div>
    </div>
  );
};

const Resposta: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = useTema();
  if (frame < T.s7) return null;
  const e = progresso(frame, T.s7 + 2, fps, MOLA_POP);
  const chip = progresso(frame, T.s7 + 24, fps, MOLA_POP);
  return (
    <>
      <div
        style={{
          position: "absolute",
          left: 120,
          top: 820,
          width: 840,
          padding: "34px 40px",
          borderRadius: RAIO.bolha,
          borderTopLeftRadius: 10,
          background: t.resposta,
          color: t.respostaTexto,
          fontFamily: FONTE.texto,
          fontWeight: 600,
          fontSize: 46,
          lineHeight: 1.22,
          scale: String(e),
          opacity: Math.min(1, e * 1.4),
          transformOrigin: "0% 0%",
          boxShadow: "0 30px 80px rgba(0,0,0,0.35)",
        }}
      >
        a troca é em até 7 dias corridos com a nota fiscal
      </div>
      <div
        style={{
          ...(t.nome === "vidro" ? superficie(t) : {}),
          position: "absolute",
          left: 120,
          top: 1080,
          display: "flex",
          alignItems: "center",
          gap: 14,
          padding: "14px 26px",
          borderRadius: RAIO.pilula,
          background: t.chip,
          border: `1.5px solid ${t.chipBorda}`,
          color: t.chipTexto,
          fontFamily: FONTE.texto,
          fontWeight: 600,
          fontSize: 36,
          scale: String(chip),
          transformOrigin: "0% 50%",
        }}
      >
        <IconeDocPequeno /> fonte trocas.pdf
      </div>
    </>
  );
};

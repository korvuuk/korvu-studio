import "./index.css";
import { Composition, Folder, Still } from "remotion";
import { VIDEO } from "./brand";
import { Capa, CapaGrade } from "./compositions/Capa";
import { calcularMetadataReel, Reel } from "./compositions/Reel";
import { DEMO_PROPS } from "./demo/amostra";
import { MODELO_RAG_DURACAO, ModeloRAG } from "./animacoes/tecnico/ModeloRAG";
import { MODELO_MISTO_DURACAO, ModeloMisto } from "./animacoes/tecnico/ModeloMisto";

// fps: `VIDEO.fps` (25, FPS_PROJETO) é só o padrão — `calcularMetadataReel` usa `props.fps`
// (reel-props.json.fps, vindo do edl.json). Capa/CapaGrade são Stills (sem fps).
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Folder name="Reels">
        {/* Uso real: npx remotion render Reel out.mp4 --props=videos/<slug>/edicao/reel-props.json */}
        <Composition
          id="Reel"
          component={Reel}
          durationInFrames={10 * VIDEO.fps}
          fps={VIDEO.fps}
          width={VIDEO.largura}
          height={VIDEO.altura}
          calculateMetadata={calcularMetadataReel}
          defaultProps={{
            video: null,
            duracaoSeg: 10,
            fps: VIDEO.fps,
            legendas: [],
            overlays: [],
            segmentos: [],
            titulo: null,
            estiloLegenda: "selecao",
            legendaPosicao: "baixo",
            arquivoProps: null,
          }}
        />
        {/* Demo sem mídia externa (fundo sólido no lugar da câmera). */}
        <Composition
          id="DemoLegendas"
          component={Reel}
          durationInFrames={10 * VIDEO.fps}
          fps={VIDEO.fps}
          width={VIDEO.largura}
          height={VIDEO.altura}
          calculateMetadata={calcularMetadataReel}
          defaultProps={DEMO_PROPS}
        />
      </Folder>
      <Folder name="AIEngineer">
        {/* Modelo de estilo (05/11): tela cheia, o autor sai → animação → Autor volta, com sound design. */}
        <Composition
          id="ModeloRAG"
          component={ModeloRAG}
          durationInFrames={MODELO_RAG_DURACAO}
          fps={VIDEO.fps}
          width={VIDEO.largura}
          height={VIDEO.altura}
          defaultProps={{ tema: "obsidiana" as const }} /* alternativa descartada em 05/11 */
        />
        <Composition
          id="ModeloRAGVidro"
          component={ModeloRAG}
          durationInFrames={MODELO_RAG_DURACAO}
          fps={VIDEO.fps}
          width={VIDEO.largura}
          height={VIDEO.altura}
          defaultProps={{ tema: "vidro" as const }}
        />
        <Composition
          id="ModeloMisto"
          component={ModeloMisto}
          durationInFrames={MODELO_MISTO_DURACAO}
          fps={VIDEO.fps}
          width={VIDEO.largura}
          height={VIDEO.altura}
        />
      </Folder>
      <Folder name="Capa">
        <Still
          id="Capa"
          component={Capa}
          width={1080}
          height={1920}
          defaultProps={{
            frame: null,
            contexto: "Se você usa o ChatGPT assim,",
            impacto: "tá jogando tempo fora.",
            cinza: 3,
            rabisco: "fora",
            selecao: "ChatGPT assim",
            posicao: "base",
            corRabisco: null,
            escurecer: 0.12,
          }}
        />
        <Still
          id="CapaGrade"
          component={CapaGrade}
          width={1080}
          height={1440}
          defaultProps={{
            frame: null,
            contexto: "Se você usa o ChatGPT assim,",
            impacto: "tá jogando tempo fora.",
            cinza: 3,
            rabisco: "fora",
            selecao: "ChatGPT assim",
            posicao: "base",
            corRabisco: null,
            escurecer: 0.12,
          }}
        />
      </Folder>
    </>
  );
};

import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { FUNDO_MARCA, VIDEO } from "../brand";

type Props = {
  children?: React.ReactNode;
};

/**
 * Fundo de marca (grade isométrica escura) para mídia retangular isolada que não preenche o quadro —
 * decisão do autor de 27/10 (`00-marca/layouts.md` § "Imagem/vídeo retangular isolado"): **nunca** preto
 * liso em volta do `solo` / do `full` contido. Usado por `ExtraMidia` (modos `solo` e `full` sem cover-crop).
 */
export const FundoIsometrico: React.FC<Props> = ({ children }) => (
  <AbsoluteFill>
    <Img
      src={staticFile(FUNDO_MARCA.isometrico)}
      style={{ width: VIDEO.largura, height: VIDEO.altura, objectFit: "cover" }}
    />
    {children}
  </AbsoluteFill>
);

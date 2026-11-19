import React from "react";
import { Composition } from "remotion";
import { FinanceCampusDemo } from "./scenes/FinanceCampusDemo";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="FinanceCampusDemo"
      component={FinanceCampusDemo}
      durationInFrames={300}
      fps={30}
      width={1080}
      height={1920}
    />
  </>
);

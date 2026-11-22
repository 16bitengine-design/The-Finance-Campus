import React from "react";
import { Composition } from "remotion";
import { FinanceCampusDemo } from "./scenes/FinanceCampusDemo";
import { MonochromeFinanceStory } from "./scenes/MonochromeFinanceStory";
import { ProgressiveNarratedSample } from "./scenes/ProgressiveNarratedSample";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="FinanceCampusDemo" component={FinanceCampusDemo} durationInFrames={480} fps={30} width={1080} height={1920}/>
    <Composition id="FinanceCampusMonochromeSample" component={MonochromeFinanceStory} durationInFrames={4500} fps={30} width={1080} height={1920}/>
    <Composition
      id="FinanceCampusProgressiveNarratedSample"
      component={ProgressiveNarratedSample}
      durationInFrames={4500}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{cues: [], duration: 150}}
    />
  </>
);

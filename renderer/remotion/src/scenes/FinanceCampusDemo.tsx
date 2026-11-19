import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { CanvasStage } from "../components/CanvasStage";
import { RoughIllustration } from "../components/RoughIllustration";
import { WhiteboardStroke } from "../components/WhiteboardStroke";

export const FinanceCampusDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const titleOpacity = interpolate(frame, [12, 35], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF", overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: 0, opacity: 0.32 }}>
        <CanvasStage width={1080} height={1920} />
      </div>
      <div style={{
        position: "absolute", top: 150, left: 70, right: 70,
        color: "#102B55", fontFamily: "Arial, sans-serif",
        fontSize: 76, fontWeight: 800, lineHeight: 1.08,
        opacity: titleOpacity, textAlign: "center",
      }}>
        Give every shilling a job
      </div>
      <svg viewBox="0 0 1080 1920" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        <WhiteboardStroke
          d="M 160 520 C 270 390 410 390 520 520 S 790 650 920 500"
          startFrame={25}
          durationFrames={75}
          stroke="#168C43"
          strokeWidth={12}
        />
        <WhiteboardStroke
          d="M 220 1110 L 430 920 L 610 1030 L 850 760"
          startFrame={95}
          durationFrames={90}
          stroke="#F5B817"
          strokeWidth={14}
        />
      </svg>
      <div style={{ position: "absolute", top: 600, left: 350, width: 380 }}>
        <RoughIllustration seed={21} />
      </div>
      <div style={{
        position: "absolute", bottom: 125, left: 70, right: 70,
        color: "#102B55", fontFamily: "Arial, sans-serif",
        fontSize: 34, fontWeight: 600, textAlign: "center",
      }}>
        Plan • Save • Spend intentionally
      </div>
    </AbsoluteFill>
  );
};

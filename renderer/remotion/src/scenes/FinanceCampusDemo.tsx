import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { FinancialStoryVector } from "../components/FinancialStoryVector";
import { WhiteboardStroke } from "../components/WhiteboardStroke";

export const FinanceCampusDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const titleOpacity = interpolate(frame, [8, 28], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#FFFFFF", overflow: "hidden" }}>
      <div style={{
        position: "absolute", top: 95, left: 65, right: 65,
        color: "#111111", fontFamily: "Arial, sans-serif",
        fontSize: 66, fontWeight: 800, lineHeight: 1.08,
        opacity: titleOpacity, textAlign: "center",
      }}>
        When the bills arrive
      </div>
      <svg viewBox="0 0 1080 1920" style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
        <WhiteboardStroke
          d="M 145 310 C 280 260 390 260 520 310 S 800 360 935 300"
          startFrame={18}
          durationFrames={60}
          stroke="#111111"
          strokeWidth={7}
        />
      </svg>
      <div style={{ position: "absolute", top: 390, left: 80, width: 920 }}>
        <FinancialStoryVector startFrame={0} />
      </div>
      <div style={{
        position: "absolute", bottom: 105, left: 70, right: 70,
        color: "#111111", fontFamily: "Arial, sans-serif",
        fontSize: 31, fontWeight: 600, textAlign: "center",
      }}>
        See the problem. Understand the choices. Change the outcome.
      </div>
    </AbsoluteFill>
  );
};

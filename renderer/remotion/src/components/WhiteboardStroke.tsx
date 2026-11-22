import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

type Props = {
  d: string;
  stroke?: string;
  strokeWidth?: number;
  startFrame?: number;
  durationFrames?: number;
  fill?: string;
};

export const WhiteboardStroke: React.FC<Props> = ({
  d,
  stroke = "#111111",
  strokeWidth = 9,
  startFrame = 0,
  durationFrames = 45,
  fill = "none",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = interpolate(
    frame,
    [startFrame, startFrame + durationFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <path
      d={d}
      fill={fill}
      stroke={stroke}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeDasharray="1"
      pathLength={1}
      strokeDashoffset={progress}
      style={{ transition: "none" }}
      data-fps={fps}
    />
  );
};

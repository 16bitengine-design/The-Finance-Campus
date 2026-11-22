import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

type Props = { startFrame?: number };

const ink = "#111111";
const paper = "#FFFFFF";

const DrawPath: React.FC<{
  d: string;
  start: number;
  duration?: number;
  width?: number;
  fill?: string;
}> = ({ d, start, duration = 35, width = 8, fill = "none" }) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [start, start + duration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <path
      d={d}
      fill={fill}
      stroke={ink}
      strokeWidth={width}
      strokeLinecap="round"
      strokeLinejoin="round"
      pathLength={1}
      strokeDasharray={1}
      strokeDashoffset={1 - progress}
    />
  );
};

/** Authored monochrome SVG scene: a person reviewing bills at a kitchen table. */
export const FinancialStoryVector: React.FC<Props> = ({ startFrame = 0 }) => {
  const frame = useCurrentFrame();
  const coinLift = Math.sin((frame - startFrame) / 12) * 5;
  const billSlide = interpolate(frame, [startFrame + 90, startFrame + 125], [35, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <svg viewBox="0 0 900 900" role="img" aria-label="Black and white vector illustration of a person reviewing household bills">
      <g fill="none" stroke={ink} strokeLinecap="round" strokeLinejoin="round">
        <DrawPath d="M65 770 H835" start={startFrame} duration={22} width={10} />
        {/* Room and window */}
        <DrawPath d="M110 90 V330 H350 V90 Z M230 90 V330 M110 210 H350" start={startFrame + 8} duration={34} />
        <DrawPath d="M145 130 L190 170 M270 130 L315 170" start={startFrame + 30} duration={20} width={5} />
        {/* Chair */}
        <DrawPath d="M235 460 V710 M235 520 Q180 500 170 560 V700 M235 700 H385" start={startFrame + 35} duration={35} />
        {/* Character head, ears and hair */}
        <DrawPath d="M405 220 C405 140 465 105 530 125 C590 145 605 215 585 285 C570 340 525 365 470 340 C425 320 405 275 405 220 Z" start={startFrame + 48} duration={48} />
        <DrawPath d="M405 220 C390 160 430 105 495 105 C550 100 600 145 600 205 C570 180 540 170 510 170 C475 170 445 190 405 220" start={startFrame + 70} duration={38} />
        <DrawPath d="M405 235 Q370 225 385 270 Q395 290 420 280 M585 235 Q620 225 605 270 Q595 290 575 280" start={startFrame + 95} duration={22} width={6} />
        {/* Worried face */}
        <DrawPath d="M455 225 Q475 210 493 225 M535 225 Q555 210 573 225" start={startFrame + 110} duration={20} width={6} />
        <DrawPath d="M465 255 Q475 247 485 255 M545 255 Q555 247 565 255" start={startFrame + 122} duration={16} width={6} />
        <DrawPath d="M495 300 Q520 280 545 300" start={startFrame + 135} duration={18} width={6} />
        <DrawPath d="M505 320 Q520 315 535 320" start={startFrame + 145} duration={12} width={4} />
        {/* Body and shirt */}
        <DrawPath d="M440 350 Q390 365 365 430 L340 590 Q420 630 590 590 L565 430 Q545 365 550 350 Q500 385 440 350 Z" start={startFrame + 155} duration={45} />
        <DrawPath d="M440 365 L490 425 L535 365 M490 425 L490 580" start={startFrame + 190} duration={28} width={6} />
        {/* Arms reaching to bills */}
        <DrawPath d="M385 420 Q330 460 345 520 L420 585 M555 420 Q620 450 650 520 L600 575" start={startFrame + 210} duration={42} />
        <DrawPath d="M420 585 Q440 600 455 580 M600 575 Q625 590 642 570" start={startFrame + 245} duration={22} width={6} />
        {/* Table */}
        <DrawPath d="M135 600 H780 M180 600 V760 M735 600 V760" start={startFrame + 260} duration={32} width={10} />
        {/* Bills and envelope */}
        <g transform={`translate(0 ${billSlide})`}>
          <DrawPath d="M230 545 L390 530 L405 615 L245 630 Z M265 565 L365 555 M275 590 L355 582" start={startFrame + 285} duration={34} />
          <DrawPath d="M520 545 L690 545 L690 650 L520 650 Z M520 545 L605 610 L690 545" start={startFrame + 315} duration={30} />
        </g>
        {/* Wallet and coins */}
        <DrawPath d="M700 500 Q740 485 770 510 L780 570 Q745 590 705 570 Z M700 520 H770" start={startFrame + 340} duration={28} />
        <g transform={`translate(0 ${coinLift})`}>
          <DrawPath d="M735 470 C735 455 785 455 785 470 C785 485 735 485 735 470 Z M735 450 C735 435 785 435 785 450 C785 465 735 465 735 450 Z M735 430 C735 415 785 415 785 430 C785 445 735 445 735 430 Z" start={startFrame + 365} duration={35} />
        </g>
        {/* Small visual stress marks */}
        <DrawPath d="M635 155 L655 135 M650 180 L680 175 M380 120 L365 95" start={startFrame + 400} duration={18} width={5} />
      </g>
      <rect x="0" y="0" width="900" height="900" fill="none" stroke={paper} />
    </svg>
  );
};

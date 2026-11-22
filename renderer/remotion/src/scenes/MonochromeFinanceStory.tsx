import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  useCurrentFrame,
} from "remotion";
import { FinancialStoryVector } from "../components/FinancialStoryVector";

const INK = "#111111";
const PAPER = "#FFFFFF";

const Draw: React.FC<{
  d: string;
  start?: number;
  duration?: number;
  width?: number;
  fill?: string;
}> = ({ d, start = 0, duration = 45, width = 8, fill = "none" }) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [start, start + duration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <path d={d} fill={fill} stroke={INK} strokeWidth={width}
      strokeLinecap="round" strokeLinejoin="round"
      pathLength={1} strokeDasharray={1} strokeDashoffset={1 - progress} />
  );
};

const SceneTitle: React.FC<{ title: string; subtitle: string }> = ({ title, subtitle }) => (
  <div style={{ position: "absolute", top: 105, left: 65, right: 65, textAlign: "center", color: INK, fontFamily: "Arial, sans-serif" }}>
    <div style={{ fontSize: 62, lineHeight: 1.08, fontWeight: 800 }}>{title}</div>
    <div style={{ marginTop: 22, fontSize: 30, fontWeight: 500 }}>{subtitle}</div>
  </div>
);

const SceneOne: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: PAPER }}>
    <SceneTitle title="WHEN THE BILLS ARRIVE" subtitle="One income. Many demands. A difficult choice." />
    <div style={{ position: "absolute", top: 390, left: 75, width: 930 }}>
      <FinancialStoryVector startFrame={15} />
    </div>
    <div style={{ position: "absolute", bottom: 125, left: 80, right: 80, textAlign: "center", fontSize: 31, color: INK, fontWeight: 600 }}>
      The pressure feels bigger when every bill arrives at once.
    </div>
  </AbsoluteFill>
);

const SceneTwo: React.FC = () => {
  const frame = useCurrentFrame();
  const slide = interpolate(frame, [80, 150], [220, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const stamps = interpolate(frame, [280, 350], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ backgroundColor: PAPER }}>
      <SceneTitle title="MAKE THE MONEY VISIBLE" subtitle="Separate the bills before deciding what to do." />
      <svg viewBox="0 0 1080 1200" style={{ position: "absolute", top: 430, width: "100%", height: 1200 }}>
        <g fill="none" stroke={INK} strokeWidth="9" strokeLinecap="round" strokeLinejoin="round">
          <Draw d="M130 250 H950 V820 H130 Z" start={0} duration={50} />
          <Draw d="M175 310 H905 M175 370 H905" start={40} duration={30} width={5} />
          <Draw d="M220 440 H470 V760 H220 Z" start={90} duration={40} />
          <Draw d="M515 440 H765 V760 H515 Z" start={125} duration={40} />
          <Draw d="M810 440 H900 V760 H810 Z" start={160} duration={40} />
          <Draw d="M250 500 H430 M250 555 H410 M250 610 H380" start={200} duration={50} width={6} />
          <Draw d="M545 500 H735 M545 555 H710 M545 610 H680" start={235} duration={50} width={6} />
          <Draw d="M830 500 H880 M830 555 H870" start={270} duration={30} width={6} />
          <Draw d="M260 685 L320 735 L425 620" start={300} duration={45} width={11} />
          <Draw d="M555 685 L615 735 L720 620" start={340} duration={45} width={11} />
        </g>
        <g fill={INK} fontFamily="Arial, sans-serif" fontSize="35" fontWeight="700" textAnchor="middle" opacity={stamps}>
          <text x="345" y="405">ESSENTIALS</text>
          <text x="640" y="405">OBLIGATIONS</text>
          <text x="855" y="405">EXTRAS</text>
        </g>
        <g transform={`translate(0 ${slide})`} fill="none" stroke={INK} strokeWidth="8">
          <Draw d="M350 150 L430 150 L450 215 L370 215 Z M370 170 H430" start={20} duration={40} />
          <Draw d="M580 140 H700 V225 H580 Z M580 140 L640 190 L700 140" start={50} duration={45} />
        </g>
      </svg>
      <div style={{ position: "absolute", bottom: 125, left: 80, right: 80, textAlign: "center", fontSize: 31, color: INK, fontWeight: 600 }}>
        List what must be paid, what can wait, and what can be reduced.
      </div>
    </AbsoluteFill>
  );
};

const SceneThree: React.FC = () => {
  const frame = useCurrentFrame();
  const coinX = interpolate(frame, [80, 220], [540, 300], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const coinY = interpolate(frame, [80, 220], [350, 730], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ backgroundColor: PAPER }}>
      <SceneTitle title="GIVE EVERY SHILLING A JOB" subtitle="A simple plan creates clarity before the money is spent." />
      <svg viewBox="0 0 1080 1200" style={{ position: "absolute", top: 420, width: "100%", height: 1200 }}>
        <g fill="none" stroke={INK} strokeWidth="9" strokeLinecap="round" strokeLinejoin="round">
          <Draw d="M470 210 H610 V330 H470 Z M500 210 V180 H580 V210" start={0} duration={50} />
          <Draw d="M540 330 V470 M540 470 L230 650 M540 470 L540 650 M540 470 L850 650" start={50} duration={75} />
          <Draw d="M120 650 H340 V930 H120 Z M120 650 Q230 590 340 650" start={120} duration={50} />
          <Draw d="M430 650 H650 V930 H430 Z M430 650 Q540 590 650 650" start={160} duration={50} />
          <Draw d="M740 650 H960 V930 H740 Z M740 650 Q850 590 960 650" start={200} duration={50} />
          <Draw d="M160 730 H300 M470 730 H610 M780 730 H920" start={250} duration={35} width={6} />
          <Draw d="M190 790 H270 M500 790 H580 M810 790 H890" start={280} duration={35} width={6} />
          <Draw d="M220 850 H250 M530 850 H560 M840 850 H870" start={310} duration={25} width={6} />
        </g>
        <g fill={INK} fontFamily="Arial, sans-serif" fontSize="34" fontWeight="700" textAnchor="middle">
          <text x="230" y="990">NEEDS</text>
          <text x="540" y="990">DEBT</text>
          <text x="850" y="990">SAVINGS</text>
          <text x="540" y="155" fontSize="40">INCOME</text>
        </g>
        <g transform={`translate(${coinX} ${coinY})`}>
          <circle cx="0" cy="0" r="42" fill={PAPER} stroke={INK} strokeWidth="9" />
          <path d="M-12 -22 V22 M12 -22 V22 M-20 -10 H20 M-20 10 H20" stroke={INK} strokeWidth="6" fill="none" />
        </g>
      </svg>
      <div style={{ position: "absolute", bottom: 125, left: 80, right: 80, textAlign: "center", fontSize: 31, color: INK, fontWeight: 600 }}>
        Start with essentials. Make a realistic debt plan. Protect a little savings.
      </div>
    </AbsoluteFill>
  );
};

const SceneFour: React.FC = () => {
  const frame = useCurrentFrame();
  const coins = [0, 1, 2, 3, 4, 5, 6].map((n) => ({
    x: 400 + (n % 3) * 105,
    y: 250 + Math.floor(n / 3) * 95,
    opacity: interpolate(frame, [70 + n * 35, 100 + n * 35], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
  }));
  return (
    <AbsoluteFill style={{ backgroundColor: PAPER }}>
      <SceneTitle title="SMALL SAVINGS STILL COUNT" subtitle="Consistency matters more than starting big." />
      <svg viewBox="0 0 1080 1200" style={{ position: "absolute", top: 420, width: "100%", height: 1200 }}>
        <g fill="none" stroke={INK} strokeWidth="10" strokeLinecap="round" strokeLinejoin="round">
          <Draw d="M390 300 H690 L650 880 Q540 960 430 880 Z" start={0} duration={55} />
          <Draw d="M470 300 V250 H610 V300" start={45} duration={30} />
          <Draw d="M440 500 Q540 550 640 500 M450 650 Q540 700 630 650" start={100} duration={55} width={6} />
          <Draw d="M460 890 H620 M490 930 H590" start={145} duration={30} width={7} />
        </g>
        {coins.map((coin, index) => (
          <g key={index} opacity={coin.opacity}>
            <circle cx={coin.x} cy={coin.y} r="37" fill={PAPER} stroke={INK} strokeWidth="8" />
            <path d={`M${coin.x - 12} ${coin.y - 17} V${coin.y + 17} M${coin.x + 12} ${coin.y - 17} V${coin.y + 17}`} stroke={INK} strokeWidth="5" />
          </g>
        ))}
        <g fill={INK} fontFamily="Arial, sans-serif" fontWeight="700" textAnchor="middle">
          <text x="540" y="1030" fontSize="40">EMERGENCY FUND</text>
          <text x="540" y="1080" fontSize="27">Build it one decision at a time</text>
        </g>
      </svg>
      <div style={{ position: "absolute", bottom: 125, left: 80, right: 80, textAlign: "center", fontSize: 31, color: INK, fontWeight: 600 }}>
        Save an amount you can repeat, then increase it when you can.
      </div>
    </AbsoluteFill>
  );
};

const SceneFive: React.FC = () => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [50, 650], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ backgroundColor: PAPER }}>
      <SceneTitle title="PROGRESS IS BUILT, NOT WISHED FOR" subtitle="A plan gives your next decision a direction." />
      <div style={{ position: "absolute", top: 410, left: 75, width: 930 }}>
        <FinancialStoryVector startFrame={0} />
      </div>
      <svg viewBox="0 0 1080 1200" style={{ position: "absolute", top: 430, width: "100%", height: 1200 }}>
        <g fill="none" stroke={INK} strokeWidth="10" strokeLinecap="round" strokeLinejoin="round">
          <Draw d="M120 940 H960 M160 940 V260" start={0} duration={45} />
          <path d="M200 850 L360 760 L520 700 L680 510 L850 360" stroke={INK} strokeWidth="12" strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1-progress} />
          <Draw d="M790 360 H850 V420" start={250} duration={25} width={8} />
        </g>
        <g fill={INK} fontFamily="Arial, sans-serif" fontSize="30" fontWeight="700">
          <text x="180" y="1010">TODAY</text>
          <text x="790" y="1010">OVER TIME</text>
        </g>
      </svg>
      <div style={{ position: "absolute", bottom: 125, left: 80, right: 80, textAlign: "center", fontSize: 31, color: INK, fontWeight: 600 }}>
        You do not need to solve everything today. Make the next money decision count.
      </div>
    </AbsoluteFill>
  );
};

const Disclaimer: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: PAPER, justifyContent: "center", alignItems: "center", padding: 100, color: INK, fontFamily: "Arial, sans-serif", textAlign: "center" }}>
    <div style={{ fontSize: 54, fontWeight: 800, marginBottom: 35 }}>THE FINANCE CAMPUS</div>
    <div style={{ fontSize: 34, lineHeight: 1.4, maxWidth: 850 }}>
      Educational content only. This is not personalized financial, investment, tax or legal advice. Consult a qualified professional about your circumstances.
    </div>
    <div style={{ marginTop: 55, fontSize: 25 }}>VISUAL SAMPLE — NOT FOR PUBLICATION</div>
  </AbsoluteFill>
);

export const MonochromeFinanceStory: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: PAPER }}>
    <Sequence from={0} durationInFrames={900}><SceneOne /></Sequence>
    <Sequence from={900} durationInFrames={900}><SceneTwo /></Sequence>
    <Sequence from={1800} durationInFrames={900}><SceneThree /></Sequence>
    <Sequence from={2700} durationInFrames={900}><SceneFour /></Sequence>
    <Sequence from={3600} durationInFrames={720}><SceneFive /></Sequence>
    <Sequence from={4320} durationInFrames={180}><Disclaimer /></Sequence>
  </AbsoluteFill>
);

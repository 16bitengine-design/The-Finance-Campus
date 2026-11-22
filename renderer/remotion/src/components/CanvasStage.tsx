import React, { useEffect, useRef } from "react";
import { useCurrentFrame } from "remotion";

type Props = {
  width: number;
  height: number;
};

export const CanvasStage: React.FC<Props> = ({ width, height }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frame = useCurrentFrame();

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;

    context.clearRect(0, 0, width, height);
    const groundY = height * 0.78;
    context.fillStyle = "#FFFFFF";
    context.fillRect(0, 0, width, height);
    context.fillStyle = "#FFFFFF";
    context.fillRect(0, groundY, width, height - groundY);

    // Deterministic frame-based movement: safe for Remotion's out-of-order rendering.
    const progress = (frame % 120) / 120;
    const moneyX = width * (0.2 + progress * 0.6);
    const moneyY = height * 0.48 + Math.sin(progress * Math.PI * 2) * 18;

    context.save();
    context.translate(moneyX, moneyY);
    context.rotate(Math.sin(progress * Math.PI * 2) * 0.08);
    context.fillStyle = "#FFFFFF";
    context.strokeStyle = "#111111";
    context.lineWidth = 5;
    context.beginPath();
    context.roundRect(-58, -34, 116, 68, 12);
    context.fill();
    context.stroke();
    context.fillStyle = "#111111";
    context.font = "bold 44px Arial";
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText("$", 0, 1);
    context.restore();
  }, [frame, height, width]);

  return <canvas ref={canvasRef} width={width} height={height} />;
};

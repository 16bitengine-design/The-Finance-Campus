import React, { useEffect, useRef } from "react";
import rough from "roughjs";

type Props = {
  seed: number;
  className?: string;
};

export const RoughIllustration: React.FC<Props> = ({ seed, className }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const rc = rough.svg(svg);
    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const ink = "#102B55";
    const green = "#168C43";
    group.appendChild(rc.path("M 72 190 C 80 90 160 50 245 80 C 300 100 320 165 300 220", {
      seed, stroke: ink, strokeWidth: 5, roughness: 1.1, bowing: 1.2,
    }));
    group.appendChild(rc.rectangle(105, 130, 150, 105, {
      seed: seed + 1, stroke: green, strokeWidth: 4, roughness: 1.4,
      fill: "#E9F5EC", fillStyle: "hachure",
    }));
    group.appendChild(rc.line(125, 165, 235, 165, {
      seed: seed + 2, stroke: ink, strokeWidth: 3,
    }));
    group.appendChild(rc.line(125, 195, 210, 195, {
      seed: seed + 3, stroke: ink, strokeWidth: 3,
    }));
    svg.appendChild(group);
  }, [seed]);

  return <svg ref={svgRef} className={className} viewBox="0 0 380 300" />;
};

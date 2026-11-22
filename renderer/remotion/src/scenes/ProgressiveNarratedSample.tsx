import React from "react";
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame} from "remotion";

const P={ink:"#30231E",brown:"#704A35",caramel:"#A77B56",sand:"#D1B895",cream:"#E9DDC9",paper:"#F8F3EA",white:"#FFFDF8"};
const clamp={extrapolateLeft:"clamp" as const,extrapolateRight:"clamp" as const};

type Cue={start:number;end:number;text:string};
const ease=(f:number,a:number,b:number)=>interpolate(f,[a,b],[0,1],clamp);
const Bill:React.FC<{x:number;y:number;delay:number;label:string}> = ({x,y,delay,label})=>{
 const f=useCurrentFrame();const p=ease(f,delay,delay+22);const drift=interpolate(f,[delay,delay+22],[130,0],clamp);
 return <g opacity={p} transform={`translate(${x} ${y+drift}) rotate(${interpolate(f,[delay,delay+30],[8,0],clamp)})`}>
 <rect x="-88" y="-57" width="176" height="114" rx="12" fill={P.white} stroke={P.brown} strokeWidth="7"/>
 <rect x="-72" y="-41" width="144" height="82" rx="8" fill="none" stroke={P.sand} strokeWidth="4"/>
 <circle cx="-42" cy="0" r="19" fill={P.cream} stroke={P.brown} strokeWidth="4"/>
 <path d="M-51 0h18m-9-9v18M-5 -17h57M-5 0h43M-5 17h31" stroke={P.brown} strokeWidth="5" strokeLinecap="round"/>
 <text x="0" y="91" textAnchor="middle" fontSize="20" fontWeight="800" fill={P.ink}>{label}</text></g>
};
const Coin:React.FC<{x:number;y:number;delay:number;index:number}> = ({x,y,delay,index})=>{
 const f=useCurrentFrame();const p=ease(f,delay,delay+18);const drop=interpolate(f,[delay,delay+28],[y-260,y],clamp);
 return <g opacity={p} transform={`translate(${x} ${drop}) rotate(${f*2+index*22})`}><ellipse rx="29" ry="22" fill={P.caramel} stroke={P.ink} strokeWidth="5"/><ellipse rx="17" ry="12" fill="none" stroke={P.cream} strokeWidth="3"/></g>
};
const Person:React.FC<{worried:boolean;action:number}> = ({worried,action})=>{
 const f=useCurrentFrame();
 const step=Math.sin(f/7);
 const lean=interpolate(f,[action,action+24],[0,-9],clamp);
 const handY=interpolate(f,[action,action+24],[410,345],clamp)+Math.sin(f/9)*7;
 const armX=interpolate(f,[action,action+24],[105,205],clamp);
 const blink=(Math.floor(f/83)%5===0 && f%83<5);
 const eyeY=blink?164:158;
 return <g transform={"translate(245 "+(Math.sin(f/8)*3)+") scale(.78) rotate("+lean+" 0 390)"} stroke={P.ink} strokeWidth="10" strokeLinecap="round" strokeLinejoin="round">
 <ellipse cx="0" cy="735" rx="130" ry="20" fill={P.ink} opacity=".13" stroke="none"/>
 <path d={"M-48 555L-64 690Q-67 715-42 720L-5 720L18 "+(690+step*13)+"L35 570"} fill={P.ink}/>
 <path d={"M18 570L42 680Q48 704 78 704L116 704Q130 692 105 675L80 555"} fill={P.brown}/>
 <path d="M-58 710Q-102 708-112 733Q-116 750-88 752H-12Q4 740-5 722M78 700Q120 690 140 716Q150 739 125 746H48Q32 735 42 716" fill={P.ink}/>
 <path d="M-84 270Q-122 300-112 460L-92 574Q0 606 92 574L112 460Q122 300 76 270Z" fill={P.brown}/>
 <path d="M-54 292L0 345L54 292L39 535Q0 556-39 535Z" fill={P.cream} stroke="none"/>
 <path d="M-54 292L0 345L54 292M0 345V520" fill="none" stroke={P.caramel} strokeWidth="8"/>
 <path d="M-20 275L0 315L20 275" fill="none" stroke={P.white} strokeWidth="8"/>
 <path d="M-86 320Q-150 350-142 440L-110 480Q-86 490-76 462L-65 405" fill="none" stroke={P.brown} strokeWidth="34"/>
 <path d={"M78 320Q132 350 142 405L"+armX+" "+(handY-70)+"L"+(armX+16)+" "+(handY-18)} fill="none" stroke={P.brown} strokeWidth="34"/>
 <path d={"M"+(armX+16)+" "+(handY-18)+"q18 4 20 22q-2 18-20 20q-19-5-18-22q1-14 18-20"} fill={P.sand} stroke={P.ink} strokeWidth="8"/>
 <path d="M-24 250V282H24V250" fill={P.sand}/>
 <g transform="rotate(13 8 158)"><ellipse cx="8" cy="158" rx="88" ry="108" fill={P.sand}/>
 <path d="M-80 145Q-95 58-22 35Q58 15 96 100L90 143Q52 91 16 96Q-30 108-80 145Z" fill={P.ink}/>
 <path d="M-48 151q13-10 27 0m31 0q13-10 27 0" fill="none" stroke={P.ink} strokeWidth="7"/>
 <ellipse cx="-31" cy={eyeY} rx="7" ry={blink?2:10} fill={P.ink} stroke="none"/><ellipse cx="35" cy={eyeY} rx="7" ry={blink?2:10} fill={P.ink} stroke="none"/>
 <path d="M3 170l-13 20h18" fill="none" stroke={P.brown} strokeWidth="6"/>
 <path d={worried?"M-13 218q18-17 36 0":"M-15 210q18 18 38 0"} fill="none" stroke={P.brown} strokeWidth="7"/>
 <path d={worried?"M-52 130l25 8m25-8l25 8":"M-52 138l25-3m25-3l25 3"} fill="none" stroke={P.ink} strokeWidth="6"/></g></g>
};
const Room:React.FC=()=> {const f=useCurrentFrame();const reveal=ease(f,0,54);return <g opacity={reveal} transform={`translate(${(1-reveal)*-70} 0)`}>
 <path d="M80 90H1000V1110H80Z" fill={P.cream} stroke={P.brown} strokeWidth="8"/>
 <path d="M95 106H985V1094H95Z" fill="none" stroke={P.white} strokeWidth="3" opacity=".8"/>
 <ellipse cx="520" cy="790" rx="390" ry="34" fill={P.brown} opacity=".07" stroke="none"/>
 <path d="M120 130H460V410H120Z" fill={P.paper} stroke={P.brown} strokeWidth="8"/>
 <path d="M290 130V410M120 270H460" stroke={P.sand} strokeWidth="8"/>
 <path d="M120 800H960V850H120Z" fill={P.brown}/>
 <path d="M160 850V1050M920 850V1050" stroke={P.brown} strokeWidth="25"/>
 <rect x="700" y="180" width="210" height="330" rx="12" fill={P.sand} stroke={P.brown} strokeWidth="8"/>
 <path d="M735 225H875M735 270H875M735 315H875" stroke={P.brown} strokeWidth="9"/>
 </g>};
const Caption:React.FC<{cues:Cue[]}> = ({cues})=>{
 const f=useCurrentFrame();const sec=f/30;const cue=cues.find(c=>sec>=c.start&&sec<c.end);
 return cue?<div style={{position:"absolute",bottom:115,left:65,right:65,textAlign:"center",fontFamily:"Arial",fontSize:31,fontWeight:800,lineHeight:1.25,color:P.white,textShadow:"0 3px 8px #30231E",background:"rgba(48,35,30,.88)",padding:"18px 24px",borderRadius:18}}>{cue.text}</div>:null;
};
const Story:React.FC<{cues:Cue[];duration:number}> = ({cues,duration})=>{
 const f=useCurrentFrame();const sec=f/30;
 const phaseDuration=duration/5;const phase=Math.min(4,Math.floor(sec/phaseDuration));
 const phaseStart=phase*phaseDuration;const phaseFrames=phaseDuration*30;const phaseFrameStart=phaseStart*30;const worried=phase<3;
 const wallet=ease(f,phaseFrameStart+phaseFrames*.08,phaseFrameStart+phaseFrames*.22);
 const paid=ease(f,phaseFrameStart+phaseFrames*.43,phaseFrameStart+phaseFrames*.62);
 const saving=ease(f,phaseFrameStart+phaseFrames*.33,phaseFrameStart+phaseFrames*.52);
 const chart=ease(f,phaseFrameStart+phaseFrames*.26,phaseFrameStart+phaseFrames*.92);
 const title=["THE MONEY ARRIVES","THEN THE BILLS COME","MAKE A PLAN BEFORE SPENDING","MOVE SAVINGS FIRST","BUILD THE HABIT"][phase];
 const subtitle=["Your income deserves a plan","Watch where your money goes","Give every shilling a purpose","Small deposits still matter","Progress is built one decision at a time"][phase];
 return <AbsoluteFill style={{background:P.paper,fontFamily:"Arial"}}>
 <svg viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet" style={{position:"absolute",inset:0,width:"100%",height:"100%"}}>
 <defs><linearGradient id="warm" x1="0" x2="0" y1="0" y2="1"><stop stopColor={P.paper}/><stop offset="1" stopColor={P.cream}/></linearGradient></defs>
 <rect width="1080" height="1920" fill="url(#warm)"/>
 <g transform="translate(0 360)"><Room/><Person worried={phase===1} action={phaseFrameStart+phaseFrames*.12}/>
 {phase===0&&<g>
 <Person worried={false} action={phaseFrameStart+phaseFrames*.12}/>
 <g opacity={wallet}><rect x="600" y="650" width="240" height="130" rx="22" fill={P.brown}/><text x="720" y="705" textAnchor="middle" fontSize="22" fill={P.cream} fontWeight="800">SALARY RECEIVED</text><text x="720" y="752" textAnchor="middle" fontSize="35" fill={P.white} fontWeight="900">+ INCOME</text></g>
 <g><Bill x={560} y={570} delay={phaseFrameStart+phaseFrames*.20} label="INCOME"/><Bill x={805} y={570} delay={phaseFrameStart+phaseFrames*.34} label="INCOME"/><Bill x={560} y={830} delay={phaseFrameStart+phaseFrames*.48} label="INCOME"/><Bill x={805} y={830} delay={phaseFrameStart+phaseFrames*.62} label="INCOME"/></g><g transform="translate(685 385)"><rect x="-120" y="-48" width="240" height="92" rx="24" fill={P.brown} stroke={P.ink} strokeWidth="7"/><text y="8" textAnchor="middle" fontSize="27" fill={P.white} fontWeight="900">PAYDAY!</text></g>
 </g>}
 {phase===1&&<g><Person worried={true} action={phaseFrameStart+phaseFrames*.12}/>
 <Bill x={560} y={520} delay={phaseFrameStart+phaseFrames*.06} label="RENT"/><Bill x={810} y={650} delay={phaseFrameStart+phaseFrames*.28} label="POWER"/><Bill x={560} y={850} delay={phaseFrameStart+phaseFrames*.5} label="FOOD"/>
 <g opacity={paid}><path d="M470 600Q650 530 860 620" fill="none" stroke={P.caramel} strokeWidth="12" strokeDasharray="20 18"/><text x="660" y="555" fontSize="28" fontWeight="900" fill={P.ink}>PAYMENT LEAVES</text></g>
 </g>}
 {phase===2&&<g>
 {[0,1,2].map(i=><g key={i} transform={`translate(${530+i*185} 650)`}><rect x="-82" y="-105" width="164" height="235" rx="25" fill={[P.cream,P.sand,P.white][i]} stroke={P.brown} strokeWidth="8"/><text y="-55" textAnchor="middle" fontSize="20" fontWeight="900" fill={P.ink}>{["NEEDS","OBLIGATIONS","FUTURE YOU"][i]}</text><Bill x={0} y={30} delay={phaseFrameStart+phaseFrames*(.18+i*.2)} label="ALLOCATE"/></g>)}
 <path d="M710 410V510M530 510H900M530 510V545M715 510V545M900 510V545" fill="none" stroke={P.brown} strokeWidth="12" strokeLinecap="round"/>
 </g>}
 {phase===3&&<g><Person worried={false} action={phaseFrameStart+phaseFrames*.12}/>
 <path d="M600 600H850L820 930Q725 1010 630 930Z" fill={P.cream} stroke={P.brown} strokeWidth="12"/>
 <path d="M650 600V550H800V600" fill="none" stroke={P.brown} strokeWidth="14"/>
 {Array.from({length:12},(_,i)=><Coin key={i} x={650+(i%4)*48} y={720+Math.floor(i/4)*58} delay={phaseFrameStart+phaseFrames*(.12+i*.075)} index={i}/>)}
 <text x="720" y="1060" textAnchor="middle" fontSize="30" fontWeight="900" fill={P.ink}>SAVINGS BUFFER</text>
 </g>}
 {phase===4&&<g>
 <path d="M500 950V500M500 950H970" stroke={P.brown} strokeWidth="12" fill="none"/>
 <path d="M540 880L635 810L730 750L825 620L930 500" stroke={P.caramel} strokeWidth="22" fill="none" strokeLinecap="round" strokeDasharray="1" pathLength="1" strokeDashoffset={1-chart}/>
 {[0,1,2,3,4].map(i=><circle key={i} cx={540+i*97.5} cy={[880,810,750,620,500][i]} r="17" fill={P.brown} opacity={chart}/>)}
 <text x="735" y="1030" textAnchor="middle" fontSize="30" fontWeight="900" fill={P.ink}>CONSISTENCY OVER TIME</text>
 </g>}
 </g>
 </svg>
 <Caption cues={cues}/>
 {sec>=duration-8&&<AbsoluteFill style={{background:P.ink,justifyContent:"center",alignItems:"center",padding:90,textAlign:"center",color:P.paper,fontFamily:"Arial"}}><div style={{fontSize:48,fontWeight:900,letterSpacing:3}}>THE FINANCE CAMPUS</div><div style={{fontSize:31,lineHeight:1.45,marginTop:42}}>Educational content only. This is not personalized financial, investment, tax or legal advice. Consult a qualified professional about your circumstances.</div><div style={{fontSize:22,color:P.sand,marginTop:45,letterSpacing:3}}>SAMPLE · NOT FOR PUBLICATION</div></AbsoluteFill>}
 <Audio src={staticFile("sample-narration.wav")}/>
 </AbsoluteFill>
};
export const ProgressiveNarratedSample:React.FC<{cues:Cue[];duration:number}>=(props)=><Story {...props}/>;

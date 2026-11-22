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
 const f=useCurrentFrame();const bob=Math.sin(f/11)*3;const reach=ease(f,action,action+18);const enter=ease(f,Math.max(0,action-24),action+12);
 return <g opacity={enter} transform={`translate(180 ${bob+(1-enter)*90})`} stroke={P.ink} strokeWidth="9" strokeLinecap="round" strokeLinejoin="round">
 <ellipse cx="0" cy="650" rx="170" ry="24" fill={P.brown} opacity=".12" stroke="none"/>
 <path d="M-88 270Q-135 300-120 470L-100 570Q0 605 100 570L120 460Q120 310 78 270Z" fill={P.brown}/>
 <path d="M-58 292Q0 320 58 292L48 530Q0 554-48 530Z" fill={P.cream} stroke="none"/>
 <path d="M-70 560L-82 690Q-85 715-52 718H-4L0 585M12 585L24 700Q28 722 65 718L105 710Q116 700 94 680L70 560" fill={P.ink}/>
 <path d="M-85 705Q-130 700-142 728Q-150 748-120 754H-18Q0 740-12 720M70 708Q120 700 142 728Q150 748 120 754H20Q5 740 20 720" fill={P.brown}/>
 <path d={`M-88 315Q-160 340-150 445L-118 490Q-92 500-80 468M88 315Q150 340 150 ${410+reach*70}L115 ${450+reach*70}Q90 ${460+reach*70} 78 ${430+reach*70}`} fill="none" stroke={P.brown} strokeWidth="34"/>
 <path d="M-24 250V285H24V250" fill={P.sand}/>
 <ellipse cx="0" cy="160" rx="92" ry="112" fill={P.sand}/>
 <path d="M-92 150Q-104 55-28 34Q60 20 94 105L88 146Q54 88 22 95Q-30 110-92 150Z" fill={P.ink}/>
 <path d="M-62 153q14-12 29 0m34 0q14-12 29 0" fill="none" stroke={P.ink} strokeWidth="7"/>
 <ellipse cx="-34" cy="172" rx="8" ry="11" fill={P.ink} stroke="none"/><ellipse cx="34" cy="172" rx="8" ry="11" fill={P.ink} stroke="none"/>
 <path d={worried?"M-18 218q18-15 36 0":"M-18 207q18 17 36 0"} fill="none" stroke={P.brown} strokeWidth="7"/>
 <path d="M-5 182l-8 20h15" fill="none" stroke={P.brown} strokeWidth="5"/>
 </g>
};
const Room:React.FC=()=> {const f=useCurrentFrame();const reveal=ease(f,0,54);return <g opacity={reveal} transform={`translate(${(1-reveal)*-70} 0)`}>
 <path d="M80 90H1000V1110H80Z" fill={P.cream} stroke={P.brown} strokeWidth="8"/>
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
 <g transform="translate(0 360)"><Room/>
 {phase===0&&<g>
 <Person worried={false} action={phaseFrameStart+phaseFrames*.12}/>
 <g opacity={wallet}><rect x="600" y="650" width="240" height="130" rx="22" fill={P.brown}/><text x="720" y="705" textAnchor="middle" fontSize="22" fill={P.cream} fontWeight="800">SALARY RECEIVED</text><text x="720" y="752" textAnchor="middle" fontSize="35" fill={P.white} fontWeight="900">+ INCOME</text></g>
 <g>{[0,1,2,3].map(i=><g key={i} transform={`translate(${540+i*75} ${610-i*42})`}><Bill x={0} y={0} delay={phaseFrameStart+phaseFrames*(.2+i*.12)} label="INCOME"/></g>)}</g>
 </g>}
 {phase===1&&<g><Person worried={true} action={phaseFrameStart+phaseFrames*.12}/>
 <Bill x={540} y={510} delay={phaseFrameStart+phaseFrames*.06} label="RENT"/><Bill x={760} y={650} delay={phaseFrameStart+phaseFrames*.28} label="POWER"/><Bill x={330} y={690} delay={phaseFrameStart+phaseFrames*.5} label="FOOD"/>
 <g opacity={paid}><path d="M470 600Q650 530 860 620" fill="none" stroke={P.caramel} strokeWidth="12" strokeDasharray="20 18"/><text x="660" y="555" fontSize="28" fontWeight="900" fill={P.ink}>PAYMENT LEAVES</text></g>
 </g>}
 {phase===2&&<g><Person worried={false} action={phaseFrameStart+phaseFrames*.12}/>
 {[0,1,2].map(i=><g key={i} transform={`translate(${220+i*320} 650)`}><rect x="-125" y="-105" width="250" height="235" rx="25" fill={[P.cream,P.sand,P.white][i]} stroke={P.brown} strokeWidth="8"/><text y="-55" textAnchor="middle" fontSize="26" fontWeight="900" fill={P.ink}>{["NEEDS","OBLIGATIONS","FUTURE YOU"][i]}</text><Bill x={0} y={30} delay={phaseFrameStart+phaseFrames*(.18+i*.2)} label="ALLOCATE"/></g>)}
 <path d="M540 410V510M220 510H860M220 510V545M540 510V545M860 510V545" fill="none" stroke={P.brown} strokeWidth="12" strokeLinecap="round"/>
 </g>}
 {phase===3&&<g><Person worried={false} action={phaseFrameStart+phaseFrames*.12}/>
 <path d="M600 600H850L820 930Q725 1010 630 930Z" fill={P.cream} stroke={P.brown} strokeWidth="12"/>
 <path d="M650 600V550H800V600" fill="none" stroke={P.brown} strokeWidth="14"/>
 {Array.from({length:12},(_,i)=><Coin key={i} x={650+(i%4)*48} y={720+Math.floor(i/4)*58} delay={phaseFrameStart+phaseFrames*(.12+i*.075)} index={i}/>)}
 <text x="720" y="1060" textAnchor="middle" fontSize="30" fontWeight="900" fill={P.ink}>SAVINGS BUFFER</text>
 </g>}
 {phase===4&&<g><Person worried={false} action={phaseFrameStart+phaseFrames*.12}/>
 <path d="M240 950V500M240 950H900" stroke={P.brown} strokeWidth="12" fill="none"/>
 <path d="M280 880L410 810L540 750L670 620L820 500" stroke={P.caramel} strokeWidth="22" fill="none" strokeLinecap="round" strokeDasharray="1" pathLength="1" strokeDashoffset={1-chart}/>
 {[0,1,2,3,4].map(i=><circle key={i} cx={280+i*135} cy={[880,810,750,620,500][i]} r="17" fill={P.brown} opacity={chart}/>)}
 <text x="565" y="1030" textAnchor="middle" fontSize="30" fontWeight="900" fill={P.ink}>CONSISTENCY OVER TIME</text>
 </g>}
 </g>
 </svg>
 <Caption cues={cues}/>
 {sec>=duration-8&&<AbsoluteFill style={{background:P.ink,justifyContent:"center",alignItems:"center",padding:90,textAlign:"center",color:P.paper,fontFamily:"Arial"}}><div style={{fontSize:48,fontWeight:900,letterSpacing:3}}>THE FINANCE CAMPUS</div><div style={{fontSize:31,lineHeight:1.45,marginTop:42}}>Educational content only. This is not personalized financial, investment, tax or legal advice. Consult a qualified professional about your circumstances.</div><div style={{fontSize:22,color:P.sand,marginTop:45,letterSpacing:3}}>SAMPLE · NOT FOR PUBLICATION</div></AbsoluteFill>}
 <Audio src={staticFile("sample-narration.wav")}/>
 </AbsoluteFill>
};
export const ProgressiveNarratedSample:React.FC<{cues:Cue[];duration:number}>=(props)=><Story {...props}/>;

import React from "react";
import {AbsoluteFill, Sequence, interpolate, useCurrentFrame} from "remotion";

const C={ink:"#30231E",dark:"#211713",brown:"#704A35",caramel:"#A77B56",sand:"#D1B895",cream:"#E9DDC9",paper:"#F8F3EA",white:"#FFFDF8"};
const clamp={extrapolateLeft:"clamp" as const,extrapolateRight:"clamp" as const};
const p=(f:number,a:number,b:number)=>interpolate(f,[a,b],[0,1],clamp);

const Room:React.FC<{variant:number}> = ({variant}) => <g>
 <rect width="1080" height="1920" fill={C.paper}/>
 <path d="M0 0H1080V1250H0Z" fill={variant%2?C.cream:C.paper}/>
 <path d="M70 110H1010V1270H70Z" fill="none" stroke={C.sand} strokeWidth="9"/>
 {[150,610].map((x,i)=><g key={x} transform={`translate(${x} 170)`}>
  <path d="M0 650V155Q0 0 175 0Q350 0 350 155V650Z" fill={C.white} stroke={C.brown} strokeWidth="14"/>
  <path d="M175 0V650M0 325H350M60 80L175 180L290 80" fill="none" stroke={C.sand} strokeWidth="13"/>
  <path d="M0 155Q0 0 175 0Q350 0 350 155" fill="none" stroke={C.caramel} strokeWidth="8"/>
 </g>)}
 <path d="M0 1260H1080V1920H0Z" fill={C.dark}/>
 <path d="M0 1260Q540 1200 1080 1260" fill="none" stroke={C.caramel} strokeWidth="14"/>
 <g opacity=".55"><path d="M100 0V1250M980 0V1250" stroke={C.brown} strokeWidth="8"/></g>
</g>;

const Character:React.FC<{x:number;y:number;scale?:number;woman?:boolean;worried?:boolean;reach?:number;relieved?:boolean}> = ({x,y,scale=1,woman=false,worried=true,reach=0,relieved=false})=>{
 const f=useCurrentFrame();const bob=Math.sin(f/11+(woman?1:0))*3;const armY=interpolate(f,[reach,reach+28],[420,315],clamp);
 return <g transform={`translate(${x} ${y+bob}) scale(${scale})`} stroke={C.ink} strokeWidth="10" strokeLinecap="round" strokeLinejoin="round">
  <ellipse cx="0" cy="745" rx="150" ry="25" fill={C.ink} opacity=".18" stroke="none"/>
  <path d="M-88 300Q-145 335-132 500L-115 640Q0 685 115 640L132 500Q145 335 88 300Z" fill={woman?C.dark:C.brown}/>
  <path d="M-58 325L0 390L58 325L42 610Q0 635-42 610Z" fill={C.cream} stroke="none"/>
  <path d="M-58 325L0 390L58 325M0 390V590" fill="none" stroke={C.caramel} strokeWidth="8"/>
  <path d="M-68 625L-85 715Q-90 745-58 750H-10L8 650M15 650L40 735Q45 755 78 750L115 740Q125 725 100 700L80 625" fill={C.ink}/>
  <path d="M-90 360Q-150 405-140 495L-112 535Q-90 545-78 515L-64 450" fill="none" stroke={woman?C.dark:C.brown} strokeWidth="36"/>
  <path d={`M88 360Q150 390 150 ${armY}L205 ${armY+35}`} fill="none" stroke={woman?C.dark:C.brown} strokeWidth="36"/>
  <path d={`M190 ${armY+25}q26 -18 43 4q12 20-9 37q-24 11-39-9q-8-18 5-32`} fill={C.sand} strokeWidth="8"/>
  <path d="M-22 270V310H22V270" fill={C.sand}/>
  <ellipse cx="0" cy="170" rx="105" ry="125" fill={C.sand}/>
  {woman?<path d="M-108 170Q-130 45-32 20Q65 -15 112 85L110 205Q90 125 52 115Q-18 105-108 170Z" fill={C.dark}/>:<path d="M-102 155Q-110 45-35 24Q58 -5 104 85L95 150Q50 100 12 110Q-42 122-102 155Z" fill={C.dark}/>}
  {woman&&<path d="M-105 135Q-160 225-115 330L-80 350L-90 205M100 130Q150 220 115 320L80 340L90 205" fill={C.dark}/>}
  <path d={worried?"M-62 142Q-38 119-15 140M15 140Q38 119 62 142":"M-62 145Q-38 155-15 145M15 145Q38 155 62 145"} fill="none" stroke={C.ink} strokeWidth="8"/>
  <ellipse cx="-38" cy="178" rx="10" ry="14" fill={C.ink} stroke="none"/><ellipse cx="38" cy="178" rx="10" ry="14" fill={C.ink} stroke="none"/>
  <path d={worried?"M-19 230Q0 208 19 230":relieved?"M-22 215Q0 245 22 215":"M-20 225Q0 235 20 225"} fill="none" stroke={C.brown} strokeWidth="8"/>
  {worried&&<path d="M-90 190q-18 24 0 35" fill="none" stroke={C.white} strokeWidth="7"/>}
 </g>
};

const MoneyNote:React.FC<{x:number;y:number;delay:number;label:string}> = ({x,y,delay,label})=>{
 const f=useCurrentFrame();const a=p(f,delay,delay+24);const dy=interpolate(f,[delay,delay+24],[120,0],clamp);
 return <g opacity={a} transform={`translate(${x} ${y+dy}) rotate(-9)`}>
  <rect x="-110" y="-66" width="220" height="132" rx="12" fill={C.cream} stroke={C.brown} strokeWidth="8"/>
  <rect x="-91" y="-48" width="182" height="96" rx="8" fill="none" stroke={C.sand} strokeWidth="5"/>
  <circle r="30" fill={C.sand} stroke={C.brown} strokeWidth="5"/>
  <path d="M-65 -20H-42M42 20H65" stroke={C.brown} strokeWidth="6"/>
  <text x="0" y="11" textAnchor="middle" fontSize="31" fontWeight="900" fill={C.brown}>£</text>
  <text x="0" y="104" textAnchor="middle" fontSize="23" fontWeight="900" fill={C.cream}>{label}</text>
 </g>
};

const StoryScene:React.FC<{phase:number}> = ({phase})=>{
 const f=useCurrentFrame();const base=0;const local=f;const reveal=p(local,0,48);
 const title=["THE PAYDAY CONVERSATION","WHEN THE BILLS ARRIVE","A CHOICE HAS CONSEQUENCES","A BETTER PLAN","SMALL STEPS, REAL PROGRESS"][phase];
 const captions=["A family has worked hard for this income.","But the bills are already waiting.","Every decision sends money somewhere.","They decide to protect a little for tomorrow.","The goal is progress, not perfection."][phase];
 const [x1,x2]=phase===0?[300,790]:phase===1?[300,790]:phase===2?[330,760]:phase===3?[320,760]:[300,790];
 return <AbsoluteFill>
  <svg viewBox="0 0 1080 1920" style={{position:"absolute",inset:0,width:"100%",height:"100%"}}>
   <Room variant={phase}/>
   <g opacity={reveal}>
    <path d="M95 1230H985" stroke={C.brown} strokeWidth="18"/>
    <path d="M145 1230V1530M935 1230V1530" stroke={C.brown} strokeWidth="22"/>
    <rect x="105" y="1160" width="870" height="85" rx="18" fill={C.caramel} stroke={C.ink} strokeWidth="9"/>
   </g>
   <Character x={x1} y={phase===4?640:590} scale={.82} worried={phase<3} relieved={phase===4} reach={base+180}/>
   <Character x={x2} y={phase===4?630:590} scale={.82} woman worried={phase===1||phase===2} relieved={phase>=3} reach={base+340}/>
   {phase===0&&<g>
    <MoneyNote x={530} y={1060} delay={base+85} label="PAYDAY"/>
    <g opacity={p(local,180,235)}><path d="M450 1040Q390 970 335 945M630 1040Q700 970 755 945" fill="none" stroke={C.caramel} strokeWidth="12" strokeDasharray="18 14"/></g>
   </g>}
   {phase===1&&<g>
    <MoneyNote x={520} y={990} delay={base+50} label="RENT"/>
    <MoneyNote x={720} y={1080} delay={base+210} label="UTILITIES"/>
    <MoneyNote x={365} y={1080} delay={base+360} label="FOOD"/>
    <g opacity={p(local,430,490)}><path d="M515 1090Q700 1200 830 1330" fill="none" stroke={C.brown} strokeWidth="13" strokeDasharray="16 13"/></g>
   </g>}
   {phase===2&&<g>
    <rect x="380" y="960" width="320" height="170" rx="20" fill={C.cream} stroke={C.brown} strokeWidth="10"/>
    <text x="540" y="1030" textAnchor="middle" fontSize="30" fontWeight="900" fill={C.ink}>ONE DECISION</text>
    <text x="540" y="1080" textAnchor="middle" fontSize="25" fontWeight="700" fill={C.brown}>TODAY OR TOMORROW?</text>
    <path d="M540 1130V1280M540 1280L330 1390M540 1280L750 1390" fill="none" stroke={C.caramel} strokeWidth="12" strokeLinecap="round"/>
    <MoneyNote x={330} y={1450} delay={base+250} label="SPENDING"/>
    <MoneyNote x={750} y={1450} delay={base+430} label="SAVING"/>
   </g>}
   {phase===3&&<g>
    <rect x="630" y="970" width="240" height="290" rx="30" fill={C.cream} stroke={C.brown} strokeWidth="12"/>
    <path d="M680 970V910H820V970" fill="none" stroke={C.brown} strokeWidth="14"/>
    <text x="750" y="1100" textAnchor="middle" fontSize="29" fontWeight="900" fill={C.ink}>SAVINGS</text>
    {[0,1,2,3,4].map(i=><g key={i} opacity={p(local,200+i*70,235+i*70)} transform={`translate(${680+(i%3)*48} ${1180-Math.floor(i/3)*48})`}><circle r="20" fill={C.caramel} stroke={C.brown} strokeWidth="5"/></g>)}
   </g>}
   {phase===4&&<g>
    <path d="M300 1450V980M300 1450H880" stroke={C.brown} strokeWidth="13" fill="none"/>
    <path d="M350 1390L470 1310L590 1260L710 1130L830 1030" fill="none" stroke={C.caramel} strokeWidth="22" strokeLinecap="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1-p(local,90,650)}/>
    {[0,1,2,3,4].map(i=><circle key={i} cx={350+i*120} cy={[1390,1310,1260,1130,1030][i]} r="17" fill={C.brown} opacity={p(local,100+i*110,145+i*110)}/>)}
   </g>}
   <g opacity={p(local,10,45)}>
    <text x="540" y="175" textAnchor="middle" fontSize="29" fontWeight="900" letterSpacing="5" fill={C.brown}>THE FINANCE CAMPUS</text>
    <text x="540" y="275" textAnchor="middle" fontSize="51" fontWeight="900" fill={C.ink}>{title}</text>
   </g>
  </svg>
  <div style={{position:"absolute",bottom:180,left:70,right:70,background:"rgba(33,23,19,.88)",color:C.white,borderRadius:22,padding:"25px 30px",textAlign:"center",fontFamily:"Arial",fontSize:31,fontWeight:700,lineHeight:1.3}}>{captions}</div>
 </AbsoluteFill>
};

export const CinematicCartoonStory:React.FC=()=>{
 const f=useCurrentFrame();const phase=Math.min(4,Math.floor(f/900));
 return <AbsoluteFill style={{background:C.paper}}>
  <Sequence from={0} durationInFrames={900}><StoryScene phase={0}/></Sequence>
  <Sequence from={900} durationInFrames={900}><StoryScene phase={1}/></Sequence>
  <Sequence from={1800} durationInFrames={900}><StoryScene phase={2}/></Sequence>
  <Sequence from={2700} durationInFrames={900}><StoryScene phase={3}/></Sequence>
  <Sequence from={3600} durationInFrames={900}><StoryScene phase={4}/></Sequence>
  {f>=4380&&<AbsoluteFill style={{background:C.dark,justifyContent:"center",alignItems:"center",padding:100,textAlign:"center",color:C.paper,fontFamily:"Arial"}}>
   <div style={{fontSize:54,fontWeight:900,letterSpacing:3}}>THE FINANCE CAMPUS</div>
   <div style={{fontSize:34,lineHeight:1.5,marginTop:50}}>Educational content only. This is not personalized financial, investment, tax or legal advice. Consult a qualified professional about your circumstances.</div>
   <div style={{fontSize:24,color:C.sand,marginTop:55,letterSpacing:3}}>VISUAL STYLE TEST · NOT FOR PUBLICATION</div>
  </AbsoluteFill>}
 </AbsoluteFill>
};

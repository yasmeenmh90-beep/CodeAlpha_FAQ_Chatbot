import { useEffect, useRef, useState } from 'react'
import { Mic, Square, Volume2, Send, AudioLines } from 'lucide-react'
type Recognition = {lang:string; interimResults:boolean; onresult:((e:{results:ArrayLike<{isFinal:boolean;0:{transcript:string}}>})=>void)|null; onend:(()=>void)|null; onerror:(()=>void)|null; start:()=>void; abort:()=>void}
type Props = {send:(text:string)=>Promise<void>; answer:string; loading:boolean; speak:(text:string)=>void; rate:number; setRate:(n:number)=>void; voices:SpeechSynthesisVoice[]; voiceName:string; setVoiceName:(s:string)=>void}
export default function VoiceStudio({send,answer,loading,speak,rate,setRate,voices,voiceName,setVoiceName}:Props){
 const [draft,setDraft]=useState(''),[status,setStatus]=useState('Idle'),[language,setLanguage]=useState('en-US'),[bars,setBars]=useState<number[]>(Array(32).fill(0)),[auto,setAuto]=useState(false)
 const recognition=useRef<Recognition|null>(null),stream=useRef<MediaStream|null>(null),ctx=useRef<AudioContext|null>(null),frame=useRef(0),generation=useRef(0),previous=useRef(answer)
 function release(){generation.current++;cancelAnimationFrame(frame.current);stream.current?.getTracks().forEach(t=>t.stop());stream.current=null;void ctx.current?.close().catch(()=>{});ctx.current=null;if(recognition.current){recognition.current.onend=null;recognition.current.onerror=null;recognition.current.onresult=null;recognition.current.abort();recognition.current=null}}
 useEffect(()=>()=>{release();window.speechSynthesis?.cancel()},[])
 useEffect(()=>{if(answer!==previous.current){previous.current=answer;if(auto&&answer)speak(answer)}},[answer,auto,speak])
 function stop(){release();setBars(Array(32).fill(0));setStatus('Idle')}
 async function start(){
  release();window.speechSynthesis?.cancel();const ticket=generation.current
  const w=window as unknown as {SpeechRecognition?:new()=>Recognition;webkitSpeechRecognition?:new()=>Recognition}
  const C=w.SpeechRecognition||w.webkitSpeechRecognition
  if(!C){setStatus('Speech recognition unavailable. Use text input.');return}
  setStatus('Requesting microphone')
  try{
   const media=await navigator.mediaDevices.getUserMedia({audio:true})
   if(ticket!==generation.current){media.getTracks().forEach(t=>t.stop());return}
   stream.current=media;const audio=new AudioContext();ctx.current=audio;const analyser=audio.createAnalyser();analyser.fftSize=256;audio.createMediaStreamSource(media).connect(analyser);const data=new Uint8Array(analyser.frequencyBinCount)
   const draw=()=>{analyser.getByteFrequencyData(data);setBars(Array.from({length:32},(_,i)=>data[i*3]/255));frame.current=requestAnimationFrame(draw)};draw()
   const rec=new C();recognition.current=rec;rec.lang=language;rec.interimResults=true
   rec.onresult=e=>setDraft(Array.from(e.results).map(r=>r[0].transcript).join(' ').slice(0,1500))
   rec.onend=stop;rec.onerror=()=>{stop();setStatus('Recognition interrupted. Try again or type.')};rec.start();setStatus('Listening')
  }catch{stop();setStatus('Microphone unavailable or permission denied')}
 }
 return <section className="library voiceStudio"><div className="eyebrow"><AudioLines size={16}/> AUDIO INTELLIGENCE</div><h1>Voice Studio</h1><p>Speak naturally. Review your transcript before sending.</p><div className="vsGrid"><article className="vsCore"><small>{loading?'Retrieving answer':status}</small><div className={'vsOrb '+(status==='Listening'?'live':'')}><Mic size={48}/></div><div className="vsWave" aria-label="Live microphone frequency levels">{bars.map((n,i)=><i key={i} style={{height:4+n*68}}/>)}</div><div className="vsActions"><button disabled={loading||status==='Listening'||status==='Requesting microphone'} onClick={()=>void start()}><Mic size={17}/> Start microphone</button><button onClick={stop}><Square size={16}/> Stop</button></div><small>Microphone audio is measured locally; browser recognition may use external services.</small></article><article className="vsControls"><h2>Voice preferences</h2><label>Recognition language<select value={language} onChange={e=>setLanguage(e.target.value)}><option value="en-US">English</option><option value="fr-FR">French</option><option value="ur-PK">Urdu</option><option value="ar-AE">Arabic</option></select></label><label>Playback voice<select value={voiceName} onChange={e=>setVoiceName(e.target.value)}><option value="">System default</option>{voices.map(v=><option key={v.name} value={v.name}>{v.name}</option>)}</select></label><label>Playback speed · {rate}×<input type="range" min=".7" max="1.5" step=".1" value={rate} onChange={e=>setRate(Number(e.target.value))}/></label><label className="vsCheck"><input type="checkbox" checked={auto} onChange={e=>setAuto(e.target.checked)}/> Read new answers aloud</label><small>Answers retain their knowledge-base language.</small></article><article className="vsTranscript"><h2>Live transcript</h2><form onSubmit={e=>{e.preventDefault();if(!draft.trim()||loading)return;stop();void send(draft.trim());setDraft('')}}><textarea aria-label="Transcript" value={draft} maxLength={1500} onChange={e=>setDraft(e.target.value)} placeholder="Speak or type your question…"/><button disabled={!draft.trim()||loading}><Send size={16}/> Ask QueryMind</button></form></article><article className="vsAnswer"><h2>Latest answer</h2><p>{answer||'Your answer will appear here.'}</p><div className="vsActions"><button disabled={!answer||loading} onClick={()=>{stop();speak(answer)}}><Volume2 size={16}/> Play answer</button><button onClick={()=>window.speechSynthesis?.cancel()}><Square size={16}/> Stop audio</button></div></article></div></section>
}

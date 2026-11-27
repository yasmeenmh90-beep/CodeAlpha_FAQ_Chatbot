import VoiceStudio from './VoiceStudio'
import KnowledgeAdmin from './KnowledgeAdmin'
import Analytics from './Analytics'
import { useEffect, useRef, useState } from 'react'
import { ArrowRight, Bot, Check, ChevronDown, CircleHelp, Command, Github, Lightbulb, Menu, MessageCircle, Plus, Send, ShieldCheck, Sparkles, Copy, Mic, Volume2, Moon, Sun, Download, ThumbsUp, ThumbsDown, X, UserRound, CreditCard, Package, Headphones, LayoutGrid, Search, RefreshCw, Activity, BarChart3, Maximize2, Minimize2, Trash2, Pencil, Square } from 'lucide-react'

type FAQ = { id: number; question: string; category: string }
type Reply = { answer: string; matched_question: string | null; confidence: number; matched: boolean; category: string | null; suggestions: string[] }
type Session = { id: number; title: string; messages: Message[] }
type Message = { latency?: number; id: number; role: 'user' | 'assistant'; text: string; match?: Reply }
const API = import.meta.env.VITE_API_URL || ''
const welcome: Message = { id: 0, role: 'assistant', text: "Welcome to QueryMind. I can help with account access, billing, orders and technical support. What can I help you with today?" }
const starters = ['How do I reset my password?', 'How do I track my order?', 'What payment methods are accepted?', 'How do I contact support?']

export default function App() {
  const [messages, setMessages] = useState<Message[]>(() => { try { return JSON.parse(localStorage.getItem('qm-chat') || 'null') || [welcome] } catch { return [welcome] } })
  const [sessions, setSessions] = useState<Session[]>(() => { try { return JSON.parse(localStorage.getItem('qm-sessions') || '[]') } catch { return [] } })
  const [activeId, setActiveId] = useState(() => Number(localStorage.getItem('qm-active') || Date.now()))
  const [historySearch, setHistorySearch] = useState('')
  const [studio, setStudio] = useState(false)
  const [analytics, setAnalytics] = useState(false)
  const [adminOpen,setAdminOpen] = useState(false)
  const [insights, setInsights] = useState(true)
  const [selectedReply, setSelectedReply] = useState<number | null>(null)
  const [expanded, setExpanded] = useState(false)
  const [rate, setRate] = useState(1)
  const [voiceName, setVoiceName] = useState('')
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([])
  useEffect(() => { if (!('speechSynthesis' in window)) return; const sync = () => setVoices(speechSynthesis.getVoices()); sync(); speechSynthesis.addEventListener('voiceschanged',sync); return () => speechSynthesis.removeEventListener('voiceschanged',sync) }, [])
  useEffect(() => { localStorage.setItem('qm-sessions', JSON.stringify(sessions)); localStorage.setItem('qm-active',String(activeId)) }, [sessions,activeId])
  function saveCurrent() { if (messages.length > 1) setSessions(prev => [...prev.filter(x => x.id !== activeId), { id: activeId, title: prev.find(x => x.id === activeId)?.title || messages.find(x => x.role === 'user')?.text.slice(0,50) || 'Conversation', messages }]) }
  function openSession(session: Session) { if (loading) return; setStudio(false); setAdminOpen(false); saveCurrent(); setActiveId(session.id); setMessages(session.messages); setAnalytics(false); setShowFaqs(false); setMenu(false) }
  const [light, setLight] = useState(() => localStorage.getItem('qm-theme') === 'light')
  const [feedback, setFeedback] = useState<Record<number, string>>(() => { try { return JSON.parse(localStorage.getItem("qm-feedback") || "{}") } catch { return {} } })
  useEffect(() => { localStorage.setItem("qm-feedback", JSON.stringify(feedback)) }, [feedback])
  const [listening, setListening] = useState(false)
  useEffect(() => { localStorage.setItem('qm-chat', JSON.stringify(messages)) }, [messages])
  useEffect(() => { localStorage.setItem('qm-theme', light ? 'light' : 'dark') }, [light])
  function speak(text: string) { if ('speechSynthesis' in window) { speechSynthesis.cancel(); const utterance = new SpeechSynthesisUtterance(text); utterance.rate = rate; utterance.voice = voices.find(v => v.name === voiceName) || null; speechSynthesis.speak(utterance) } }
  function download() { const url = URL.createObjectURL(new Blob([messages.map(m => m.role + ': ' + m.text).join('\n\n')], { type: 'text/plain' })); const a = document.createElement('a'); a.href = url; a.download = 'querymind-conversation.txt'; a.click(); URL.revokeObjectURL(url) }
  function voice() {
    type Recognition = { lang: string; onresult: (e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void; onend: () => void; onerror: () => void; start: () => void }
    const w = window as unknown as { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition }
    const RecognitionClass = w.SpeechRecognition || w.webkitSpeechRecognition
    if (!RecognitionClass) { setError('Voice input is not supported in this browser.'); return }
    const recognition = new RecognitionClass(); recognition.lang = 'en-US'
    recognition.onresult = e => setInput(e.results[0][0].transcript)
    recognition.onend = () => setListening(false)
    recognition.onerror = () => { setListening(false); setError('Microphone unavailable or permission denied.') }
    try { recognition.start(); setListening(true) } catch { setError('Unable to start microphone.') }
  }
  const [input, setInput] = useState('')
  const [apiStatus, setApiStatus] = useState<'loading' | 'ready' | 'offline'>('loading')
  const [refresh, setRefresh] = useState(0)
  const [faqs, setFaqs] = useState<FAQ[]>([])
  const [category, setCategory] = useState('all')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [menu, setMenu] = useState(false)
  const [showFaqs, setShowFaqs] = useState(false)
  const [search, setSearch] = useState('')
  const [copied, setCopied] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const [voiceOpen, setVoiceOpen] = useState(false)
  const [promptsOpen, setPromptsOpen] = useState(true)
  useEffect(() => {
    fetch(`${API}/api/faqs`).then(r => { if (!r.ok) throw new Error('Unable to load FAQs'); return r.json() })
      .then(d => { setFaqs(d.faqs); setApiStatus('ready'); setError('') }).catch(() => { setApiStatus('offline'); setError('Backend is offline. Start the API to enable real answers.') })
  }, [refresh])
  useEffect(() => { const el = scrollRef.current; if (el) el.scrollTop = el.scrollHeight }, [messages, loading, showFaqs, analytics])
  const categories = Array.from(new Set(['all','account','billing','orders','support', ...faqs.map(f => f.category)]))
  const topicName = category === 'all' ? 'All topics' : category[0].toUpperCase() + category.slice(1)
  const topicIcons: Record<string, typeof Bot> = { all: LayoutGrid, account: UserRound, billing: CreditCard, orders: Package, support: Headphones }
  const prompts = category === 'all' ? starters : faqs.filter(f => f.category === category).slice(0,4).map(f => f.question)
  function openTopic(cat: string) { setStudio(false); setAdminOpen(false); setCategory(cat); setSearch(''); setShowFaqs(true); setAnalytics(false); setMenu(false) }
  async function send(message = input, topic = category) {
    const text = message.trim()
    if (!text || loading || text.length > 1500) return
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', text }])
    setInput('')
    const started = performance.now()
    setLoading(true)
    setError('')
    try {
      const response = await fetch(`${API}/api/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text, category: topic }) })
      if (!response.ok) throw new Error('The service could not process your request.')
      const result: Reply = await response.json()
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', text: result.answer, match: result, latency: Math.round(performance.now()-started) }])
    } catch {
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', text: 'Connection error — please check that the FAQ backend is running and try again.' }])
      setError('Connection to the API failed.')
    } finally { setLoading(false) }
  }
  function clearChat() { if (loading) return; saveCurrent(); setActiveId(Date.now()); setMessages([welcome]); setError(''); setMenu(false) }
  const filtered = faqs.filter(f => (category === 'all' || f.category === category) && f.question.toLowerCase().includes(search.toLowerCase()))
  const answered = messages.filter(m => m.role === 'assistant' && m.match?.matched).length
  const attempts = messages.filter(m => m.role === 'user').length
  const allMessages = [...sessions.filter(s => s.id !== activeId).flatMap(s => s.messages), ...messages]
  const inspected = messages.find(m=>m.id===selectedReply && m.match) || [...messages].reverse().find(m=>m.match)
  return <div className={`shell ${light ? "light" : ""} ${expanded ? "expanded" : ""}`}>
    <aside className={`sidebar ${menu ? 'open' : ''}`}>
      <div className="brand"><div className="brandIcon"><Sparkles size={21}/></div><div><strong>querymind<span>.ai</span></strong><small>INTELLIGENT SUPPORT</small></div><button className="iconButton mobileClose" aria-label="Close menu" onClick={() => setMenu(false)}><X size={18}/></button></div>
      <div className="sidebarGroup"><div className="sideLabel">WORKSPACE</div><button className={`navItem ${!showFaqs && !studio && !adminOpen && !analytics ? "active" : ""}`} onClick={() => { setStudio(false); setAdminOpen(false); setAnalytics(false); setShowFaqs(false); setCategory('all'); setMenu(false) }}><MessageCircle size={18}/> AI Assistant <span className="navPill">LIVE</span></button><button className={`navItem ${showFaqs ? "active" : ""}`} onClick={() => { openTopic('all') }}><CircleHelp size={18}/> FAQ Library <span className="count">{faqs.length}</span></button><button className={`navItem ${studio?"active":""}`} onClick={()=>{setStudio(true);setAdminOpen(false);setAnalytics(false);setShowFaqs(false);setMenu(false)}}><Mic size={18}/> Voice Studio</button></div>
      <div className="sidebarGroup"><div className="sideLabel">TOPICS</div>{categories.map(cat => <button key={cat} className={`navItem topic ${category === cat ? 'selected' : ''}`} aria-pressed={showFaqs && category === cat} onClick={() => openTopic(cat)}>{(() => { const Icon = topicIcons[cat] || CircleHelp; return <Icon size={16}/> })()}{cat === 'all' ? 'All topics' : cat[0].toUpperCase() + cat.slice(1)}<span className="topicCount">{faqs.filter(f => cat === 'all' || f.category === cat).length}</span>{showFaqs && category === cat && <Check size={15}/>}</button>)}</div>
      <div className="sidebarGroup"><div className="sideLabel">INSIGHTS</div><button className="navItem" onClick={()=>{setStudio(false);setAdminOpen(true);setMenu(false)}}><ShieldCheck size={17}/> Knowledge Studio</button><button className="navItem" onClick={() => { setStudio(false);setAdminOpen(false);setAnalytics(true); setMenu(false) }}><BarChart3 size={17}/> Analytics</button><div className="sideLabel">CHAT HISTORY</div><button className="navItem" disabled={loading} onClick={() => { clearChat();setStudio(false);setAdminOpen(false); setAnalytics(false); setShowFaqs(false) }}><Plus size={16}/> New chat</button><input className="historySearch" placeholder="Search saved chats" aria-label="Search saved chats" value={historySearch} onChange={e => setHistorySearch(e.target.value)}/>{sessions.filter(s => s.title.toLowerCase().includes(historySearch.toLowerCase())).map(s => <div className="historyRow" key={s.id}><button disabled={loading} onClick={() => openSession(s)}>{s.title}</button><button aria-label="Rename chat" onClick={() => { const title = window.prompt('Conversation name',s.title); if(title?.trim()) setSessions(prev => prev.map(x => x.id === s.id ? {...x,title:title.trim().slice(0,80)} : x)) }}><Pencil size={12}/></button><button aria-label="Delete saved chat" disabled={loading} onClick={() => { if(window.confirm('Delete saved conversation?')) setSessions(prev => prev.filter(x => x.id !== s.id)) }}><Trash2 size={12}/></button></div>)}</div><div className="sidebarBottom"><div className="miniCard"><div className="miniBadge"><Lightbulb size={14}/> ABOUT THIS WORKSPACE</div><p>Answers are retrieved from a curated demonstration knowledge base.</p></div><a className="github" href="https://github.com/yasmeenmh90-beep/CodeAlpha_FAQ_Chatbot" target="_blank" rel="noreferrer"><Github size={17}/> View on GitHub <ArrowRight size={15}/></a></div>
    </aside>
    {menu && <div className="overlay" onClick={() => setMenu(false)} />}
    <main className="main">
      <header className="topbar"><div className="topLeft"><button className="iconButton mobileMenu" aria-label="Open menu" onClick={() => setMenu(true)}><Menu size={21}/></button><span className="breadcrumb">Workspace</span><span className="slash">/</span><strong>{studio ? 'Voice Studio' : adminOpen ? 'Knowledge Studio' : analytics ? 'Analytics' : showFaqs ? 'FAQ Library' : 'AI Assistant'}</strong></div><div className="topRight"><span className={`status ${apiStatus}`}><span/> {apiStatus === 'ready' ? 'Connected' : apiStatus === 'loading' ? 'Connecting' : 'Offline'}</span><button className="iconButton" aria-label="Toggle theme" onClick={() => setLight(v => !v)}>{light ? <Moon size={18}/> : <Sun size={18}/>}</button><span className="topAvatar">Q</span></div></header>
      {studio ? <VoiceStudio send={text=>send(text,"all")} answer={[...messages].reverse().find(m=>m.role==="assistant"&&m.id>0)?.text||""} loading={loading} speak={speak} rate={rate} setRate={setRate} voices={voices} voiceName={voiceName} setVoiceName={setVoiceName}/> : adminOpen ? <><button className="returnChat" onClick={()=>setAdminOpen(false)}>Back to workspace</button><KnowledgeAdmin onSaved={()=>{setCategory("all");setRefresh(v=>v+1)}}/></> : analytics ? <Analytics messages={allMessages} feedback={feedback}/> : showFaqs ? <section className="library"><div className="eyebrow"><Sparkles size={15}/> KNOWLEDGE BASE</div><h1>{topicName}</h1><p>Browse the questions powering QueryMind's retrieval engine. Choose a question to start a conversation.</p><div className="libraryTools"><div className="searchBox"><Search size={18}/><input className="search" aria-label="Search FAQs" value={search} placeholder="Search the FAQ library..." onChange={e => setSearch(e.target.value)} /></div><button className="returnChat" onClick={() => setShowFaqs(false)}><MessageCircle size={16}/> Ask assistant</button></div><div className="libraryCount" aria-live="polite">{filtered.length} questions · {topicName}</div><div className="faqGrid">{filtered.map(f => <button className="faqCard" key={f.id} onClick={() => { setShowFaqs(false); void send(f.question, f.category) }}><span>{f.category}</span><strong>{f.question}</strong><ArrowRight size={17}/></button>)}</div>{apiStatus === 'offline' ? <div className="emptyState"><p>Knowledge base unavailable. Start the backend and retry.</p><button className="returnChat" onClick={() => { setApiStatus('loading'); setRefresh(v => v+1) }}><RefreshCw size={16}/> Retry connection</button></div> : apiStatus === 'loading' ? <p>Loading FAQs…</p> : filtered.length === 0 && <p>No matching questions found.</p>}</section> :
      <div className="workspace">
        <section className="intro"><div className="eyebrow"><span className="eyebrowDot"/> CUSTOMER SUPPORT / WORKSPACE</div><h1>Support, <em>simplified.</em></h1><p>Find clear answers to your questions, all in one place.</p><div className="statRow"><span><ShieldCheck size={16}/> Privacy-first</span><span><Sparkles size={16}/> NLP-powered</span><span><Command size={16}/> Instant answers</span></div></section>
        <div className="chatLayout"><section className="chatPanel"><div className="chatHeader"><div className="assistantAvatar"><Bot size={24}/></div><div><strong>QueryMind Assistant <span className="verified"><Check size={11}/></span></strong><small><span className={`onlineDot ${apiStatus}`}/> {topicName} · {apiStatus === 'ready' ? 'Connected' : 'Not connected'}</small></div><div className="chatActions"><button className="iconButton" aria-label="Toggle response intelligence" aria-pressed={insights} onClick={()=>setInsights(v=>!v)}><Activity size={17}/></button><button className="iconButton" aria-label="Toggle expanded chat" onClick={()=>setExpanded(v=>!v)}>{expanded?<Minimize2 size={17}/>:<Maximize2 size={17}/>}</button><button className="iconButton" title="New conversation" aria-label="Clear chat" disabled={loading} onClick={clearChat}><Plus size={19}/></button><button className="iconButton" title="Copy conversation" aria-label="Copy conversation" onClick={() => { navigator.clipboard.writeText(messages.map(m => `${m.role}: ${m.text}`).join('\n\n')).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1600) }).catch(() => setError('Could not copy conversation.')) }}>{copied ? <Check size={18}/> : <Copy size={18}/>}</button><button className="iconButton" aria-label="Download transcript" onClick={download}><Download size={18}/></button></div></div>
          <div className="chatMessages" ref={scrollRef} aria-live="polite">{messages.map(m => <div className={`message ${m.role}`} key={m.id}>{m.role === 'assistant' && <div className="messageAvatar"><Sparkles size={15}/></div>}<div className="messageBody"><div className="bubble">{m.text}</div>{m.id>0 && <small className="timestamp">{new Date(m.id).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}</small>}{m.match?.matched && <div className="matchMeta"><Check size={12}/> Matched FAQ · {Math.round(m.match.confidence * 100)}% similarity</div>}{m.match?.matched_question && <details className="sourceDetails"><summary onClick={()=>{setSelectedReply(m.id);setInsights(true)}}>Answer source</summary>{m.match.matched_question}</details>}{m.role === 'assistant' && m.id !== 0 && <div className="responseTools"><button aria-label="Copy answer" onClick={()=>navigator.clipboard.writeText(m.text).catch(()=>setError('Clipboard unavailable'))}><Copy size={14}/></button><button aria-label="Stop audio" onClick={()=>window.speechSynthesis?.cancel()}><Square size={14}/></button><button aria-label="Read answer aloud" onClick={() => speak(m.text)}><Volume2 size={14}/></button><button aria-label="Helpful" aria-pressed={feedback[m.id] === 'up'} onClick={() => setFeedback(f => ({...f, [m.id]: 'up'}))}><ThumbsUp size={14}/></button><button aria-label="Not helpful" aria-pressed={feedback[m.id] === 'down'} onClick={() => setFeedback(f => ({...f, [m.id]: 'down'}))}><ThumbsDown size={14}/></button></div>}{m.match?.suggestions.length ? <div className="suggestions">{m.match.suggestions.map(s => <button key={s} disabled={loading} onClick={() => void send(s)}>{s} <ArrowRight size={12}/></button>)}</div> : null}</div></div>)}{loading && <div className="message assistant"><div className="messageAvatar"><Sparkles size={15}/></div><div className="bubble typing"><span/><span/><span/></div></div>}<div ref={endRef}/></div>
          {messages.length === 1 && <div className="quickPrompts"><button className="promptLabel promptToggle" aria-expanded={promptsOpen} onClick={()=>setPromptsOpen(v=>!v)}>SUGGESTED QUESTIONS <ChevronDown size={14}/></button>{promptsOpen && <div className="promptGrid">{prompts.map((s,i) => <button key={s} onClick={() => void send(s)}><span className="promptNum">0{i+1}</span>{s}<ArrowRight size={15}/></button>)}</div>}</div>}
          <div className="voiceDock"><button className="voiceToggle" aria-expanded={voiceOpen} onClick={()=>setVoiceOpen(v=>!v)}><Mic size={14}/> Voice settings <ChevronDown size={13}/></button>{voiceOpen && <div className="voiceSettings voicePopover"><div className="voicePopoverTitle"><strong>Voice preferences</strong><button className="iconButton" aria-label="Close voice settings" onClick={()=>setVoiceOpen(false)}><X size={16}/></button></div><label>Voice <select value={voiceName} onChange={e=>setVoiceName(e.target.value)}><option value="">Default</option>{voices.map(v=><option key={v.name} value={v.name}>{v.name}</option>)}</select></label><label>Speed <input type="range" min=".7" max="1.5" step=".1" value={rate} onChange={e=>setRate(Number(e.target.value))}/>{rate}×</label></div>}</div><form className="composer" onSubmit={e => { e.preventDefault(); void send() }}><div className="inputWrap"><input value={input} onChange={e => setInput(e.target.value)} placeholder="Ask QueryMind anything..." aria-label="Your question" maxLength={1500} /><button type="button" className={`micButton ${listening ? "listening" : ""}`} disabled={listening} aria-label="Voice input" onClick={voice}><Mic size={17}/></button><button type="submit" aria-label="Send message" disabled={!input.trim() || loading}><Send size={18}/></button></div><div className="composerHint"><span>{topicName} · NLP retrieval</span><span>Enter ↵ to send</span></div>{error && <small className="error" role="alert">{error}</small>}</form>
        </section>
        {insights && <aside className="intelligencePanel"><div className="eyebrow">RESPONSE INTELLIGENCE</div><h2>Retrieval details</h2>{inspected?.match ? <><div className="intelligenceScore"><strong>{Math.round(inspected.match.confidence*100)}%</strong><span>Similarity score · not probability</span><div className="intelligenceMeter"><i style={{width:Math.max(0,Math.min(100,inspected.match.confidence*100))+'%'}}/></div></div><dl><dt>Outcome</dt><dd>{inspected.match.matched?'FAQ matched':'No reliable match'}</dd><dt>Category</dt><dd>{inspected.match.category||'Unknown'}</dd><dt>Latency</dt><dd>{inspected.latency===undefined?'Not measured':inspected.latency+' ms'}</dd></dl><h3>Retrieval pipeline</h3><ol><li>NLTK text preprocessing</li><li>TF-IDF vectorization</li><li>Cosine similarity ranking</li><li>{inspected.match.matched?'FAQ response':'Fallback response'}</li></ol><h3>Knowledge source</h3><p>{inspected.match.matched_question||'No source matched'}</p></>:<p>Ask a question to inspect its retrieval score, source and response time.</p>}</aside>}</div><div className="metrics"><div><span>KNOWLEDGE BASE</span><strong>{faqs.length || '—'} <small>FAQs</small></strong></div><div><span>QUESTIONS ASKED</span><strong>{attempts}</strong></div><div><span>SUCCESSFUL MATCHES</span><strong>{answered}</strong></div><div className="lastMetric"><span>AI ENGINE</span><strong>TF-IDF <small>+ NLP</small></strong></div></div>
      </div>}
    </main>
  </div>
}

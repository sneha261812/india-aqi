import { useState, useRef, useEffect } from 'react'
import { sendChatMessage } from '../api'
import { MessageCircle, Send, Bot, User } from 'lucide-react'

const STARTERS = [
  "What does an AQI of 200 mean for my health?",
  "Why is Delhi's AQI so bad in winter?",
  "Which N95 mask is best for Indian pollution?",
  "How do I protect my child from air pollution?",
]

export default function ChatbotPage() {
  const [messages, setMessages] = useState([
    {
      role: 'model',
      parts: ["Namaste! I'm AQI Saathi 🌿 — your AI guide for India's air quality. Ask me anything about AQI, health effects, or pollution in your city!"],
    }
  ])
  const [input, setInput]     = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send(text) {
    const msg = (text || input).trim()
    if (!msg || sending) return
    setInput('')
    const updated = [...messages, { role: 'user', parts: [msg] }]
    setMessages(updated)
    setSending(true)
    try {
      // Build history for API (exclude the latest user message we just pushed)
      const history = updated.slice(0, -1).map(m => ({ role: m.role, parts: [m.parts[0]] }))
      const res = await sendChatMessage(msg, history)
      setMessages(prev => [...prev, { role: 'model', parts: [res.data.response] }])
    } catch {
      setMessages(prev => [...prev, { role: 'model', parts: ['Sorry, I had trouble connecting. Please try again.'] }])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-9rem)] max-w-3xl flex-col">
      {/* Header */}
      <div className="card mb-4 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-500/10">
          <Bot className="h-5 w-5 text-orange-400" />
        </div>
        <div>
          <h1 className="font-display font-semibold">AQI Saathi</h1>
          <p className="text-xs text-gray-400">Powered by Gemini · Live AQI-aware responses</p>
        </div>
        <div className="ml-auto flex h-2 w-2 rounded-full bg-green-400 shadow-lg shadow-green-400/50" />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.map((m, i) => (
          <Message key={i} role={m.role} text={m.parts[0]} />
        ))}
        {sending && (
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-orange-500/10">
              <Bot className="h-4 w-4 text-orange-400" />
            </div>
            <div className="rounded-2xl rounded-tl-none bg-[var(--surface-2)] px-4 py-3">
              <div className="flex gap-1">
                {[0, 1, 2].map(d => (
                  <span key={d} className="h-2 w-2 animate-bounce rounded-full bg-orange-400"
                    style={{ animationDelay: `${d * 0.15}s` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Starter prompts */}
      {messages.length <= 1 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {STARTERS.map(s => (
            <button key={s} onClick={() => send(s)}
              className="rounded-full border border-[var(--border)] px-3 py-1.5 text-xs text-gray-300 transition hover:border-orange-500 hover:text-orange-300">
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder="Ask about AQI, health, pollution…"
          className="flex-1 rounded-xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-sm outline-none focus:border-orange-500"
        />
        <button
          onClick={() => send()}
          disabled={!input.trim() || sending}
          className="flex h-12 w-12 items-center justify-center rounded-xl bg-orange-500 transition hover:bg-orange-400 disabled:opacity-40"
        >
          <Send className="h-5 w-5 text-white" />
        </button>
      </div>
    </div>
  )
}

function Message({ role, text }) {
  const isBot = role === 'model'
  return (
    <div className={`flex items-start gap-3 ${isBot ? '' : 'flex-row-reverse'}`}>
      <div className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full ${isBot ? 'bg-orange-500/10' : 'bg-blue-500/10'}`}>
        {isBot ? <Bot className="h-4 w-4 text-orange-400" /> : <User className="h-4 w-4 text-blue-400" />}
      </div>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
        isBot ? 'rounded-tl-none bg-[var(--surface-2)] text-gray-200' : 'rounded-tr-none bg-blue-600/20 text-white'
      }`}>
        {text}
      </div>
    </div>
  )
}

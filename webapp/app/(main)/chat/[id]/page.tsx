'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams } from 'next/navigation'
import { useSession } from 'next-auth/react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, ArrowLeft, Phone, Video, MoreVertical, Play, Pause } from 'lucide-react'
import { useRouter } from 'next/navigation'
import type { Socket } from 'socket.io-client'
import { formatTime, getInitials, formatDuration } from '@/lib/utils'
import { VoiceRecorder } from '@/components/voice-recorder'
import { VideoCircleRecorder, VideoCircleDisplay } from '@/components/video-circle'

type Message = {
  id: string
  content?: string
  type: 'TEXT' | 'VOICE' | 'VIDEO_CIRCLE' | 'IMAGE' | 'FILE'
  fileUrl?: string
  duration?: number
  createdAt: string
  sender: { id: string; username: string; avatar?: string }
}

type ChatInfo = {
  id: string
  name?: string
  type: string
  members: { user: { id: string; username: string; isOnline: boolean } }[]
}

export default function ChatPage() {
  const { id } = useParams<{ id: string }>()
  const { data: session } = useSession()
  const router = useRouter()

  const [messages, setMessages] = useState<Message[]>([])
  const [chat, setChat] = useState<ChatInfo | null>(null)
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(true)
  const [showVoice, setShowVoice] = useState(false)
  const [showVideoCircle, setShowVideoCircle] = useState(false)
  const [typing, setTyping] = useState(false)
  const [otherTyping, setOtherTyping] = useState(false)

  const bottomRef = useRef<HTMLDivElement>(null)
  const socketRef = useRef<Socket | null>(null)
  const typingTimerRef = useRef<NodeJS.Timeout | null>(null)

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    // Load chat info and messages
    Promise.all([
      fetch(`/api/chats/${id}`).then((r) => r.json()),
      fetch(`/api/messages?chatId=${id}`).then((r) => r.json()),
    ]).then(([chatData, msgs]) => {
      setChat(chatData)
      setMessages(msgs)
      setLoading(false)
    })

    // Socket.io connection (dynamic import to avoid SSR issues)
    let socket: Socket
    import('socket.io-client').then(({ default: io }) => {
      socket = io({ path: '/api/socket' })
      socketRef.current = socket

      socket.emit('join-room', id)

      socket.on('message', (msg: Message) => {
        setMessages((prev) => [...prev, msg])
      })

      socket.on('typing', (userId: string) => {
        if (userId !== session?.user?.id) setOtherTyping(true)
      })

      socket.on('stop-typing', (userId: string) => {
        if (userId !== session?.user?.id) setOtherTyping(false)
      })
    })

    return () => {
      socketRef.current?.emit('leave-room', id)
      socketRef.current?.disconnect()
    }
  }, [id, session?.user?.id])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const sendText = async () => {
    if (!text.trim()) return
    const content = text.trim()
    setText('')
    await sendMessage({ type: 'TEXT', content })
  }

  const sendMessage = async (data: { type: string; content?: string; fileUrl?: string; duration?: number }) => {
    const res = await fetch('/api/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chatId: id, ...data }),
    })
    if (res.ok) {
      const msg = await res.json()
      socketRef.current?.emit('send-message', { roomId: id, message: msg })
      setMessages((prev) => [...prev, msg])
    }
  }

  const handleVoiceSend = async (blob: Blob, duration: number) => {
    setShowVoice(false)
    const formData = new FormData()
    formData.append('file', blob, 'voice.webm')
    formData.append('chatId', id)
    const res = await fetch('/api/upload', { method: 'POST', body: formData })
    if (res.ok) {
      const { url } = await res.json()
      await sendMessage({ type: 'VOICE', fileUrl: url, duration })
    }
  }

  const handleVideoSend = async (blob: Blob, duration: number) => {
    setShowVideoCircle(false)
    const formData = new FormData()
    formData.append('file', blob, 'video.webm')
    formData.append('chatId', id)
    const res = await fetch('/api/upload', { method: 'POST', body: formData })
    if (res.ok) {
      const { url } = await res.json()
      await sendMessage({ type: 'VIDEO_CIRCLE', fileUrl: url, duration })
    }
  }

  const handleTyping = () => {
    if (!typing) {
      setTyping(true)
      socketRef.current?.emit('typing', { roomId: id, userId: session?.user?.id })
    }
    typingTimerRef.current && clearTimeout(typingTimerRef.current)
    typingTimerRef.current = setTimeout(() => {
      setTyping(false)
      socketRef.current?.emit('stop-typing', { roomId: id, userId: session?.user?.id })
    }, 1500)
  }

  const myId = session?.user?.id
  const chatName = chat?.name || chat?.members.find((m) => m.user.id !== myId)?.user.username || 'Чат'
  const isOnline = chat?.members.some((m) => m.user.id !== myId && m.user.isOnline)

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-white/[0.06] glass shrink-0">
        <button onClick={() => router.push('/chat')} className="text-text-muted hover:text-text-primary transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="relative">
          <div className="w-9 h-9 rounded-full btn-gradient flex items-center justify-center text-sm font-bold text-white">
            {getInitials(chatName)}
          </div>
          {isOnline && <div className="online-dot absolute -bottom-0.5 -right-0.5" />}
        </div>
        <div className="flex-1">
          <div className="text-sm font-semibold text-text-primary">{chatName}</div>
          <div className="text-[11px] text-text-muted">
            {otherTyping ? (
              <span className="text-accent-purple-light">печатает...</span>
            ) : isOnline ? (
              'В сети'
            ) : (
              'Не в сети'
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <button className="w-8 h-8 rounded-xl glass flex items-center justify-center text-text-muted hover:text-text-primary transition-colors">
            <Phone className="w-4 h-4" />
          </button>
          <button className="w-8 h-8 rounded-xl glass flex items-center justify-center text-text-muted hover:text-text-primary transition-colors">
            <Video className="w-4 h-4" />
          </button>
          <button className="w-8 h-8 rounded-xl glass flex items-center justify-center text-text-muted hover:text-text-primary transition-colors">
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-1">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="w-8 h-8 border-2 border-accent-purple border-t-transparent rounded-full animate-spin" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-text-muted gap-2">
            <div className="text-4xl">👋</div>
            <p className="text-sm">Начни общение!</p>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => {
              const isMine = msg.sender.id === myId
              const showAvatar = !isMine && (i === 0 || messages[i - 1]?.sender.id !== msg.sender.id)
              return (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex items-end gap-2 ${isMine ? 'justify-end' : 'justify-start'}`}
                >
                  {!isMine && (
                    <div className={`w-6 h-6 rounded-full btn-gradient flex items-center justify-center text-[10px] font-bold text-white shrink-0 mb-1 ${!showAvatar ? 'opacity-0' : ''}`}>
                      {getInitials(msg.sender.username)}
                    </div>
                  )}
                  <div className={`max-w-[70%] ${isMine ? 'items-end' : 'items-start'} flex flex-col`}>
                    {!isMine && showAvatar && (
                      <span className="text-[11px] text-accent-purple-light mb-1 px-1">{msg.sender.username}</span>
                    )}

                    {msg.type === 'TEXT' && (
                      <div className={`px-4 py-2.5 ${isMine ? 'bubble-sent' : 'bubble-received'}`}>
                        <p className="text-sm text-text-primary leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    )}

                    {msg.type === 'VOICE' && msg.fileUrl && (
                      <VoiceMessagePlayer url={msg.fileUrl} duration={msg.duration || 0} isMine={isMine} />
                    )}

                    {msg.type === 'VIDEO_CIRCLE' && msg.fileUrl && (
                      <VideoCircleDisplay url={msg.fileUrl} isSent={isMine} />
                    )}

                    {msg.type === 'IMAGE' && msg.fileUrl && (
                      <img src={msg.fileUrl} alt="" className="rounded-2xl max-w-full max-h-64 object-cover border border-white/[0.06]" />
                    )}

                    <span className="text-[10px] text-text-muted mt-1 px-1">{formatTime(msg.createdAt)}</span>
                  </div>
                </motion.div>
              )
            })}
            {otherTyping && (
              <div className="flex items-end gap-2">
                <div className="w-6 h-6 rounded-full bg-bg-surface shrink-0" />
                <div className="bubble-received px-4 py-3">
                  <div className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                      <div key={i} className="w-1.5 h-1.5 rounded-full bg-text-muted animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="p-3 border-t border-white/[0.06] glass shrink-0">
        {showVideoCircle ? (
          <div className="flex justify-center py-2">
            <VideoCircleRecorder
              onSend={handleVideoSend}
              onCancel={() => setShowVideoCircle(false)}
            />
          </div>
        ) : showVoice ? (
          <VoiceRecorder
            onSend={handleVoiceSend}
            onCancel={() => setShowVoice(false)}
          />
        ) : (
          <div className="flex items-end gap-2">
            <div className="flex gap-1">
              <button
                onClick={() => setShowVoice(true)}
                className="w-9 h-9 rounded-xl glass flex items-center justify-center text-text-muted hover:text-accent-purple-light transition-colors"
                title="Голосовое"
              >
                🎤
              </button>
              <button
                onClick={() => setShowVideoCircle(true)}
                className="w-9 h-9 rounded-xl glass flex items-center justify-center text-text-muted hover:text-accent-cyan-light transition-colors"
                title="Кружок"
              >
                ⭕
              </button>
            </div>
            <div className="flex-1 relative">
              <textarea
                value={text}
                onChange={(e) => { setText(e.target.value); handleTyping() }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    sendText()
                  }
                }}
                placeholder="Написать сообщение..."
                rows={1}
                className="input-dark w-full rounded-2xl px-4 py-2.5 text-sm resize-none max-h-32"
                style={{ lineHeight: '1.5' }}
              />
            </div>
            <button
              onClick={sendText}
              disabled={!text.trim()}
              className="w-9 h-9 rounded-xl btn-gradient flex items-center justify-center disabled:opacity-40 shrink-0"
            >
              <Send className="w-4 h-4 text-white" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// Voice message player component
function VoiceMessagePlayer({ url, duration, isMine }: { url: string; duration: number; isMine: boolean }) {
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const audioRef = useRef<HTMLAudioElement>(null)

  const toggle = () => {
    if (!audioRef.current) return
    if (playing) {
      audioRef.current.pause()
      setPlaying(false)
    } else {
      audioRef.current.play()
      setPlaying(true)
    }
  }

  return (
    <div className={`flex items-center gap-3 px-4 py-3 ${isMine ? 'bubble-sent' : 'bubble-received'} min-w-[160px]`}>
      <audio
        ref={audioRef}
        src={url}
        onTimeUpdate={(e) => {
          const el = e.currentTarget
          setProgress((el.currentTime / el.duration) * 100 || 0)
        }}
        onEnded={() => { setPlaying(false); setProgress(0) }}
      />
      <button onClick={toggle} className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center shrink-0">
        {playing ? <Pause className="w-3.5 h-3.5 text-white" /> : <Play className="w-3.5 h-3.5 text-white" />}
      </button>
      <div className="flex-1">
        <div className="h-1 bg-white/20 rounded-full overflow-hidden">
          <div className="h-full bg-white/60 rounded-full transition-all" style={{ width: `${progress}%` }} />
        </div>
        <span className="text-[10px] text-white/60 mt-1 block">{formatDuration(duration)}</span>
      </div>
    </div>
  )
}

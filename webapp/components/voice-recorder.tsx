'use client'

import { useState, useRef, useEffect } from 'react'
import { Mic, Square, Play, Pause, Send, Trash2 } from 'lucide-react'
import { formatDuration } from '@/lib/utils'

type Props = {
  onSend: (blob: Blob, duration: number) => void
  onCancel: () => void
}

export function VoiceRecorder({ onSend, onCancel }: Props) {
  const [state, setState] = useState<'idle' | 'recording' | 'preview'>('idle')
  const [duration, setDuration] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [blob, setBlob] = useState<Blob | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)

  const mediaRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    return () => {
      timerRef.current && clearInterval(timerRef.current)
      audioUrl && URL.revokeObjectURL(audioUrl)
    }
  }, [audioUrl])

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const recorder = new MediaRecorder(stream)
    mediaRef.current = recorder
    chunksRef.current = []
    recorder.ondataavailable = (e) => chunksRef.current.push(e.data)
    recorder.onstop = () => {
      const b = new Blob(chunksRef.current, { type: 'audio/webm' })
      setBlob(b)
      setAudioUrl(URL.createObjectURL(b))
      setState('preview')
      stream.getTracks().forEach((t) => t.stop())
    }
    recorder.start()
    setState('recording')
    setDuration(0)
    timerRef.current = setInterval(() => setDuration((d) => d + 1), 1000)
  }

  const stopRecording = () => {
    mediaRef.current?.stop()
    timerRef.current && clearInterval(timerRef.current)
  }

  const togglePlay = () => {
    if (!audioRef.current) return
    if (playing) {
      audioRef.current.pause()
      setPlaying(false)
    } else {
      audioRef.current.play()
      setPlaying(true)
      audioRef.current.onended = () => setPlaying(false)
    }
  }

  const send = () => {
    if (blob) onSend(blob, duration)
  }

  if (state === 'idle') {
    return (
      <button
        onClick={startRecording}
        className="w-9 h-9 rounded-xl glass flex items-center justify-center text-text-muted hover:text-accent-purple-light transition-colors"
        title="Записать голосовое"
      >
        <Mic className="w-4 h-4" />
      </button>
    )
  }

  if (state === 'recording') {
    return (
      <div className="flex items-center gap-2 px-3 py-2 glass rounded-xl">
        <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
        <span className="text-xs text-red-400 font-mono min-w-[36px]">{formatDuration(duration)}</span>
        <button
          onClick={stopRecording}
          className="w-7 h-7 rounded-lg bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-400 hover:bg-red-500/30 transition-colors"
        >
          <Square className="w-3 h-3 fill-red-400" />
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 px-3 py-2 glass rounded-xl">
      {audioUrl && (
        <audio ref={audioRef} src={audioUrl} className="hidden" />
      )}
      <button
        onClick={togglePlay}
        className="w-7 h-7 rounded-full btn-gradient flex items-center justify-center"
      >
        {playing ? (
          <Pause className="w-3 h-3 text-white" />
        ) : (
          <Play className="w-3 h-3 text-white" />
        )}
      </button>
      <div className="flex-1 h-1 bg-white/10 rounded-full min-w-[60px]">
        <div className="h-full bg-gradient-main rounded-full w-1/3" />
      </div>
      <span className="text-[10px] text-text-muted font-mono">{formatDuration(duration)}</span>
      <button onClick={onCancel} className="text-text-muted hover:text-red-400 transition-colors">
        <Trash2 className="w-3.5 h-3.5" />
      </button>
      <button onClick={send} className="w-7 h-7 rounded-lg btn-gradient flex items-center justify-center">
        <Send className="w-3 h-3 text-white" />
      </button>
    </div>
  )
}

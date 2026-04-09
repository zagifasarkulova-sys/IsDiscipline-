'use client'

import { useState, useRef, useEffect } from 'react'
import { Video, Square, Send, Trash2, Play, Pause } from 'lucide-react'

type RecorderProps = {
  onSend: (blob: Blob, duration: number) => void
  onCancel: () => void
}

export function VideoCircleRecorder({ onSend, onCancel }: RecorderProps) {
  const [state, setState] = useState<'idle' | 'recording' | 'preview'>('idle')
  const [duration, setDuration] = useState(0)
  const [blob, setBlob] = useState<Blob | null>(null)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [playing, setPlaying] = useState(false)

  const previewRef = useRef<HTMLVideoElement>(null)
  const recordRef = useRef<HTMLVideoElement>(null)
  const mediaRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  useEffect(() => () => {
    timerRef.current && clearInterval(timerRef.current)
    streamRef.current?.getTracks().forEach((t) => t.stop())
    videoUrl && URL.revokeObjectURL(videoUrl)
  }, [videoUrl])

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 320, height: 320 }, audio: true })
    streamRef.current = stream
    if (recordRef.current) {
      recordRef.current.srcObject = stream
      recordRef.current.play()
    }
    const recorder = new MediaRecorder(stream)
    mediaRef.current = recorder
    chunksRef.current = []
    recorder.ondataavailable = (e) => chunksRef.current.push(e.data)
    recorder.onstop = () => {
      const b = new Blob(chunksRef.current, { type: 'video/webm' })
      setBlob(b)
      setVideoUrl(URL.createObjectURL(b))
      setState('preview')
      stream.getTracks().forEach((t) => t.stop())
    }
    recorder.start()
    setState('recording')
    setDuration(0)
    timerRef.current = setInterval(() => {
      setDuration((d) => {
        if (d >= 59) { stopRecording(); return d }
        return d + 1
      })
    }, 1000)
  }

  const stopRecording = () => {
    mediaRef.current?.stop()
    timerRef.current && clearInterval(timerRef.current)
  }

  const togglePlay = () => {
    if (!previewRef.current) return
    if (playing) {
      previewRef.current.pause()
      setPlaying(false)
    } else {
      previewRef.current.play()
      setPlaying(true)
      previewRef.current.onended = () => setPlaying(false)
    }
  }

  if (state === 'idle') {
    return (
      <button
        onClick={startRecording}
        className="w-9 h-9 rounded-xl glass flex items-center justify-center text-text-muted hover:text-accent-cyan-light transition-colors"
        title="Записать кружок"
      >
        <Video className="w-4 h-4" />
      </button>
    )
  }

  if (state === 'recording') {
    return (
      <div className="flex flex-col items-center gap-2">
        <div className="relative">
          <video
            ref={recordRef}
            muted
            className="w-28 h-28 object-cover rounded-full"
            style={{ transform: 'scaleX(-1)' }}
          />
          <div
            className="absolute inset-0 rounded-full border-4 border-transparent"
            style={{
              background: `conic-gradient(#7c3aed ${(duration / 60) * 360}deg, transparent 0deg)`,
              WebkitMaskImage: 'radial-gradient(transparent 52px, black 53px)',
              maskImage: 'radial-gradient(transparent 52px, black 53px)',
            }}
          />
          <div className="absolute bottom-1 left-1/2 -translate-x-1/2 bg-black/60 rounded-full px-2 py-0.5 text-[10px] text-white font-mono">
            {60 - duration}с
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={onCancel} className="px-3 py-1.5 rounded-xl glass text-xs text-text-muted hover:text-red-400 transition-colors">
            Отмена
          </button>
          <button
            onClick={stopRecording}
            className="px-3 py-1.5 rounded-xl bg-red-500/20 border border-red-500/40 text-xs text-red-400 flex items-center gap-1"
          >
            <Square className="w-3 h-3 fill-red-400" />
            Стоп
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-28 h-28 video-circle cursor-pointer" onClick={togglePlay}>
        {videoUrl && <video ref={previewRef} src={videoUrl} className="w-full h-full object-cover" loop />}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-9 h-9 rounded-full glass-strong flex items-center justify-center">
            {playing ? <Pause className="w-4 h-4 text-white" /> : <Play className="w-4 h-4 text-white" />}
          </div>
        </div>
      </div>
      <div className="flex gap-2">
        <button onClick={onCancel} className="p-2 rounded-xl glass text-text-muted hover:text-red-400 transition-colors">
          <Trash2 className="w-3.5 h-3.5" />
        </button>
        <button onClick={() => blob && onSend(blob, duration)} className="px-4 py-2 rounded-xl btn-gradient text-xs font-medium text-white flex items-center gap-1.5">
          <Send className="w-3 h-3" />
          Отправить
        </button>
      </div>
    </div>
  )
}

// Display component for received/sent video circles
type DisplayProps = {
  url: string
  isSent: boolean
}

export function VideoCircleDisplay({ url, isSent }: DisplayProps) {
  const [playing, setPlaying] = useState(false)
  const ref = useRef<HTMLVideoElement>(null)

  const toggle = () => {
    if (!ref.current) return
    if (playing) { ref.current.pause(); setPlaying(false) }
    else { ref.current.play(); setPlaying(true); ref.current.onended = () => setPlaying(false) }
  }

  return (
    <div
      className="relative w-24 h-24 video-circle cursor-pointer hover:opacity-90 transition-opacity"
      onClick={toggle}
    >
      <video ref={ref} src={url} className="w-full h-full object-cover" loop />
      <div className="absolute inset-0 flex items-center justify-center">
        {!playing && (
          <div className="w-8 h-8 rounded-full bg-black/50 flex items-center justify-center">
            <Play className="w-4 h-4 text-white" />
          </div>
        )}
      </div>
    </div>
  )
}

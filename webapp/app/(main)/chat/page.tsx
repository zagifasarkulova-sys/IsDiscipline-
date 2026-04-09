'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useSession } from 'next-auth/react'
import { motion } from 'framer-motion'
import { Search, Plus, MessageCircle, Users } from 'lucide-react'
import { formatTime, getInitials } from '@/lib/utils'

type Chat = {
  id: string
  type: string
  name?: string
  members: { user: { id: string; username: string; isOnline: boolean } }[]
  messages: { content?: string; type: string; createdAt: string; sender: { username: string } }[]
}

export default function ChatListPage() {
  const { data: session } = useSession()
  const [chats, setChats] = useState<Chat[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    fetch('/api/chats')
      .then((r) => r.json())
      .then((data) => { setChats(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const filtered = chats.filter((c) => {
    const name = getChatName(c, session?.user?.id || '')
    return name.toLowerCase().includes(search.toLowerCase())
  })

  function getChatName(chat: Chat, myId: string): string {
    if (chat.name) return chat.name
    const other = chat.members.find((m) => m.user.id !== myId)
    return other?.user.username || 'Чат'
  }

  function getLastMessage(chat: Chat): string {
    const last = chat.messages[0]
    if (!last) return 'Нет сообщений'
    if (last.type === 'VOICE') return '🎤 Голосовое'
    if (last.type === 'VIDEO_CIRCLE') return '⭕ Видеокружок'
    if (last.type === 'IMAGE') return '🖼 Фото'
    return last.content || ''
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-white/[0.06]">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-lg font-bold text-text-primary">Сообщения</h1>
          <button className="w-8 h-8 rounded-xl btn-gradient flex items-center justify-center">
            <Plus className="w-4 h-4 text-white" />
          </button>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск чатов..."
            className="input-dark w-full rounded-xl pl-9 pr-4 py-2.5 text-sm"
          />
        </div>
      </div>

      {/* Chat list */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 p-4">
              <div className="w-11 h-11 rounded-full shimmer shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-3 w-32 rounded shimmer" />
                <div className="h-2 w-48 rounded shimmer" />
              </div>
            </div>
          ))
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-text-muted gap-3">
            <MessageCircle className="w-12 h-12 opacity-20" />
            <p className="text-sm">Нет чатов</p>
            <button className="btn-gradient text-white text-xs px-4 py-2 rounded-xl">
              Начать диалог
            </button>
          </div>
        ) : (
          filtered.map((chat, i) => {
            const name = getChatName(chat, session?.user?.id || '')
            const last = chat.messages[0]
            const isOnline = chat.members.some(
              (m) => m.user.id !== session?.user?.id && m.user.isOnline
            )
            return (
              <motion.button
                key={chat.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                onClick={() => router.push(`/chat/${chat.id}`)}
                className="w-full flex items-center gap-3 p-4 hover:bg-white/[0.03] transition-colors border-b border-white/[0.04]"
              >
                <div className="relative shrink-0">
                  <div className="w-11 h-11 rounded-full btn-gradient flex items-center justify-center text-sm font-bold text-white">
                    {chat.type === 'GROUP' ? (
                      <Users className="w-5 h-5" />
                    ) : (
                      getInitials(name)
                    )}
                  </div>
                  {isOnline && <div className="online-dot absolute -bottom-0.5 -right-0.5" />}
                </div>
                <div className="flex-1 min-w-0 text-left">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-text-primary truncate">{name}</span>
                    {last && (
                      <span className="text-[10px] text-text-muted shrink-0 ml-2">
                        {formatTime(last.createdAt)}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-text-muted truncate mt-0.5">{getLastMessage(chat)}</p>
                </div>
              </motion.button>
            )
          })
        )}
      </div>
    </div>
  )
}

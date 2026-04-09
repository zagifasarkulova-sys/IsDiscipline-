'use client'

import { useState, useEffect, useRef } from 'react'
import { useSession } from 'next-auth/react'
import { motion, AnimatePresence } from 'framer-motion'
import { Image, Smile, Send, Heart, MessageCircle, Zap, Flame, TrendingUp } from 'lucide-react'
import { formatDate, getInitials } from '@/lib/utils'
import toast from 'react-hot-toast'

type Post = {
  id: string
  content: string
  imageUrl?: string
  createdAt: string
  author: { id: string; username: string; avatar?: string; streak: number; xp: number }
  likes: { userId: string }[]
  comments: { id: string; content: string; user: { username: string }; createdAt: string }[]
  _count: { likes: number; comments: number }
}

export default function FeedPage() {
  const { data: session } = useSession()
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)
  const [text, setText] = useState('')
  const [posting, setPosting] = useState(false)
  const [expandedComments, setExpandedComments] = useState<Set<string>>(new Set())
  const [commentText, setCommentText] = useState<Record<string, string>>({})

  const fetchPosts = async () => {
    try {
      const res = await fetch('/api/posts')
      if (res.ok) setPosts(await res.json())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchPosts() }, [])

  const submitPost = async () => {
    if (!text.trim()) return
    setPosting(true)
    try {
      const res = await fetch('/api/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text.trim() }),
      })
      if (res.ok) {
        setText('')
        fetchPosts()
        toast.success('Опубликовано! +10 XP ⚡')
      }
    } finally {
      setPosting(false)
    }
  }

  const toggleLike = async (postId: string) => {
    await fetch(`/api/posts/${postId}/like`, { method: 'POST' })
    fetchPosts()
  }

  const submitComment = async (postId: string) => {
    const content = commentText[postId]?.trim()
    if (!content) return
    const res = await fetch(`/api/posts/${postId}/comment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    })
    if (res.ok) {
      setCommentText((prev) => ({ ...prev, [postId]: '' }))
      fetchPosts()
    }
  }

  const userId = session?.user?.id

  return (
    <div className="h-full flex overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto space-y-4">
          {/* Post composer */}
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="glass-strong rounded-2xl p-4">
            <div className="flex gap-3">
              <div className="w-9 h-9 rounded-full btn-gradient flex items-center justify-center text-sm font-bold text-white shrink-0">
                {session?.user?.name ? getInitials(session.user.name) : '?'}
              </div>
              <div className="flex-1">
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Что нового? Поделись прогрессом..."
                  className="input-dark w-full rounded-xl px-4 py-3 text-sm resize-none min-h-[80px]"
                  onKeyDown={(e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) submitPost() }}
                />
                <div className="flex items-center justify-between mt-2">
                  <div className="flex gap-2">
                    <button className="p-2 rounded-lg glass text-text-muted hover:text-accent-purple-light transition-colors">
                      <Image className="w-4 h-4" />
                    </button>
                    <button className="p-2 rounded-lg glass text-text-muted hover:text-accent-purple-light transition-colors">
                      <Smile className="w-4 h-4" />
                    </button>
                  </div>
                  <button
                    onClick={submitPost}
                    disabled={!text.trim() || posting}
                    className="btn-gradient flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white disabled:opacity-50"
                  >
                    <span>{posting ? 'Публикация...' : 'Опубликовать'}</span>
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Posts */}
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="post-card p-4 space-y-3">
                <div className="flex gap-3 items-center">
                  <div className="w-9 h-9 rounded-full shimmer" />
                  <div className="space-y-2 flex-1">
                    <div className="h-3 w-32 rounded shimmer" />
                    <div className="h-2 w-20 rounded shimmer" />
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="h-3 w-full rounded shimmer" />
                  <div className="h-3 w-3/4 rounded shimmer" />
                </div>
              </div>
            ))
          ) : posts.length === 0 ? (
            <div className="text-center py-16 text-text-muted">
              <Zap className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">Пока нет постов. Будь первым!</p>
            </div>
          ) : (
            <AnimatePresence>
              {posts.map((post, i) => {
                const liked = post.likes.some((l) => l.userId === userId)
                const showComments = expandedComments.has(post.id)
                return (
                  <motion.div
                    key={post.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="post-card p-4"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-9 h-9 rounded-full btn-gradient flex items-center justify-center text-sm font-bold text-white shrink-0">
                        {getInitials(post.author.username)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-text-primary">{post.author.username}</span>
                          {post.author.streak > 0 && (
                            <span className="flex items-center gap-0.5 text-xs text-orange-400">
                              <Flame className="w-3 h-3" />{post.author.streak}
                            </span>
                          )}
                          <span className="xp-badge">{post.author.xp} XP</span>
                        </div>
                        <span className="text-[11px] text-text-muted">{formatDate(post.createdAt)}</span>
                      </div>
                    </div>
                    <p className="text-sm text-text-primary leading-relaxed mb-3 whitespace-pre-wrap">{post.content}</p>
                    {post.imageUrl && (
                      <img src={post.imageUrl} alt="" className="rounded-xl w-full object-cover max-h-80 mb-3 border border-white/[0.06]" />
                    )}
                    <div className="flex items-center gap-3 pt-2 border-t border-white/[0.04]">
                      <button
                        onClick={() => toggleLike(post.id)}
                        className={`flex items-center gap-1.5 text-xs transition-colors ${liked ? 'text-red-400' : 'text-text-muted hover:text-red-400'}`}
                      >
                        <Heart className={`w-4 h-4 ${liked ? 'fill-red-400' : ''}`} />
                        <span>{post._count.likes}</span>
                      </button>
                      <button
                        onClick={() => setExpandedComments((prev) => { const n = new Set(prev); n.has(post.id) ? n.delete(post.id) : n.add(post.id); return n })}
                        className="flex items-center gap-1.5 text-xs text-text-muted hover:text-accent-purple-light transition-colors"
                      >
                        <MessageCircle className="w-4 h-4" />
                        <span>{post._count.comments}</span>
                      </button>
                    </div>
                    <AnimatePresence>
                      {showComments && (
                        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mt-3 space-y-2">
                          {post.comments.map((c) => (
                            <div key={c.id} className="flex gap-2">
                              <div className="w-6 h-6 rounded-full btn-gradient flex items-center justify-center text-[10px] font-bold text-white shrink-0">
                                {getInitials(c.user.username)}
                              </div>
                              <div className="glass rounded-xl px-3 py-2 flex-1">
                                <span className="text-xs font-semibold text-accent-purple-light mr-1.5">{c.user.username}</span>
                                <span className="text-xs text-text-secondary">{c.content}</span>
                              </div>
                            </div>
                          ))}
                          <div className="flex gap-2 mt-2">
                            <input
                              value={commentText[post.id] || ''}
                              onChange={(e) => setCommentText((prev) => ({ ...prev, [post.id]: e.target.value }))}
                              onKeyDown={(e) => { if (e.key === 'Enter') submitComment(post.id) }}
                              placeholder="Комментарий..."
                              className="input-dark flex-1 rounded-xl px-3 py-2 text-xs"
                            />
                            <button onClick={() => submitComment(post.id)} className="btn-gradient w-8 h-8 rounded-xl flex items-center justify-center">
                              <Send className="w-3.5 h-3.5 text-white" />
                            </button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                )
              })}
            </AnimatePresence>
          )}
        </div>
      </div>

      {/* Right panel */}
      <div className="w-72 shrink-0 border-l border-white/[0.06] p-4 overflow-y-auto hidden xl:block">
        <div className="space-y-4">
          <div className="glass-strong rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-accent-purple-light" />
              <span className="text-sm font-semibold text-text-primary">Твой прогресс</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {[{ label: 'Streak', value: '0', icon: '🔥' }, { label: 'XP', value: '0', icon: '⚡' }, { label: 'Посты', value: '0', icon: '📝' }, { label: 'Место', value: '—', icon: '🏆' }].map(({ label, value, icon }) => (
                <div key={label} className="glass rounded-xl p-2.5 text-center">
                  <div className="text-lg mb-0.5">{icon}</div>
                  <div className="text-base font-bold gradient-text">{value}</div>
                  <div className="text-[10px] text-text-muted">{label}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="glass-strong rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span className="text-sm font-semibold text-text-primary">Онлайн сейчас</span>
            </div>
            <p className="text-xs text-text-muted">Скоро здесь появятся активные участники</p>
          </div>
        </div>
      </div>
    </div>
  )
}

'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Users, MessageCircle, FileText, Activity, Crown, Trash2, ShieldOff, Shield, Search, ChevronDown } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import toast from 'react-hot-toast'

type User = {
  id: string; username: string; email?: string; role: string; isOnline: boolean
  streak: number; xp: number; createdAt: string
  _count: { posts: number; sentMessages: number }
}

type Post = {
  id: string; content: string; createdAt: string
  author: { username: string }
  _count: { likes: number; comments: number }
}

type Stats = { totalUsers: number; onlineUsers: number; totalPosts: number; totalMessages: number }

type Tab = 'overview' | 'users' | 'posts'

export function AdminClient({ users, posts, stats }: { users: User[]; posts: Post[]; stats: Stats }) {
  const [tab, setTab] = useState<Tab>('overview')
  const [search, setSearch] = useState('')
  const [localUsers, setLocalUsers] = useState(users)
  const [localPosts, setLocalPosts] = useState(posts)

  const deletePost = async (id: string) => {
    if (!confirm('Удалить пост?')) return
    const res = await fetch(`/api/admin/posts/${id}`, { method: 'DELETE' })
    if (res.ok) {
      setLocalPosts((prev) => prev.filter((p) => p.id !== id))
      toast.success('Пост удалён')
    }
  }

  const changeRole = async (userId: string, role: string) => {
    const res = await fetch(`/api/admin/users/${userId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role }),
    })
    if (res.ok) {
      setLocalUsers((prev) => prev.map((u) => (u.id === userId ? { ...u, role } : u)))
      toast.success('Роль изменена')
    }
  }

  const deleteUser = async (userId: string) => {
    if (!confirm('Удалить пользователя? Это действие нельзя отменить.')) return
    const res = await fetch(`/api/admin/users/${userId}`, { method: 'DELETE' })
    if (res.ok) {
      setLocalUsers((prev) => prev.filter((u) => u.id !== userId))
      toast.success('Пользователь удалён')
    }
  }

  const filteredUsers = localUsers.filter((u) =>
    u.username.toLowerCase().includes(search.toLowerCase()) ||
    (u.email || '').toLowerCase().includes(search.toLowerCase())
  )

  const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'overview', label: 'Обзор', icon: Activity },
    { id: 'users', label: `Пользователи (${stats.totalUsers})`, icon: Users },
    { id: 'posts', label: `Посты (${stats.totalPosts})`, icon: FileText },
  ]

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-yellow-500/20 border border-yellow-500/30 flex items-center justify-center">
            <Crown className="w-5 h-5 text-yellow-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-text-primary">Панель администратора</h1>
            <p className="text-xs text-text-muted">Полный контроль над IsDiscipline</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 glass rounded-xl p-1 mb-6 w-fit">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                tab === id ? 'btn-gradient text-white' : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        {/* Overview tab */}
        {tab === 'overview' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: 'Всего пользователей', value: stats.totalUsers, icon: '👥', color: 'purple' },
                { label: 'Онлайн сейчас', value: stats.onlineUsers, icon: '🟢', color: 'green' },
                { label: 'Всего постов', value: stats.totalPosts, icon: '📝', color: 'blue' },
                { label: 'Всего сообщений', value: stats.totalMessages, icon: '💬', color: 'cyan' },
              ].map(({ label, value, icon }) => (
                <div key={label} className="glass-strong rounded-2xl p-4">
                  <div className="text-2xl mb-2">{icon}</div>
                  <div className="text-2xl font-bold gradient-text mb-0.5">{value}</div>
                  <div className="text-xs text-text-muted">{label}</div>
                </div>
              ))}
            </div>

            <div className="glass-strong rounded-2xl p-4">
              <h3 className="text-sm font-semibold text-text-primary mb-3">Последние регистрации</h3>
              <div className="space-y-2">
                {localUsers.slice(0, 5).map((u) => (
                  <div key={u.id} className="flex items-center gap-3 py-2 border-b border-white/[0.04] last:border-0">
                    <div className="w-8 h-8 rounded-full btn-gradient flex items-center justify-center text-xs font-bold text-white">
                      {u.username[0].toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-text-primary">{u.username}</div>
                      <div className="text-[11px] text-text-muted">{formatDate(u.createdAt)}</div>
                    </div>
                    {u.isOnline && <div className="w-2 h-2 rounded-full bg-green-400" />}
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Users tab */}
        {tab === 'users' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Поиск по имени или email..."
                className="input-dark w-full rounded-xl pl-9 pr-4 py-3 text-sm"
              />
            </div>
            <div className="glass-strong rounded-2xl overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/[0.06]">
                    {['Пользователь', 'Роль', 'Streak', 'XP', 'Посты', 'Действия'].map((h) => (
                      <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-text-muted">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((u) => (
                    <tr key={u.id} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-full btn-gradient flex items-center justify-center text-xs font-bold text-white">
                            {u.username[0].toUpperCase()}
                          </div>
                          <div>
                            <div className="text-sm font-medium text-text-primary">{u.username}</div>
                            {u.email && <div className="text-[11px] text-text-muted">{u.email}</div>}
                          </div>
                          {u.isOnline && <div className="w-1.5 h-1.5 rounded-full bg-green-400" />}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          u.role === 'ADMIN' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                          u.role === 'MODERATOR' ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' :
                          'bg-white/5 text-text-muted border border-white/10'
                        }`}>
                          {u.role}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-orange-400">🔥 {u.streak}</td>
                      <td className="px-4 py-3 text-sm text-yellow-400">⚡ {u.xp}</td>
                      <td className="px-4 py-3 text-sm text-text-secondary">{u._count.posts}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1.5">
                          {u.role !== 'ADMIN' && (
                            <button
                              onClick={() => changeRole(u.id, u.role === 'MODERATOR' ? 'USER' : 'MODERATOR')}
                              className="p-1.5 rounded-lg glass text-text-muted hover:text-accent-purple-light transition-colors"
                              title={u.role === 'MODERATOR' ? 'Снять модератора' : 'Назначить модератором'}
                            >
                              {u.role === 'MODERATOR' ? <ShieldOff className="w-3.5 h-3.5" /> : <Shield className="w-3.5 h-3.5" />}
                            </button>
                          )}
                          {u.role !== 'ADMIN' && (
                            <button
                              onClick={() => deleteUser(u.id)}
                              className="p-1.5 rounded-lg glass text-text-muted hover:text-red-400 transition-colors"
                              title="Удалить"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}

        {/* Posts tab */}
        {tab === 'posts' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
            {localPosts.map((post) => (
              <div key={post.id} className="glass-strong rounded-2xl p-4 flex gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-semibold text-accent-purple-light">{post.author.username}</span>
                    <span className="text-xs text-text-muted">{formatDate(post.createdAt)}</span>
                  </div>
                  <p className="text-sm text-text-secondary line-clamp-2">{post.content}</p>
                  <div className="flex gap-4 mt-2 text-xs text-text-muted">
                    <span>❤️ {post._count.likes}</span>
                    <span>💬 {post._count.comments}</span>
                  </div>
                </div>
                <button
                  onClick={() => deletePost(post.id)}
                  className="p-2 rounded-xl glass text-text-muted hover:text-red-400 transition-colors h-fit"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </motion.div>
        )}
      </div>
    </div>
  )
}

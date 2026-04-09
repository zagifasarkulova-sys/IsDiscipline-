'use client'

import { useState } from 'react'
import { useSession } from 'next-auth/react'
import { motion } from 'framer-motion'
import { Save, Flame, Zap } from 'lucide-react'
import { getInitials } from '@/lib/utils'
import toast from 'react-hot-toast'

export default function ProfilePage() {
  const { data: session } = useSession()
  const [bio, setBio] = useState('')
  const [saving, setSaving] = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      const res = await fetch('/api/users/me', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bio }),
      })
      if (res.ok) toast.success('Сохранено!')
      else toast.error('Ошибка')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-lg mx-auto">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-strong rounded-2xl p-6">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 rounded-2xl btn-gradient flex items-center justify-center text-2xl font-bold text-white glow-purple">
              {session?.user?.name ? getInitials(session.user.name) : '?'}
            </div>
            <div>
              <h1 className="text-xl font-bold gradient-text">{session?.user?.name}</h1>
              <div className="flex gap-3 mt-1">
                <span className="flex items-center gap-1 text-xs text-orange-400">
                  <Flame className="w-3 h-3" /> 0 streak
                </span>
                <span className="flex items-center gap-1 text-xs text-yellow-400">
                  <Zap className="w-3 h-3" /> 0 XP
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">О себе</label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Расскажи о себе..."
                rows={3}
                className="input-dark w-full rounded-xl px-4 py-3 text-sm resize-none"
              />
            </div>
            <button
              onClick={save}
              disabled={saving}
              className="btn-gradient w-full py-3 rounded-xl text-sm font-semibold text-white flex items-center justify-center gap-2 disabled:opacity-60"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Сохраняем...' : 'Сохранить'}
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

'use client'

import { useState } from 'react'
import { signIn } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { Eye, EyeOff, Zap, MessageCircle, Users, Shield } from 'lucide-react'

export default function LandingPage() {
  const [tab, setTab] = useState<'login' | 'register'>('login')
  const [loading, setLoading] = useState(false)
  const [showPass, setShowPass] = useState(false)
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const router = useRouter()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    const res = await signIn('credentials', {
      username: form.username,
      password: form.password,
      redirect: false,
    })
    setLoading(false)
    if (res?.ok) {
      router.push('/feed')
    } else {
      toast.error('Неверный логин или пароль')
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const data = await res.json()
      if (!res.ok) {
        toast.error(data.error || 'Ошибка регистрации')
        setLoading(false)
        return
      }
      toast.success('Аккаунт создан! Входим...')
      const login = await signIn('credentials', {
        username: form.username,
        password: form.password,
        redirect: false,
      })
      setLoading(false)
      if (login?.ok) router.push('/feed')
    } catch {
      toast.error('Ошибка сервера')
      setLoading(false)
    }
  }

  return (
    <div className="relative h-screen w-screen overflow-hidden flex items-center justify-center">
      {/* Animated background orbs */}
      <div className="orb orb-purple" style={{ width: 600, height: 600, top: '-10%', left: '-15%', opacity: 0.5 }} />
      <div className="orb orb-cyan" style={{ width: 500, height: 500, bottom: '-10%', right: '-10%', opacity: 0.4 }} />
      <div className="orb orb-purple" style={{ width: 300, height: 300, top: '50%', left: '60%', opacity: 0.2 }} />

      {/* Grid overlay */}
      <div className="absolute inset-0 opacity-[0.03]" style={{
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)',
        backgroundSize: '40px 40px',
      }} />

      <div className="relative z-10 w-full max-w-md px-4">
        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl btn-gradient mb-4 glow-purple">
            <Zap className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold gradient-text mb-1">IsDiscipline</h1>
          <p className="text-text-secondary text-sm">Социальная сеть для тех, кто добивается</p>
        </motion.div>

        {/* Features row */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="flex justify-center gap-6 mb-8"
        >
          {[
            { icon: MessageCircle, label: 'Чаты' },
            { icon: Users, label: 'Сообщество' },
            { icon: Zap, label: 'Прогресс' },
            { icon: Shield, label: 'Приватность' },
          ].map(({ icon: Icon, label }) => (
            <div key={label} className="flex flex-col items-center gap-1">
              <div className="w-8 h-8 rounded-lg glass flex items-center justify-center">
                <Icon className="w-4 h-4 text-accent-purple-light" />
              </div>
              <span className="text-[11px] text-text-muted">{label}</span>
            </div>
          ))}
        </motion.div>

        {/* Auth card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="glass-strong rounded-2xl p-6"
        >
          {/* Tabs */}
          <div className="flex rounded-xl glass p-1 mb-6">
            {(['login', 'register'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  tab === t
                    ? 'btn-gradient text-white shadow-lg'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                {t === 'login' ? 'Войти' : 'Регистрация'}
              </button>
            ))}
          </div>

          <AnimatePresence mode="wait">
            <motion.form
              key={tab}
              initial={{ opacity: 0, x: tab === 'login' ? -10 : 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: tab === 'login' ? 10 : -10 }}
              transition={{ duration: 0.15 }}
              onSubmit={tab === 'login' ? handleLogin : handleRegister}
              className="space-y-4"
            >
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5">
                  Имя пользователя
                </label>
                <input
                  type="text"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  placeholder="например: focus_pro"
                  className="input-dark w-full rounded-xl px-4 py-3 text-sm"
                  required
                  autoComplete="username"
                />
              </div>

              {tab === 'register' && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <label className="block text-xs font-medium text-text-secondary mb-1.5">
                    Email <span className="text-text-muted">(необязательно)</span>
                  </label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    placeholder="your@email.com"
                    className="input-dark w-full rounded-xl px-4 py-3 text-sm"
                    autoComplete="email"
                  />
                </motion.div>
              )}

              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1.5">
                  Пароль
                </label>
                <div className="relative">
                  <input
                    type={showPass ? 'text' : 'password'}
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    placeholder="минимум 6 символов"
                    className="input-dark w-full rounded-xl px-4 py-3 pr-11 text-sm"
                    required
                    autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass(!showPass)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                  >
                    {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-gradient w-full py-3 rounded-xl text-sm font-semibold text-white disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <span>
                  {loading
                    ? 'Загрузка...'
                    : tab === 'login'
                    ? 'Войти'
                    : 'Создать аккаунт'}
                </span>
              </button>
            </motion.form>
          </AnimatePresence>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-center text-xs text-text-muted mt-4"
        >
          Создавая аккаунт, ты соглашаешься с правилами сообщества
        </motion.p>
      </div>
    </div>
  )
}

'use client'

import { usePathname, useRouter } from 'next/navigation'
import { useSession, signOut } from 'next-auth/react'
import { motion } from 'framer-motion'
import {
  Home, MessageCircle, Users, Crown, Settings,
  LogOut, Zap, Bell, Search
} from 'lucide-react'
import { getInitials } from '@/lib/utils'

const NAV = [
  { href: '/feed', icon: Home, label: 'Лента' },
  { href: '/chat', icon: MessageCircle, label: 'Сообщения' },
  { href: '/explore', icon: Search, label: 'Обзор' },
  { href: '/community', icon: Users, label: 'Сообщество' },
]

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { data: session } = useSession()
  const user = session?.user
  const isAdmin = (user as any)?.role === 'ADMIN'

  return (
    <aside className="flex flex-col h-full w-64 glass border-r border-white/[0.06] p-4 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-3 px-2 mb-8">
        <div className="w-9 h-9 rounded-xl btn-gradient flex items-center justify-center shrink-0">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="font-bold text-sm text-text-primary">IsDiscipline</div>
          <div className="text-[10px] text-text-muted">Социальная сеть</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-1 flex-1">
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = pathname.startsWith(href)
          return (
            <button
              key={href}
              onClick={() => router.push(href)}
              className={`sidebar-item flex items-center gap-3 px-3 py-2.5 text-sm font-medium w-full text-left ${
                active ? 'active text-text-primary' : 'text-text-secondary'
              }`}
            >
              <Icon className={`w-5 h-5 ${active ? 'text-accent-purple-light' : 'text-text-muted'}`} />
              {label}
              {href === '/chat' && (
                <span className="ml-auto bg-accent-purple text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                  3
                </span>
              )}
            </button>
          )
        })}

        {isAdmin && (
          <button
            onClick={() => router.push('/admin')}
            className={`sidebar-item flex items-center gap-3 px-3 py-2.5 text-sm font-medium w-full text-left mt-2 ${
              pathname.startsWith('/admin') ? 'active text-text-primary' : 'text-text-secondary'
            }`}
          >
            <Crown className={`w-5 h-5 ${pathname.startsWith('/admin') ? 'text-yellow-400' : 'text-text-muted'}`} />
            Админ
            <span className="ml-auto text-[10px] bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 px-1.5 py-0.5 rounded-full font-semibold">
              ADMIN
            </span>
          </button>
        )}
      </nav>

      {/* User card */}
      <div className="mt-4 border-t border-white/[0.06] pt-4">
        <div className="flex items-center gap-3 px-2 mb-3">
          <div className="relative shrink-0">
            <div className="w-9 h-9 rounded-full btn-gradient flex items-center justify-center text-sm font-bold text-white">
              {user?.name ? getInitials(user.name) : '?'}
            </div>
            <div className="online-dot absolute -bottom-0.5 -right-0.5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-semibold text-text-primary truncate">{user?.name}</div>
            <div className="text-[11px] text-text-muted">В сети</div>
          </div>
          <Bell className="w-4 h-4 text-text-muted hover:text-text-secondary cursor-pointer shrink-0" />
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => router.push('/profile')}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl glass text-xs text-text-secondary hover:text-text-primary transition-colors"
          >
            <Settings className="w-3.5 h-3.5" />
            Профиль
          </button>
          <button
            onClick={() => signOut({ callbackUrl: '/' })}
            className="flex items-center justify-center w-9 h-9 rounded-xl glass text-text-muted hover:text-red-400 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  )
}

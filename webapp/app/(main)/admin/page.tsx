export const dynamic = 'force-dynamic'

import { redirect } from 'next/navigation'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'
import { AdminClient } from './client'

export default async function AdminPage() {
  const session = await getServerSession(authOptions)
  if (!session || (session.user as any).role !== 'ADMIN') redirect('/feed')

  const [users, posts, totalMessages] = await Promise.all([
    prisma.user.findMany({
      orderBy: { createdAt: 'desc' },
      take: 50,
      select: {
        id: true, username: true, email: true, role: true, isOnline: true,
        streak: true, xp: true, createdAt: true,
        _count: { select: { posts: true, sentMessages: true } },
      },
    }),
    prisma.post.findMany({
      orderBy: { createdAt: 'desc' },
      take: 20,
      include: { author: { select: { username: true } }, _count: { select: { likes: true, comments: true } } },
    }),
    prisma.message.count(),
  ])

  const stats = {
    totalUsers: await prisma.user.count(),
    onlineUsers: await prisma.user.count({ where: { isOnline: true } }),
    totalPosts: await prisma.post.count(),
    totalMessages,
  }

  return <AdminClient users={users as any} posts={posts as any} stats={stats} />
}

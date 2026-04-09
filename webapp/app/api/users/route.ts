import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'

export async function GET(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 })

  const q = req.nextUrl.searchParams.get('q')
  try {
    const users = await prisma.user.findMany({
      where: q ? { username: { contains: q, mode: 'insensitive' } } : undefined,
      take: 20,
      select: { id: true, username: true, avatar: true, bio: true, isOnline: true, streak: true, xp: true },
    })
    return NextResponse.json(users)
  } catch {
    return NextResponse.json({ error: 'Ошибка' }, { status: 500 })
  }
}

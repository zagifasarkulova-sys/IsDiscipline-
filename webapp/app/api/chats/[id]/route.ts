import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'

export async function GET(_req: NextRequest, { params }: { params: { id: string } }) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 })

  try {
    const chat = await prisma.chat.findUnique({
      where: { id: params.id },
      include: {
        members: { include: { user: { select: { id: true, username: true, isOnline: true } } } },
      },
    })
    if (!chat) return NextResponse.json({ error: 'Чат не найден' }, { status: 404 })
    return NextResponse.json(chat)
  } catch {
    return NextResponse.json({ error: 'Ошибка' }, { status: 500 })
  }
}

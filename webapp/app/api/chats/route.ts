import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'

export async function GET() {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 })

  try {
    const chats = await prisma.chat.findMany({
      where: { members: { some: { userId: session.user.id } } },
      include: {
        members: { include: { user: { select: { id: true, username: true, isOnline: true } } } },
        messages: {
          orderBy: { createdAt: 'desc' },
          take: 1,
          include: { sender: { select: { username: true } } },
        },
      },
      orderBy: { createdAt: 'desc' },
    })
    return NextResponse.json(chats)
  } catch {
    return NextResponse.json({ error: 'Ошибка' }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 })

  try {
    const { targetUserId, type = 'DIRECT', name } = await req.json()

    if (type === 'DIRECT') {
      // Check if direct chat already exists
      const existing = await prisma.chat.findFirst({
        where: {
          type: 'DIRECT',
          AND: [
            { members: { some: { userId: session.user.id } } },
            { members: { some: { userId: targetUserId } } },
          ],
        },
      })
      if (existing) return NextResponse.json(existing)

      const chat = await prisma.chat.create({
        data: {
          type: 'DIRECT',
          members: {
            create: [{ userId: session.user.id }, { userId: targetUserId }],
          },
        },
      })
      return NextResponse.json(chat, { status: 201 })
    }

    const chat = await prisma.chat.create({
      data: {
        type: 'GROUP',
        name,
        members: { create: { userId: session.user.id } },
      },
    })
    return NextResponse.json(chat, { status: 201 })
  } catch {
    return NextResponse.json({ error: 'Ошибка' }, { status: 500 })
  }
}

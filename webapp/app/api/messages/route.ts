import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'

export async function GET(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 })

  const chatId = req.nextUrl.searchParams.get('chatId')
  if (!chatId) return NextResponse.json({ error: 'chatId required' }, { status: 400 })

  try {
    const messages = await prisma.message.findMany({
      where: { chatId },
      orderBy: { createdAt: 'asc' },
      take: 100,
      include: { sender: { select: { id: true, username: true, avatar: true } } },
    })
    return NextResponse.json(messages)
  } catch {
    return NextResponse.json({ error: 'Ошибка' }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 })

  try {
    const { chatId, content, type = 'TEXT', fileUrl, duration } = await req.json()
    if (!chatId) return NextResponse.json({ error: 'chatId required' }, { status: 400 })

    const message = await prisma.message.create({
      data: {
        chatId,
        senderId: session.user.id,
        content: content?.trim(),
        type,
        fileUrl,
        duration,
      },
      include: { sender: { select: { id: true, username: true, avatar: true } } },
    })

    return NextResponse.json(message, { status: 201 })
  } catch {
    return NextResponse.json({ error: 'Ошибка' }, { status: 500 })
  }
}

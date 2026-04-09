import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'

export async function GET() {
  try {
    const posts = await prisma.post.findMany({
      orderBy: { createdAt: 'desc' },
      take: 50,
      include: {
        author: { select: { id: true, username: true, avatar: true, streak: true, xp: true } },
        likes: { select: { userId: true } },
        comments: {
          include: { user: { select: { id: true, username: true } } },
          orderBy: { createdAt: 'asc' },
        },
        _count: { select: { likes: true, comments: true } },
      },
    })
    return NextResponse.json(posts)
  } catch {
    return NextResponse.json({ error: 'Ошибка сервера' }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 })

  try {
    const { content, imageUrl } = await req.json()
    if (!content?.trim()) return NextResponse.json({ error: 'Пустой пост' }, { status: 400 })

    const post = await prisma.post.create({
      data: { content: content.trim(), imageUrl, authorId: session.user.id },
      include: {
        author: { select: { id: true, username: true, avatar: true, streak: true, xp: true } },
        likes: { select: { userId: true } },
        comments: { include: { user: { select: { id: true, username: true } } } },
        _count: { select: { likes: true, comments: true } },
      },
    })

    // Award XP for posting
    await prisma.user.update({
      where: { id: session.user.id },
      data: { xp: { increment: 10 } },
    })

    return NextResponse.json(post, { status: 201 })
  } catch {
    return NextResponse.json({ error: 'Ошибка сервера' }, { status: 500 })
  }
}

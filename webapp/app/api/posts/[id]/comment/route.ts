import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'

export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 })

  try {
    const { content } = await req.json()
    if (!content?.trim()) return NextResponse.json({ error: 'Пустой комментарий' }, { status: 400 })

    const comment = await prisma.comment.create({
      data: { content: content.trim(), userId: session.user.id, postId: params.id },
      include: { user: { select: { id: true, username: true } } },
    })

    return NextResponse.json(comment, { status: 201 })
  } catch {
    return NextResponse.json({ error: 'Ошибка' }, { status: 500 })
  }
}

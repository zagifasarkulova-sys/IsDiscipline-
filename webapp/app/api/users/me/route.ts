import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/db'

export async function GET() {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 })
  const user = await prisma.user.findUnique({
    where: { id: session.user.id },
    select: { id: true, username: true, email: true, bio: true, avatar: true, streak: true, xp: true, role: true },
  })
  return NextResponse.json(user)
}

export async function PATCH(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 })
  const { bio, avatar } = await req.json()
  const user = await prisma.user.update({
    where: { id: session.user.id },
    data: { bio, avatar },
    select: { id: true, username: true, bio: true, avatar: true },
  })
  return NextResponse.json(user)
}

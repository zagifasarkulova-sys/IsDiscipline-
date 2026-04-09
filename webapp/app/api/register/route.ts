import { NextRequest, NextResponse } from 'next/server'
import bcrypt from 'bcryptjs'
import { prisma } from '@/lib/db'

export async function POST(req: NextRequest) {
  try {
    const { username, email, password } = await req.json()

    if (!username || !password) {
      return NextResponse.json({ error: 'Username и пароль обязательны' }, { status: 400 })
    }

    if (username.length < 3) {
      return NextResponse.json({ error: 'Username минимум 3 символа' }, { status: 400 })
    }

    if (password.length < 6) {
      return NextResponse.json({ error: 'Пароль минимум 6 символов' }, { status: 400 })
    }

    const existing = await prisma.user.findFirst({
      where: { OR: [{ username }, ...(email ? [{ email }] : [])] },
    })

    if (existing) {
      return NextResponse.json({ error: 'Пользователь уже существует' }, { status: 409 })
    }

    const hashed = await bcrypt.hash(password, 12)
    const user = await prisma.user.create({
      data: { username, email: email || undefined, password: hashed },
      select: { id: true, username: true, email: true, role: true },
    })

    return NextResponse.json(user, { status: 201 })
  } catch {
    return NextResponse.json({ error: 'Ошибка сервера' }, { status: 500 })
  }
}

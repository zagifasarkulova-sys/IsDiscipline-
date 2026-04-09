import { withAuth } from 'next-auth/middleware'

export default withAuth({
  pages: {
    signIn: '/',
  },
})

export const config = {
  matcher: ['/feed/:path*', '/chat/:path*', '/admin/:path*', '/profile/:path*', '/explore/:path*', '/community/:path*'],
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable static generation — all pages are dynamic (we use DB)
  staticPageGenerationTimeout: 1,
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '**' },
    ],
  },
  experimental: {
    serverComponentsExternalPackages: ['@prisma/client', 'bcryptjs', 'socket.io', 'socket.io-client'],
  },
  // Ignore type errors during build (for Render deploy)
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
}

export default nextConfig

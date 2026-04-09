FROM node:20-alpine

# Install OpenSSL required by Prisma
RUN apk add --no-cache openssl openssl-dev libc6-compat

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --no-audit --no-fund --prefer-offline || npm install --no-audit --no-fund

# Copy prisma schema and generate client
COPY prisma ./prisma/
RUN npx prisma generate

# Copy all source files
COPY . .

# Build Next.js (dummy vars needed at build time only)
ENV NEXTAUTH_SECRET=build-time-secret
ENV NEXTAUTH_URL=http://localhost:3000
ENV DATABASE_URL=postgresql://dummy:dummy@localhost:5432/dummy
ENV NODE_OPTIONS="--max-old-space-size=512"

RUN npm run build

EXPOSE 3000

# Run migrations then start server
CMD npx prisma db push --accept-data-loss && node server.js

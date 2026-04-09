FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy prisma schema and generate client
COPY prisma ./prisma/
RUN npx prisma generate

# Copy all source files
COPY . .

# Build Next.js
RUN npm run build

EXPOSE 3000

# Run migrations then start server
CMD npx prisma migrate deploy && node server.js

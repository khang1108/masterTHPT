FROM node:22.17.0-alpine3.21 AS base
WORKDIR /app

# deps
FROM base AS deps
COPY package*.json ./
RUN npm ci

# build
FROM base AS build
COPY package*.json ./
COPY --from=deps /app/node_modules ./node_modules
COPY prisma ./prisma
COPY tsconfig*.json ./
COPY nest-cli.json ./
COPY src ./src

RUN npx prisma generate
RUN npm run build

# production deps only
FROM base AS prod-deps
COPY package*.json ./
RUN npm ci --omit=dev
COPY prisma ./prisma

RUN npx prisma generate

# runner
FROM node:22.17.0-alpine3.21 AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3001

RUN apk add --no-cache openssl

COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY --from=build /app/prisma ./prisma
COPY package*.json ./

EXPOSE 3001
CMD ["node", "dist/main.js"]
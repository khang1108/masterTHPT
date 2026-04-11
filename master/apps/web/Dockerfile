FROM node:22.17.0-alpine3.21 AS base
WORKDIR /app

# deps
FROM base AS deps
COPY package*.json ./
RUN npm ci

# build
FROM base AS build
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# runner
FROM node:22.17.0-alpine3.21 AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
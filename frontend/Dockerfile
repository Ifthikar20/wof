# syntax=docker/dockerfile:1.7
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM node:22-alpine AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
# Public (non-secret) values baked into the browser bundle and CSP at build time.
ARG NEXT_PUBLIC_MEDIA_HOST=""
ARG NEXT_PUBLIC_UPLOAD_HOST=""
ARG NEXT_PUBLIC_TURNSTILE_SITE_KEY=""
ARG NEXT_PUBLIC_AUTH_PROMPT_DELAY_MS="45000"
ENV NEXT_PUBLIC_MEDIA_HOST=$NEXT_PUBLIC_MEDIA_HOST \
    NEXT_PUBLIC_UPLOAD_HOST=$NEXT_PUBLIC_UPLOAD_HOST \
    NEXT_PUBLIC_TURNSTILE_SITE_KEY=$NEXT_PUBLIC_TURNSTILE_SITE_KEY \
    NEXT_PUBLIC_AUTH_PROMPT_DELAY_MS=$NEXT_PUBLIC_AUTH_PROMPT_DELAY_MS
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
RUN addgroup -S -g 10001 wof && adduser -S -u 10001 -G wof wof
COPY --from=build --chown=root:root /app/.next/standalone ./
COPY --from=build --chown=root:root /app/.next/static ./.next/static
COPY --from=build --chown=root:root /app/public ./public
RUN mkdir -p .next/cache && chown wof:wof .next/cache
USER wof
EXPOSE 3000
CMD ["node", "server.js"]

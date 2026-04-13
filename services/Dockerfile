FROM node:20-alpine

ARG SERVICE
ENV SERVICE=${SERVICE}
ENV NODE_ENV=production

WORKDIR /app/services
COPY services/package*.json ./
RUN npm ci --omit=dev

WORKDIR /app
COPY services ./services

CMD ["sh", "-c", "node services/${SERVICE}/src/index.js"]

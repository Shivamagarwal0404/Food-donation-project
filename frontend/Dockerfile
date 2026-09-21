# =============================================================================
# FoodShare — Frontend Dockerfile
# Node 20 / React / Vite
# =============================================================================

FROM node:20-alpine

WORKDIR /app

# Copy package files first (Docker layer cache optimization)
COPY package.json package-lock.json* ./

RUN npm ci

# Copy source
COPY . .

EXPOSE 5173

# Default: Vite dev server. Override with `npm run build` + nginx in production.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

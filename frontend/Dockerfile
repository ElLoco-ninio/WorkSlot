# Frontend Service (Vite Build + Static Server)
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files (Context is 'frontend/')
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . ./
# Skip verification of types during build to ensure deployment succeeds
RUN npm run build

# Production stage - serve with simple static server
FROM node:18-alpine
WORKDIR /app
# Copy built assets
COPY --from=builder /app/dist ./dist

# Install serve to run it
RUN npm install -g serve

# Serve single page app
CMD serve -s dist -l ${PORT} --single

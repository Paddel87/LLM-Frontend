# Multi-stage build für das Frontend
FROM node:18-alpine AS builder

# Arbeitsverzeichnis setzen
WORKDIR /app

# Package files kopieren
COPY package*.json ./

# Dependencies installieren
RUN npm ci --only=production

# Source code kopieren
COPY . .

# Build erstellen
RUN npm run build

# Production stage
FROM nginx:alpine

# Nginx-Konfiguration kopieren
COPY nginx.conf /etc/nginx/nginx.conf

# Build-Artefakte kopieren
COPY --from=builder /app/dist /usr/share/nginx/html

# Port exponieren
EXPOSE 80

# Nginx starten
CMD ["nginx", "-g", "daemon off;"] 
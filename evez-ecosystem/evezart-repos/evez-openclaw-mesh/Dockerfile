FROM node:20-alpine

WORKDIR /app

# Install OpenClaw + deps
RUN npm install -g @openclaw/cli@latest

# Install Playwright deps for browser tool
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    harfbuzz \
    ca-certificates \
    ttf-freefont

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    CHROMIUM_PATH=/usr/bin/chromium-browser

# Copy config and workspace
COPY openclaw.json /root/.openclaw/openclaw.json
COPY . /workspace

# Health check endpoint
RUN echo '#!/bin/sh\ncurl -f http://localhost:18789/health || exit 1' > /healthcheck.sh \
    && chmod +x /healthcheck.sh

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD /healthcheck.sh

EXPOSE 18789

CMD ["openclaw", "--port", "18789", "--profile", "goblin"]
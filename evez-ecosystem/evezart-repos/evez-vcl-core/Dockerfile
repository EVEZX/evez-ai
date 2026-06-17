FROM node:20-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
COPY src/ ./src/
ENV VCL_ID=fire
ENV NODE_ENV=production
CMD ["node", "src/main.js"]

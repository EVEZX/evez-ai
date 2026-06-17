# EVEZ Discord Bot

Free AI bot for your Discord server. Uses the EVEZ API (99% cheaper than OpenAI).

## Setup
1. Create a Discord bot at [discord.com/developers](https://discord.com/developers)
2. Get a free EVEZ API key at [evez-api2.fly.dev/signup](https://evez-api2.fly.dev/signup)
3. Deploy:
```
DISCORD_TOKEN=your-token EVEZ_API_KEY=your-evez-key DISCORD_APP_ID=your-app-id node bot.js
```

## Commands
- `/ask <prompt>` — Ask EVEZ anything
- `/ask <prompt> model: Code` — Use a specific model
- `@EVEZ <prompt>` — Mention the bot to chat
- `/models` — List available models

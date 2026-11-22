# TomoBao Bot 🤖

A multipurpose Python Discord bot for the TomoBao community.

## Commands

| Command | Description |
| --- | --- |
| `/ping` | Check latency |
| `/help` | List commands |
| `/userinfo` | Show member details |
| `/serverinfo` | Show server details |
| `/avatar` | Show member avatar |
| `/botinfo` | Show bot information |
| `/clear` | Delete 1–50 messages (Manage Messages permission required) |

## Setup

1. Install Python 3.10 or newer.
2. Create a Discord application and bot in the [Discord Developer Portal](https://discord.com/developers/applications).
3. Invite it with `bot` and `applications.commands` scopes. Grant only the permissions you need (Manage Messages for `/clear`).
4. Copy `.env.example` to `.env`. Set `DISCORD_TOKEN` and optionally `GUILD_ID`.
5. Run:

   ```bash
   python -m pip install -r requirements.txt
   python bot.py
   ```

6. Set `SYNC_ON_STARTUP=true` for one restart to register commands; set it back to `false` afterward. If `GUILD_ID=0`, synchronization is global and may take time to propagate.

## Security

Never commit `.env`, tokens, or credentials. Keep the bot's permissions minimal. Use a separate bot token from Toe Bot.

## Hosting

Run on Ubuntu/Debian in a Python virtual environment or a dedicated Proxmox VM. Use a process supervisor to restart it if needed; avoid running multiple copies of the same bot.

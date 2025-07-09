# Vikrant Security Bot 🔐

A powerful anti-nuke and moderation bot for Discord.

## Features

- `/setup` command to auto-create or manually configure:
  - Admin channel (`#vikrant-admin`)
  - Complaint channel (`#complaints`)

- `/complain` command to submit anonymous complaints
  - Complaints are sent directly to the configured complaint channel.
  - Supports dynamic complaint channel lookup per server.

- `/lockdown` & `/unlock` commands
  - Lock all text channels in the server (`@everyone` cannot send messages)
  - Unlock previously locked channels
  - Useful during raids or server-wide emergencies

## Setup

1. Invite Vikrant with the [official invite link](https://discord.com/oauth2/authorize?client_id=1390545148139802735&permissions=8&scope=bot+applications.commands).

2. Run `/setup` to initialize the admin and complaint channels.

3. Use `/lockdown` and `/unlock` for emergency moderation control.

4. Users can submit complaints using `/complain`.

## Project Structure

- `/cogs/setup.py` — Interactive setup command
- `/cogs/complaints.py` — Complaint submission command
- `/cogs/lockdown.py` — Lockdown and unlock all channels
- `/data/config.json` — Stores per-server configuration

## Deployment

Currently hosted on Render for 24/7 uptime.

---


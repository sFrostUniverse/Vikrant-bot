# Vikrant Security Bot 🔐

A powerful anti-nuke and moderation bot for Discord.

## Features

- `/setup` command to auto-create or manually configure:
  - Admin channel (`#vikrant-admin`)
  - Complaint channel (`#complaints`)

- `/complain` command to submit anonymous complaints
  - Complaints are sent directly to the configured complaint channel.
  - Supports dynamic complaint channel lookup per server.

## Setup

1. Invite Vikrant with the [official invite link](https://discord.com/oauth2/authorize?client_id=1390545148139802735&permissions=8&scope=bot+applications.commands).

2. Run `/setup` to initialize the admin and complaint channels.

3. Users can now submit complaints using `/complain`.

## Project Structure

- `/cogs/setup.py` — Interactive setup command
- `/cogs/complaints.py` — Complaint submission command
- `/data/config.json` — Stores per-server configuration

## Deployment

Currently hosted on Render for 24/7 uptime.

---

Feel free to customize or let me know if you want me to write a fuller README with installation instructions and more!


# Vikrant Security Bot 🔐

A powerful, customizable **anti-nuke and moderation bot** designed to protect your Discord server from raids, mass destruction, and abuse — with real-time defense features and user-friendly setup.

---

## ⚙️ Features

### 🛡️ Anti-Nuke System
- Real-time monitoring of:
  - Mass bans
  - Role deletions
  - Channel deletions
- Auto-punishes attackers based on your config:
  - `ban`, `kick`, or `strip roles`
- Trust system to exempt selected admins

### 🔧 `/setup`
- One command to initialize:
  - Admin channel (`#vikrant-admin`) for security alerts
  - Complaint channel (`#complaints`) for user reports
- Supports **auto-create** or **manual selection** of existing channels
- Saves configuration into `config.json` per server:
  - `trusted_admins`, `auto_punish`, `punishment_type`, etc.

### 📩 `/complain`
- Anonymous complaint system
- Messages are routed to the configured complaint channel
- Keeps users safe from retaliation

### 🚨 `/lockdown` & `/unlock`
- Lock all text channels to prevent messages from @everyone
- Restore normal access after the threat is gone
- Effective during raids or emergencies

---

## 🧩 Project Structure

```
vikrant/
├── cogs/
│   ├── setup.py              # Interactive setup command
│   ├── complaints.py         # Anonymous complaint submission
│   ├── lockdown.py           # Lockdown/unlock commands
│   └── audit_log_watcher.py  # Anti-nuke protection core
├── data/
│   └── config.json           # Per-server configuration store
├── main.py                   # Bot startup and cog loading
└── readme.md
```

---

## 🚀 Setup Instructions

1. **Invite Vikrant** using [this link](https://discord.com/oauth2/authorize?client_id=1390545148139802735&permissions=8&scope=bot+applications.commands)

2. Run `/setup` to configure channels and protection settings

3. Use:
   - `/complain` to allow anonymous complaints
   - `/lockdown` and `/unlock` for emergency control

4. Customize your config in `data/config.json` (if needed)

---

## 🌐 Hosting

Vikrant is currently hosted on **Render.com** for 24/7 uptime.  
You may self-host or fork as needed — just ensure your bot token and permissions are secure.

---

## 💬 Support & Contributions

Want to contribute, report bugs, or suggest features?  
Reach out to the creator Sehaj or fork the repo!

---

*Built with ❤️ to protect Discord communities from harm.*

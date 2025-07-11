
# Vikrant Security Bot 🔐

A powerful, customizable **anti-nuke and moderation bot** designed to protect your Discord server from raids, mass destruction, link spam, and abuse — with real-time defense and a friendly setup flow.

---

## ⚙️ Features

### 🛡️ Anti-Nuke System
- Real-time monitoring of destructive actions:
  - 🚫 Mass bans
  - 🧨 Role deletions
  - 📁 Channel deletions
- Auto-punishes attackers using your chosen method:
  - `ban`, `kick`, or `remove roles`
- Trust system: whitelist selected admins from protection triggers

### 🔧 `/setup`
- One interactive command to configure the bot
- Options to:
  - **Auto-create** admin + complaint channels
  - **Manually select** existing ones
- Saves all settings to `config.json`:
  - `admin_log_channel`, `complaint_channel`, `trusted_admins`, `auto_punish`, and more

### 🔗 Link Spam Protection
- Detects users posting suspicious links across multiple channels
- Instantly **kicks** the user to prevent mass scams
- Logs the action in the admin channel

### 📩 `/complain`
- Submit anonymous complaints
- Delivered directly to your configured complaint channel
- Ensures safety and privacy for your community

### 🚨 `/lockdown` & `/unlock`
- Instantly locks all text channels for @everyone
- Useful during raids, floods, or emergencies
- `/unlock` restores normal access



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

## 🚀 How to Use

1. **Invite Vikrant** to your server  
   [Click here to invite](https://discord.com/oauth2/authorize?client_id=1390545148139802735&permissions=8&scope=bot+applications.commands)

2. Run `/setup`  
   - Configure your admin and complaint channels

3. Features available after setup:
   - `/complain` for anonymous reporting
   - `/lockdown` and `/unlock` for emergency control
   - Automatic anti-nuke protection
   - Link spam detection

4. (Optional) Customize your config in `data/config.json`

---

## 🌐 Hosting & Deployment

- Hosted via **Render.com** for 24/7 uptime  
- Self-hosting is supported — just install dependencies, load your `.env` and run `main.py`

---

## 💬 Support & Contributions

Want to contribute or suggest features?  
Reach out to the creator — **she/her**, aka the builder of this bot, or fork the repository on GitHub.

> GitHub: [https://github.com/sFrostUniverse/Vikrant-bot](https://github.com/sFrostUniverse/Vikrant-bot)

---

*Built with 💙 to defend Discord communities from harm — safely, professionally, and stylishly.*

import json
import os

CONFIG_FILE = "data/config.json"

# Ensure file exists
if not os.path.exists(CONFIG_FILE):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump({}, f)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def get_news_channel(guild_id):
    config = load_config()
    guild_config = config.get(str(guild_id))
    return int(guild_config["news_channel"]) if guild_config else None

def set_news_channel(guild_id, channel_id):
    config = load_config()
    config[str(guild_id)] = {"news_channel": int(channel_id)}  # ✅ fix here
    save_config(config)

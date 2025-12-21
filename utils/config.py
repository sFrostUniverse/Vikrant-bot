import json, os

CONFIG_FILE = "data/config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_guild_config(guild_id: int):
    data = load_config()
    return data.get(str(guild_id))

def is_setup_owner_or_server_owner(interaction):
    guild_data = get_guild_config(interaction.guild.id)
    if not guild_data:
        return False

    return (
        interaction.user.id == guild_data.get("setup_owner_id")
        or interaction.user.id == interaction.guild.owner_id
    )

import json
import os
from discord.app_commands import CheckFailure

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

os.makedirs(DATA_DIR, exist_ok=True)


def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({}, f)

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
        raise CheckFailure("Server is not configured.")

    if (
        interaction.user.id != guild_data.get("setup_owner_id")
        and interaction.user.id != interaction.guild.owner_id
    ):
        raise CheckFailure("You are not authorized to do this.")

    return True

import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests, os, logging
from bs4 import BeautifulSoup
from utils.config import load_config


class NewsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fetch_news.start()

    def cog_unload(self):
        self.fetch_news.cancel()

    @app_commands.command(name="news", description="Fetch top headlines from multiple sources")
    async def manual_news(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embeds = self.get_all_headlines()

        if embeds:
            for embed in embeds:
                await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("⚠️ Unable to fetch news at the moment. Please try again later.")

    def get_all_headlines(self):
        return self.scrape_indian_express(limit=2) + self.scrape_ndtv(limit=2)

    def scrape_indian_express(self, limit=2):
        url = "https://indianexpress.com/"
        headers = {"User-Agent": "Mozilla/5.0"}
        headlines = []

        try:
            res = requests.get(url, headers=headers, timeout=5)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            articles = soup.select("div.main-story, div.lead-story, div.other-article")
        except Exception as e:
            logging.error(f"[IndianExpress] Failed: {e}")
            return []

        for article in articles:
            link_tag = article.find("a", href=True)
            if not link_tag:
                continue

            title = link_tag.get_text(strip=True)
            link = link_tag["href"]
            if not title or not link.startswith("http"):
                continue

            img_tag = article.find("img")
            img_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else None

            embed = discord.Embed(
                title=title,
                url=link,
                description="📰 Source: Indian Express",
                color=discord.Color.orange()
            )
            if img_url:
                embed.set_thumbnail(url=img_url)
            embed.set_footer(text="FrostNews 24/7 • IndianExpress.com")
            headlines.append(embed)

            if len(headlines) >= limit:
                break

        return headlines

    def scrape_ndtv(self, limit=2):
        url = "https://www.ndtv.com/latest"
        headers = {"User-Agent": "Mozilla/5.0"}
        headlines = []

        try:
            res = requests.get(url, headers=headers, timeout=5)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            articles = soup.select("div.new_storylising > ul > li")
        except Exception as e:
            logging.error(f"[NDTV] Failed: {e}")
            return []

        for article in articles:
            link_tag = article.find("a", href=True)
            if not link_tag:
                continue

            title = link_tag.get_text(strip=True)
            link = link_tag["href"]
            if not title or not link.startswith("http"):
                continue

            img_tag = article.find("img")
            img_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else None

            embed = discord.Embed(
                title=title,
                url=link,
                description="📰 Source: NDTV",
                color=discord.Color.dark_blue()
            )
            if img_url:
                embed.set_thumbnail(url=img_url)
            embed.set_footer(text="FrostNews 24/7 • NDTV.com")
            headlines.append(embed)

            if len(headlines) >= limit:
                break

        return headlines

    @tasks.loop(minutes=15)
    async def fetch_news(self):
        logging.info("Auto-fetching headlines...")
        embeds = self.get_all_headlines()

        if not embeds:
            logging.warning("No headlines to send.")
            return

        config = load_config()
        for guild_id, guild_data in config.items():
            channel_id = int(guild_data["news_channel"])
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    for embed in embeds:
                        await channel.send(embed=embed)
                    logging.info(f"Headlines sent to {channel.guild.name} ({channel.name})")
                except Exception as e:
                    logging.error(f"Failed to send to {channel_id}: {e}")


async def setup(bot):
    await bot.add_cog(NewsCog(bot))

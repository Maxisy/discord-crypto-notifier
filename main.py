import asyncio
import json
import os

import aiohttp
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.app_commands import Choice


class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync()
            self.synced = True
        print(f"The bot has logged in as {self.user}.")


client = aclient()
tree = app_commands.CommandTree(client)
load_dotenv("./.env")


@tree.command(name="notify", description="Notifies in DMs or on this channel when a coin's price ($) is below/above specified price.")
@app_commands.describe(
    ticker="Coin's ticker (e.g. BTC).",
    position="Should the bot notify you when the price is below or above specified price.",
    price="The price to be notified about.",
    where="Where should the bot notify you about the price change. If you select DMs make sure to open the DMs from users on this server."
)
@app_commands.choices(position=[
    Choice(name="above", value=1),
    Choice(name="below", value=2)
], where=[
    Choice(name="DMs", value=1),
    Choice(name="this channel", value=2),
    Choice(name="both", value=3)
])
async def notify(interaction: discord.Interaction, ticker: str, position: Choice[int], price: str, where: Choice[int]):
    await interaction.response.defer(ephemeral=True)

    try:
        if "," in price:
            float_price = float(price.replace(",", "."))
        else:
            float_price = float(price)
    except ValueError:
        await interaction.followup.send("Specify a valid number.", ephemeral=True)
        return

    coingecko_token_list_endpoint = "https://api.coingecko.com/api/v3/coins/list?include_platform=false"
    async with aiohttp.ClientSession() as cs:
        async with cs.get(coingecko_token_list_endpoint) as r:
            token_list_r = await r.json()

    coin_id = ""
    for obj in token_list_r:
        if obj["symbol"].lower() == ticker.lower():
            coin_id = obj["id"].lower()

    if coin_id == "":
        await interaction.followup.send(f"The symbol {ticker.upper()} is not valid.", ephemeral=True)
        return

    if position.value == 1:
        await interaction.followup.send(f"I will notify you when {ticker.upper()} price is above ${float_price}.")
    else:
        await interaction.followup.send(f"I will notify you when {ticker.upper()} price is below ${float_price}.")

    coingecko_info_endpoint = "https://api.coingecko.com/api/v3/coins/" + coin_id
    while True:
        async with aiohttp.ClientSession() as cs:
            async with cs.get(coingecko_info_endpoint) as r:
                info_r = await r.json()

        with open("r.json", "w") as f:
            json.dump(info_r, f, indent=4)
        usd_price = float(info_r["market_data"]["current_price"]["usd"])

        if position.value == 1:  # above
            if usd_price > float_price:
                if where.value == 1:  # DMs
                    user = client.get_user(interaction.user.id)
                    await user.send(f"Price of {ticker.upper()} is above ${float_price}!\n\nData provided by <https://www.coingecko.com/>")
                elif where.value == 2:  # channel
                    await interaction.channel.send(f"<@{interaction.user.id}> Price of {ticker.upper()} is above ${float_price}!\n\nData provided by <https://www.coingecko.com/>")
                else:  # both
                    user = client.get_user(interaction.user.id)
                    await user.send(f"Price of {ticker.upper()} is above ${float_price}!\n\nData provided by <https://www.coingecko.com/>")
                    await interaction.channel.send(f"<@{interaction.user.id}> Price of {ticker.upper()} is above ${float_price}!\n\nData provided by <https://www.coingecko.com/>")
                return
        else:  # below
            if usd_price < float_price:
                if where.value == 1:  # DMs
                    user = client.get_user(interaction.user.id)
                    await user.send(f"Price of {ticker.upper()} is below ${float_price}!\n\nData provided by https://www.coingecko.com/")
                elif where.value == 2:  # channel
                    await interaction.channel.send(f"<@{interaction.user.id}> Price of {ticker.upper()} is below ${float_price}!\n\nData provided by <https://www.coingecko.com/>")
                else:  # both
                    user = client.get_user(interaction.user.id)
                    await user.send(f"Price of {ticker.upper()} is below ${float_price}!\n\nData provided by <https://www.coingecko.com/>")
                    await interaction.channel.send(f"<@{interaction.user.id}> Price of {ticker.upper()} is below ${float_price}!\n\nData provided by <https://www.coingecko.com/>")
                return
        await asyncio.sleep(2)

client.run(os.getenv("DISCORD_TOKEN"))

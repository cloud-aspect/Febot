"""Discord bot for the ferrous few discord"""
import os
import sys

from commands.commandrouter import CommandRouter
from dotenv import load_dotenv
import discord

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client(intents=discord.Intents.all())

cr = CommandRouter(client)

print(cr.comlist.keys())



@client.event
async def on_ready():
    """prints message to show the bot is ready to receive messages"""
    print(f'{client.user} is connected\n')

@client.event
async def on_message(message):
    """send new messages to the router"""
    if message.author == client.user:
        return

    await cr.route_messsage(message)

@client.event
async def on_raw_reaction_add(payload):
    """send emojis added/removed to the router"""
    if payload.member == client.user:
        return

    await cr.route_emoji(payload)

client.run(TOKEN)

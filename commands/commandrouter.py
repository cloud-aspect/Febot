
"""This file implements a commmandrouter for a discord bot"""
import os
import json
import shlex
from collections import defaultdict

from commands.command import Command, InvocationCommand
from commands.instances import *

from dotenv import load_dotenv
from aiofile import AIOFile

class CommandRouter:
    """routes messages to commands"""
    def __init__(self, command_json_file):
        #self.COMMAND_FILE = command_json_file
        self.SETTINGS_FILE = "commands/settings.json"
        with open(self.SETTINGS_FILE) as settingsfp:
            self.settings = json.load(settingsfp)
        self.settings = defaultdict(lambda: self.settings["default"], self.settings)

        self.comlist = {}
        self.emoji_comlist = {}
        self.client = None

        for com in InvocationCommand.__subclasses__():
            com = com(self)
            self._add_command(com)

    def set_client(self, client):
        """sets the client as provided by discord.py"""
        self.client = client

    def get_guild_from_id(self, guild_id):
        """uses the client to retrieve a guild object by id.
           This is necessary for some emoji commands as they don't receive a ctx object"""
        return self.client.get_guild(guild_id)

    def _add_command(self, command):
        """adds a command to the list of possible commands"""
        if command.commandtype == "invocation":
            self.comlist[command.__name__] = command

    def add_emoji_listener(self, messageid, command):
        """adds emoji to be routed for a given message"""
        self.emoji_comlist[messageid] = command

    def remove_emoji_listener(self, messageid):
        """removes emojis to be routed for a given message"""
        del self.emoji_comlist[messageid]
        if str(messageid) + "_message" in self.emoji_comlist:
            del self.emoji_comlist[str(messageid) + "_message"]

    async def _iscommand(self, command):
        #command must be defined in commands.json
        return command in self.comlist

    def _startswithprefix(self, ctx, command):
        return command.startswith(self.settings[ctx.guild.id]["prefix"])

    async def route_messsage(self, ctx):
        """given a discord message interprets it
            and routes it to the associated command"""
        if ctx.author.bot:
            return

        command = ctx.content
        if not self._startswithprefix(ctx, command):
            return
        command = shlex.split(command)
        #remove prefix
        command[0] = command[0][len(self.settings[ctx.guild.id]["prefix"]):]

        if not await self._iscommand(command[0]):
            await ctx.channel.send("{} is not a command".format(command[0]))
            return

        await self.comlist[command[0]].run(ctx, command[1:])

    async def route_emoji(self, payload):
        """given an added/removed reaction routes it"""
        if not payload.message_id in self.emoji_comlist:
            return

        # remember the message after an emoji has been pressed once, 
        # so we don't fetch it mutltiple times
        message = self.emoji_comlist.get(str(payload.message_id) + "_message")
        if not message:
            channel = await self.client.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            self.emoji_comlist[str(payload.message_id) + "_message"] = message

        await self.emoji_comlist[payload.message_id].run(message, payload)

    async def save_command_params(self):
        """saves command parameters to file if they've been updated"""
        async with AIOFile(self.COMMAND_FILE, "w+") as afp:
            await afp.write(json.dumps(self.settings, indent=2))

load_dotenv()
COMMAND_FILE = os.getenv('COMMAND_FILE')
cr = CommandRouter(COMMAND_FILE)

print(cr.comlist.keys())

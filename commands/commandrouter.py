
"""This file implements a commmandrouter for a discord bot"""
import json
import shlex
import re
import discord
from collections import defaultdict

from commands.command import InvocationCommand
from commands.instances import *

from aiofile import AIOFile

class CommandRouter:
    """routes messages to commands"""
    def __init__(self, client):
        self.SETTINGS_FILE = "commands/settings.json"
        with open(self.SETTINGS_FILE) as settingsfp:
            self.settings = json.load(settingsfp)
        self.settings = defaultdict(lambda: self.settings["default"], self.settings)

        self.comlist = {}
        self.emoji_comlist = {}
        self.channel_comlist = {}
        self.dm_handler = None
        self.client = client

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

    def add_channel_listener(self, channel_id, command):
        self.channel_comlist[channel_id] = command

    def remove_emoji_listener(self, messageid):
        """removes emojis to be routed for a given message"""
        del self.emoji_comlist[messageid]
        if str(messageid) + "_message" in self.emoji_comlist:
            del self.emoji_comlist[str(messageid) + "_message"]

    def set_dm_handler(self, command):
        self.dm_handler = command

    def _iscommand(self, command):
        #command must be defined in commands.json
        return command in self.comlist

    def _startswithprefix(self, ctx, command):
        pattern = re.compile("[A-Za-z]")
        prefix = self.settings[str(ctx.guild.id)]["prefix"]
        return (command.startswith(prefix)
            and len(command[len(prefix):]) > 3
            and re.search(pattern, command))

    async def route_messsage(self, ctx):
        """given a discord message interprets it
            and routes it to the associated command"""
        if ctx.author.bot:
            return
        
        
        if isinstance(ctx.channel, discord.channel.DMChannel) and ctx.author != self.client.user and self.dm_handler is not None:
            await self.dm_handler.run(ctx)
            return

        command = ctx.content
        if self._startswithprefix(ctx, command):
            command = shlex.split(command)
            #remove prefix
            command[0] = command[0][len(self.settings[ctx.guild.id]["prefix"]):]

            if not self._iscommand(command[0]):
                await ctx.channel.send("{} is not a command".format(command[0]))
                return

            await self.comlist[command[0]].run(ctx, command[1:])
            return

        if ctx.channel.id in self.channel_comlist:
            await self.channel_comlist[ctx.channel.id].run(ctx)

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
        async with AIOFile(self.SETTINGS_FILE, "w+") as afp:
            await afp.write(json.dumps(self.settings, indent=2))
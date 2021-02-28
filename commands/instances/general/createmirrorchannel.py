"""general command to set settings for the bot"""
from commands.command import InvocationCommand
from commands.command import MessageListener
from utils.async_utils import json_save

import discord
import json


MIRROR_CHANNELS_FILE = 'database/mirror.json'

with open(MIRROR_CHANNELS_FILE) as data:
    mirror_channels = json.load(data)

class CreateMirrorChannel(InvocationCommand):
    """sets the prefix to anything you want"""
    def __init__(self, cr):
        super().__init__(cr, self.create_mirror_channel, "createmirrorchannel")
        self.resume()

    async def create_mirror_channel(self, ctx, channel_from: discord.TextChannel, channel_to: discord.TextChannel):
        """creates a mirrored channel"""
        onResponse(self.router, channel_from.id, channel_to.id)
        mirror_channels[channel_from.id] = channel_to.id
        await json_save(MIRROR_CHANNELS_FILE, mirror_channels)  

    def resume(self):
        """resumes polls when the bot has been down for a while"""
        for channel_from, channel_to in mirror_channels.items():
            onResponse(self.router, int(channel_from), int(channel_to))

class onResponse(MessageListener):
    def __init__(self, cr, channel_id: int, mirror_channel: int):
        super().__init__(cr, channel_id=channel_id, function=self.on_response)
        self.mirror_channel = mirror_channel

    async def on_response(self, ctx):
        """"copies the send message to a channel for admins to review"""
        if isinstance(self.mirror_channel, int):
            self.mirror_channel = ctx.guild.get_channel(self.mirror_channel)

        await self.send_msg(ctx.channel, content="Thank you for your feedback!".format(), delete_after=10)

        #copy images/files
        attachments = ctx.attachments
        files = []
        for a in attachments:
            files += [await a.to_file()]
        if not files:
            files = None

        #deletes the message
        await ctx.delete()

        await self.mirror_channel.send(content=ctx.content, files=files)
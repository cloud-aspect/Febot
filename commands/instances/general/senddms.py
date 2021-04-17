from commands.command import DMHandler, InvocationCommand
from utils.async_utils import json_save
import discord
import json

DM_CHANNEL_FILE = 'database/dm.json'

with open(DM_CHANNEL_FILE) as data:
    dm_channel = json.load(data)

class CreatedmChannel(InvocationCommand):
    """sets the prefix to anything you want"""
    def __init__(self, cr):
        super().__init__(cr, self.create_dm_channel, "createdmchannel")
        self.resume()

    async def create_dm_channel(self, ctx, channel_to: discord.TextChannel):
        """creates a dmed channel"""
        onMessage(self.router, ctx.guild.id, channel_to.id)
        dm_channel_id = channel_to.id
        await json_save(DM_CHANNEL_FILE, {ctx.guild.id: dm_channel_id})
        
        self.send_msg(ctx.channel, content="succes!")

    def resume(self):
        """resumes polls when the bot has been down for a while"""
        for guild_id, channel_to in dm_channel.items():
            onMessage(self.router, int(guild_id), int(channel_to))

class onMessage(DMHandler):
    def __init__(self, cr, guild_id:int, mirror_channel_id: int):
        super().__init__(cr, function=self.on_response)
        self.mirror_channel_id = mirror_channel_id
        self.guild_id = guild_id
        self.guild = None
        self.mirror_channel = None

    async def on_response(self, ctx):
        """"copies the send message to a channel for admins to review"""
        if self.guild is None:
            self.guild = self.router.client.get_guild(self.guild_id)
            if(self.guild is None):
                self.guild = await self.router.client.fetch_guild(self.guild_id)
                
        if self.mirror_channel is None:
            self.mirror_channel = self.guild.get_channel(self.mirror_channel_id)
            if(self.mirror_channel is None):
                self.mirror_channel = await self.guild.fetch_channel(self.mirror_channel_id)

        await self.send_msg(ctx.channel, content="Thank you for your feedback!".format())

        #copy images/files
        attachments = ctx.attachments
        files = []
        for a in attachments:
            files += [await a.to_file()]
        if not files:
            files = None

        await self.mirror_channel.send(content=ctx.content, files=files)
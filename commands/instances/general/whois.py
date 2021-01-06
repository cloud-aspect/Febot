"""implements a whois command for discord"""
from datetime import datetime

from commands.command import InvocationCommand

import discord

from utils.datetime_utils import td_format


class WhoIs(InvocationCommand):
    """creates a message detailing a user"""
    def __init__(self, cr):
        super().__init__(cr, self.whois, "whois")

    async def whois(self, ctx, member: discord.Member):
        """creates a nice embed with detail about a user"""

        embed = discord.Embed(title="{}#{} ({})".format(member.name, member.discriminator,
                                                        member.display_name), color=member.colour)
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Avatar", value="[link]({})".format(member.avatar_url), inline=True)
        embed.add_field(name="Account Created", value=member.created_at.date(), inline=True)
        embed.add_field(name="Account Age",
                        value=td_format(datetime.utcnow() - member.created_at),
                        inline=True)
        embed.add_field(name="Joined Server At", value=member.joined_at.date(), inline=True)
        embed.add_field(name="Join Server Age",
                        value=td_format(datetime.utcnow() - member.joined_at),
                        inline=True)
        embed.add_field(name="Status", value=member.status, inline=True)
        await self.send_msg(ctx.channel, embed=embed)

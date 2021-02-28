"""implements a whois command for discord"""
from datetime import datetime
import json

from commands.command import InvocationCommand

import discord

from utils.datetime_utils import td_format
from utils.constants import alias_to_rank, OSRS_RANKS

def _getmemberentry(userJson: {}, guild_id: str, member_id: str):
    guild_id = str(guild_id)
    member_id = str(member_id)
    guild = userJson.get(guild_id)
    if guild is None:
        userJson[guild_id] = {}
        guild = userJson[guild_id]
    entry = guild.get(member_id)
    if entry is None:
        entry = {
            "current_rank":OSRS_RANKS[0],
            "rank_time":{
            }
        }
        guild[member_id] = entry
    return entry

class WhoIs(InvocationCommand):
    USER_DB_FILE = "database/users.json"

    """creates a message detailing a user"""
    def __init__(self, cr):
        super().__init__(cr, self.whois, "whois")

    async def whois(self, ctx, member: discord.Member):
        """creates a nice embed with details about a user"""
        
        embed = discord.Embed(title="{}#{} ({})".format(member.name, member.discriminator,
                                                        member.display_name), color=member.colour)
        
        rank = None
        with open(self.USER_DB_FILE) as userfp:
            users = json.load(userfp)
            entry = _getmemberentry(users, ctx.guild.id, member.id)
            rank = entry['current_rank']

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
        if rank:
            embed.add_field(name="Rank", value=rank, inline=True)
            embed.add_field(name="​", value="​", inline=True) #zero width space as name and value
        await self.send_msg(ctx.channel, embed=embed)

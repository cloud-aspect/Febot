"""implements checks for ranking users"""

import json

from datetime import datetime, timedelta, timezone
from collections import defaultdict

import discord

from commands.command import InvocationCommand, EmojiCommand, MessageListener
from utils.constants import alias_to_rank, OSRS_RANKS
from utils.async_utils import json_save, Timer

RANK_REQ_FILE = "database/rank_requirements.json"
USER_DB_FILE = "database/users.json"

with open(RANK_REQ_FILE) as rankfp:
    rank_req = json.load(rankfp)
rank_req = defaultdict(lambda: rank_req["default"], rank_req)

with open(USER_DB_FILE) as userfp:
    users = json.load(userfp)



def _getmemberentry(guild_id: str, member_id: str):
    guild_id = str(guild_id)
    member_id = str(member_id)
    guild = users.get(guild_id)
    if guild is None:
        users[guild_id] = {}
        guild = users[guild_id]
    entry = guild.get(member_id)
    if entry is None:
        entry = {
            "current_rank":OSRS_RANKS[0],
            "rank_time":{
            }
        }
        guild[member_id] = entry
    return entry

def _setrank(guild_id, member_id, rank):
    timestamp = datetime.timestamp(datetime.now(timezone.utc))
    entry = _getmemberentry(guild_id, member_id)
    entry["current_rank"] = rank
    entry["rank_time"][rank] = timestamp
    # users[guild_id][member_id] = entry

def _time_till_rank(guild_id, member):
    """returns time till rankup in seconds"""
    member_info = _getmemberentry(guild_id, member.id)
    rank = member_info["current_rank"]

    #if unranked can get a rank now
    if rank == OSRS_RANKS[0]:
        return 0

    time_req = rank_req[str(guild_id)][OSRS_RANKS[OSRS_RANKS.index(rank)+1]]["time"]
    # sorts all the ranks by the time they where assinged then gets the earliest timestamp as the
    # joining time of the cc
    # ranks_sorted_by_date = sorted(member_info["rank_time"].items(), key=lambda item: item[1])
    join_time = member.joined_at.replace(tzinfo=None)
    last_rank_time = datetime.fromtimestamp(member_info["rank_time"][rank], timezone.utc)

    #refuse rankup because not enough time in cc
    if join_time + timedelta(days=7*time_req) > datetime.now(timezone.utc).replace(tzinfo=None):
        rankuptime = join_time + timedelta(days=7*time_req) - datetime.now(timezone.utc).replace(tzinfo=None)
        return rankuptime.total_seconds()

    #refuse rankup because to short since last rankup
    if last_rank_time + timedelta(days=31) > datetime.now(timezone.utc):
        rankuptime = last_rank_time + timedelta(days=32) - datetime.now(timezone.utc)
        return rankuptime.total_seconds()

    #theres enough time
    return 0

class SetRank(InvocationCommand):
    """sets the rank of a user"""
    def __init__(self, cr):
        super().__init__(cr, self.set_rank, "setrank")


    async def set_rank(self, ctx, member: discord.member.Member, rank: str):
        if rank not in alias_to_rank.keys():
            self.send_error_msg(self, ctx.channel, "I don't know that rank")
            return
        rank = alias_to_rank[rank]
        _setrank(ctx.guild.id, member.id, rank)
        await json_save(USER_DB_FILE, users)


TIME_REMAINING_EMOJI = "\U0001f552"
RANK_REQ_EMOJI = "rankup"
RECRUIT_REQ_EMOJI = "Recruit"

class SetRankupChannel(InvocationCommand):
    """"sets a channel to rank up users in"""

    def __init__(self, cr):
        super().__init__(cr, self.set_rankup_channel, "setrankupchannel")
        self.resume()

    async def set_rankup_channel(self, ctx, channel: discord.TextChannel, message_id: int, pending_ranks_channel: discord.TextChannel, rank_updates_channel: discord.TextChannel, ranking_role: discord.Role):
        """designates a message in a channel as the 'rank-up-channel'"""

        message = await channel.fetch_message(message_id)
        if message is None:
            await self.send_error_msg(ctx.channel, "can't find that message")
        await message.add_reaction(TIME_REMAINING_EMOJI)
        await message.add_reaction(discord.utils.get(ctx.guild.emojis, name=RANK_REQ_EMOJI))
        await message.add_reaction(discord.utils.get(ctx.guild.emojis, name=RECRUIT_REQ_EMOJI))
        onRankupRequest(self.router, message_id)
        onResponse(self.router, channel.id, pending_ranks_channel)

        if not ctx.guild.id in users:
            users[str(ctx.guild.id)] = {}
        users[str(ctx.guild.id)]["settings"] = {
            "rankupchannel": channel.id,
            "rankup_message_id": message_id,
            "pending_ranks_channel": pending_ranks_channel.id,
            "rank_updates_channel":rank_updates_channel.id,
            "ranking_role": ranking_role.id
        }

        users[str(ctx.guild.id)]["pending_rankup"] = {}
        await json_save(USER_DB_FILE, users)

    def resume(self):
        for guild in users.values():
            settings = guild["settings"]
            onResponse(self.router, settings["rankupchannel"], settings["pending_ranks_channel"])
            onRankupRequest(self.router, int(settings["rankup_message_id"]))
            pending_rankups = guild["pending_rankup"]
            for rankup in pending_rankups.values():
                if "message" in rankup:
                    onRankgranted(self.router, int(rankup["message"]))
                else:
                    del rankup

class onRankupRequest(EmojiCommand):

    def __init__(self, cr, message_id):
        super().__init__(cr, message_id=message_id, function=self.on_rankup_request)

    async def on_rankup_request(self, message, payload):
        emoji_poster = message.channel.guild.get_member(payload.user_id)

        if payload.emoji.is_unicode_emoji():
            emoji = payload.emoji.name
        else:
            emoji = "<:{}:{}>".format(payload.emoji.name, payload.emoji.id)
        
        
        print(emoji)
        await message.remove_reaction(emoji, emoji_poster)
        emoji = payload.emoji.name

        for role in emoji_poster.roles:
            if role.id == int(users[str(message.guild.id)]["settings"]["ranking_role"]):
                return

        member_entry = _getmemberentry(message.channel.guild.id, emoji_poster.id)
        current_rank = member_entry["current_rank"]
        if OSRS_RANKS.index(current_rank) == len(OSRS_RANKS) - 1:
            reply = "{} you're already the highest rank"
            reply = reply.format(emoji_poster.mention)
            await self.send_msg(message.channel, reply, delete_after=20)
            return

        next_rank = OSRS_RANKS[OSRS_RANKS.index(current_rank)+1]

        if emoji == TIME_REMAINING_EMOJI:
            if rank_req[str(message.guild.id)][next_rank]["handpicked"] == 1:
                reply = "{} you can't get the next rank, it's handpicked by staff"
                reply = reply.format(emoji_poster.mention)
                await self.send_msg(message.channel, reply, delete_after=20)
                return

            time = _time_till_rank(message.channel.guild.id, emoji_poster)
            if time > 0:
                time = int(time/(60*60*24))+1
                reply = "{} you need another {} day{} until you're eligable for a rank-up"
                reply = reply.format(emoji_poster.mention, time, "s" if time > 1 else "")
            else:
                reply = "{} you've been in the cc long enough for your next rank!"
                reply = reply.format(emoji_poster.mention)
            await self.send_msg(message.channel,
                                reply,
                                delete_after=20)
            return


        if emoji == RECRUIT_REQ_EMOJI:
            if OSRS_RANKS.index(current_rank) >= OSRS_RANKS.index("recruit"):
                 await self.send_msg(message.channel, 
                                "{}, your rank is already recruit or higher than recruit".format(emoji_poster.mention),
                                delete_after=60)
            await self.send_msg(message.channel, 
                                "{} please send 1 image in this channel showing that you have the gear required for raiding, along with your exact rsn".format(emoji_poster.mention),
                                delete_after=60)
            await message.channel.set_permissions(emoji_poster, send_messages=True)
            users[str(message.guild.id)]["pending_rankup"][str(emoji_poster.id)] = {
                "next_rank":"recruit"
            }
            Timer(120, message.channel.set_permissions, emoji_poster, overwrite=None)

        if emoji == RANK_REQ_EMOJI:
            next_rank_req = rank_req[str(message.guild.id)][next_rank]
            time_till_rankup = _time_till_rank(message.channel.guild.id, emoji_poster)
            # you can always get a smiley
            if member_entry["current_rank"] == OSRS_RANKS[0]:
                await self.send_msg(message.channel, 
                                    "{} please send 1 message in this channel with your exact rsn".format(emoji_poster.mention),
                                    delete_after=60)
            # you can't get a handpicked rank
            elif next_rank_req["handpicked"] == "1":
                await self.send_msg(message.channel, 
                                    "{} {} is currently handpicked by staff".format(emoji_poster.mention, OSRS_RANKS[OSRS_RANKS.index(current_rank)+1]),
                                    delete_after=60)
                return
            # you need the time until the next rank
            elif time_till_rankup > 0:
                time = int(time_till_rankup/(60*60*24))+1
                await self.send_msg(message.channel, 
                                    "{} you need to wait another {} day{} for a rank-up!".format(emoji_poster.mention, time, "s" if time > 1 else ""),
                                    delete_after=20)
                return
            # you may need gear for a rankup
            elif next_rank_req["gear"] == 1:
                if OSRS_RANKS[OSRS_RANKS.index(current_rank)+1] != "lieutenant":
                    await self.send_msg(message.channel, 
                                        "{} please send 1 image in this channel showing that you have the gear required for {} along with your exact rsn".format(emoji_poster.mention, next_rank),
                                        delete_after=60)
                else:
                    await self.send_msg(message.channel, 
                                        "{} please send 1 message in this channel with your exact rsn and an image of the gear (if needed)".format(emoji_poster.mention),
                                        delete_after=60)
            else:
                await self.send_msg(message.channel, 
                                    "{} please send 1 message in this channel with your exact rsn".format(emoji_poster.mention),
                                    delete_after=60)

            users[str(message.guild.id)]["pending_rankup"][str(emoji_poster.id)] = {
                "next_rank":next_rank
            }
            await message.channel.set_permissions(emoji_poster, send_messages=True)
            Timer(120, message.channel.set_permissions, emoji_poster, overwrite=None)
            await json_save(USER_DB_FILE, users)

RANK_GRANTED_EMOJI = "\u2705"
RANK_DENIED_EMOJI = "\u274c"

class onResponse(MessageListener):
    def __init__(self, cr, channel_id: int, mirror_channel: int):
        super().__init__(cr, channel_id=channel_id, function=self.on_response)
        self.mirror_channel = mirror_channel

    async def on_response(self, ctx):
        """"copies the send message to a channel for admins to review"""
        if isinstance(self.mirror_channel, int):
            self.mirror_channel = ctx.guild.get_channel(self.mirror_channel)

        if str(ctx.author.id) not in users[str(ctx.channel.guild.id)]["pending_rankup"]:
            return

        await self.send_msg(ctx.channel, content="{} gold stars will now look at your rankup!".format(ctx.author.mention), delete_after=30)


        current_rank = _getmemberentry(ctx.channel.guild.id, ctx.author.id)["current_rank"]

        #copy images
        attachments = ctx.attachments
        files = []
        for a in attachments:
            files += [await a.to_file()]
        if not files:
            files = None

        #deletes the message
        await ctx.delete()

        #set channel permissions back to normal
        await ctx.channel.set_permissions(ctx.author, overwrite=None)
        
        #send the ranking up message and sets up the emoji commands
        message = "{} wants to rank up to {} their rsn 'should' be: {}".format(ctx.author.mention,
                                                                               OSRS_RANKS[OSRS_RANKS.index(current_rank)+1],
                                                                               ctx.content)
        send_message = await self.mirror_channel.send(content=message, files=files)
        users[str(ctx.channel.guild.id)]["pending_rankup"][str(ctx.author.id)]["message"] = send_message.id
        await send_message.add_reaction(RANK_GRANTED_EMOJI)
        await send_message.add_reaction(RANK_DENIED_EMOJI)
        onRankgranted(self.router, send_message.id)

        #save db states
        await json_save(USER_DB_FILE, users)

class onRankgranted(EmojiCommand):
    """"Handles what happens when the rank is granted/denied"""
    def __init__(self, cr, message_id):
        super().__init__(cr, message_id=message_id, function=self.on_rank_granted)

    async def on_rank_granted(self, message, payload):
        """Saves whatever the changes are to ranks in the database"""
        emoji_poster = message.channel.guild.get_member(payload.user_id)
        allowed = False
        for role in emoji_poster.roles:
            if role.id == int(users[str(message.guild.id)]["settings"]["ranking_role"]):
                allowed = True
        if not allowed:
            return

        if payload.emoji.is_unicode_emoji():
            emoji = payload.emoji.name
        else:
            emoji = "<:{}:{}>".format(payload.emoji.name, payload.emoji.id)

        ranking_member = message.mentions[0]

        channel = message.guild.get_channel(users[str(message.guild.id)]["settings"]["rank_updates_channel"])
        pending_entry = users[str(message.guild.id)]["pending_rankup"][str(ranking_member.id)]
        if emoji == RANK_DENIED_EMOJI:
            await self.send_msg(channel, "{}, rank up to {} denied. You either don't have the total level or didn't show all the required gear.\nPlease send another request when ready".format(ranking_member.mention, pending_entry["next_rank"]))

        if emoji == RANK_GRANTED_EMOJI:
            await self.send_msg(channel, "{} - {}".format(ranking_member.mention, pending_entry["next_rank"]))
            _setrank(message.guild.id, ranking_member.id, pending_entry["next_rank"])

        await message.delete()
        if str(ranking_member.id) in users[str(message.guild.id)]["pending_rankup"]:
            del users[str(message.guild.id)]["pending_rankup"][str(ranking_member.id)]
        await json_save(USER_DB_FILE, users)
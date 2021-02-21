"""implements a polling function using emojis in dicord"""
import json
from datetime import datetime, timedelta, timezone

from commands.command import InvocationCommand, EmojiCommand

import discord
from utils.discord_utils import is_emoji, id_or_mention_to_id
from utils.async_utils import Timer, json_save

RUNNING_POLLS_FILE = 'database/polls.json'
timers = {}

with open(RUNNING_POLLS_FILE) as data:
    running_polls = json.load(data)

class CreatePoll(InvocationCommand):
    """implements a polling command"""
    def __init__(self, cr):
        super().__init__(cr, self.create_poll, "createpoll")
        self.resume()

    async def create_poll(self, ctx, runtime: int, title: str, *args: str,
                          channel: discord.TextChannel = None, message: str = None,
                          message_id: int = None):
        """sanitizes input for _create_poll"""

        #only specify either message or message id
        if message and message_id:
            await self.send_error_msg(ctx.channel,
                                      "you specified both messsage and message_id, only specify 1")
            return

        #don't @anyone in poll titles or message
        # title = discord.utils.escape_mentions(title)
        # if message:
        #     message = discord.utils.escape_mentions(message)

        if len(args[0::2]) != len(args[1::2]):
            await self.send_error_msg(ctx.channel,
                                      "Not every emoji has a message")
            return
        #check if emojis and options are properly alternating
        emojis = ctx.guild.emojis
        emoji_options = []
        options = []
        for emoji, option in zip(args[0::2], args[1::2]):
            if not is_emoji(emoji):
                await self.send_error_msg(ctx.channel, 
                                          "I can't use '{}' as an emoji maybe you need to use \" marks around an option?".format(emoji))
                return
            emoji_options += [emoji]
            options += [option]

        if len(emoji_options) < 2:
            await self.send_error_msg(ctx.channel,
                                      "The poll needs more options than {}".format(len(emojis)))
            return

      

        if channel is None:
            channel = ctx.channel

        await self._create_poll(ctx, runtime, title, emoji_options, options, channel=channel,
                                message=message, message_id=message_id)

    async def _create_poll(self, ctx, runtime, title, emojis, options, channel=None, message=None,
                           message_id=None):
        """creates a poll message"""
        #create message if it wasn't given
        if not message_id:
            poll_options = {}

            if not message:
                message = "{} started a poll! It will last for {} days.\nVote by clicking on the emojis below! I will remember the last option you pressed. The options are as follows:\n"
                message = message.format(ctx.author.mention, runtime)

            embed = discord.Embed(title=title, description=message)
            for emoji, option in zip(emojis, options):
                poll_options[emoji] = option
                embed.add_field(value="```{}```".format(option), name=emoji)

            # description = "{}\n```{}```".format(message, description)
            message = await self.send_msg(channel, embed=embed)
        else:
            #if the message is given fetch it
            try:
                message = channel.fetch_message(message_id)
            except discord.NotFound:
                self.send_error_msg(ctx.channel, "Couldn't find that message!")
                return
            except discord.Forbidden:
                self.send_error_msg(ctx.channel, "I'm missing permissions")
                return
            except discord.HTTPException:
                self.send_error_msg(ctx.channel, "Something went wrong")
                return

        #add emojis to the message/remember what options correspond to the emojis
        for emoji, option in zip(emojis, options):
            poll_options[emoji] = option
            await message.add_reaction(emoji)

        votes = dict().fromkeys(poll_options.keys(), 0)
        poll = {
            "options":poll_options,
            "channel_id":channel.id,
            "votes":votes,
            "uservotes":{},
            "end_time":datetime.timestamp(datetime.now(timezone.utc) + timedelta(days=runtime)),
            "guild_id":channel.guild.id,
            "title":title
        }

        #add poll to the list of running polls
        running_polls[str(message.id)] = poll
        OnPollReaction(self.router, message.id)
        time = timedelta(days=runtime).total_seconds()
        #EndPoll
        timers[str(message.id)] = Timer(time, _end_poll, self.router, message.id)
        await json_save(RUNNING_POLLS_FILE, running_polls)

    def resume(self):
        """resumes polls when the bot has been down for a while"""
        for pollmessage_id, poll in running_polls.items():
            OnPollReaction(self.router, int(pollmessage_id))
            end_date = datetime.fromtimestamp(poll["end_time"], tz=timezone.utc)
            #end poll if it has ended during downtime
            if end_date < datetime.now(timezone.utc):
                # just ends it 60 seconds from now because the discord bot needs to finish
                # initializing very unsafe but should always work
                timers[pollmessage_id] = Timer(60, _end_poll, self.router, pollmessage_id)
            #start a thread to end the poll if it's somewhere in the future
            else:
                time = (end_date - datetime.now(timezone.utc)).total_seconds()
                timers[pollmessage_id] = Timer(time, _end_poll, self.router, pollmessage_id)


def _get_poll_results_as_string(message_id):
    poll = running_polls[str(message_id)]
    results = ""
    sorted_vote_list = sorted(poll["votes"].items(), key=lambda item: item[1], reverse=True)

    winner = sorted_vote_list[0]
    if sorted_vote_list[0][1] == sorted_vote_list[1][1]:
        #tie
        results += "It's a tie between: {} {}".format(sorted_vote_list[0][0],
                                                      poll["options"][sorted_vote_list[0][0]])
        tiesize = sum([sorted_vote_list[0][1] == vote for option, vote in sorted_vote_list])
        for emoji, votes in sorted_vote_list[1:tiesize]:
            results += " and {} {}".format(emoji, poll["options"][emoji])
        results += " they have {} votes each.\n".format(sorted_vote_list[0][1])
        remaining_options = tiesize
    else:
        #not a tie
        results += "The winner is {} {}, with {} votes!\n".format(winner[0],
                                                                  poll["options"][winner[0]],
                                                                  winner[1])
        remaining_options = 1

    for emoji, votes in sorted_vote_list[remaining_options:]:
        results += "{} {}\t{} votes\n".format(emoji, poll["options"][emoji], votes)

    return results

async def _end_poll(router, message_id):
    if str(message_id) not in running_polls:
        return
    router.remove_emoji_listener(int(message_id))
    message_id = str(message_id)

    poll = running_polls[message_id]
    guild = router.client.get_guild(int(poll["guild_id"]))
    channel = guild.get_channel(poll["channel_id"])

    content = "The poll has ended the results are as follows:"
    description = _get_poll_results_as_string(message_id)

    await channel.send(embed=discord.Embed(title=poll["title"], content=content,
                                           description=description))
    del running_polls[message_id]
    await json_save(RUNNING_POLLS_FILE, running_polls)

class EndPoll(InvocationCommand):
    """command to end a poll"""
    def __init__(self, cr):
        super().__init__(cr, function=self.end_poll, invocation="endpoll")

    async def end_poll(self, _, message_id):
        """manually end a poll before the specified time"""
        if message_id in timers:
            timers[message_id].cancel()
            del timers[message_id]
        await _end_poll(self.router, message_id)

class OnPollReaction(EmojiCommand):
    """"command to add a vote to a poll"""
    def __init__(self, cr, message_id):
        super().__init__(cr, message_id=message_id, function=self.on_vote)

    async def on_vote(self, message, payload):
        """adds a vote to the poll based on the emoji pressed"""
        poll = running_polls[str(payload.message_id)]
        emoji_poster = message.channel.guild.get_member(payload.user_id)

        if payload.emoji.is_unicode_emoji():
            emoji = payload.emoji.name
        else:
            emoji = "<:{}:{}>".format(payload.emoji.name, payload.emoji.id)

        await message.remove_reaction(emoji, emoji_poster)

        if emoji not in poll["options"]:
            return

        for poll_emoji in [str(x) for x in poll["options"]]:
            if poll_emoji not in [str(x) for x in message.reactions]:
                await message.add_reaction(poll_emoji)


        if payload.user_id in poll["uservotes"]:
            #remove previous vote
            poll["votes"][poll["uservotes"][payload.user_id]] -= 1

        poll["uservotes"][payload.user_id] = emoji
        poll["votes"][emoji] += 1
        await json_save(RUNNING_POLLS_FILE, running_polls)

class ShowPollResults(InvocationCommand):
    """command to show current votes in a poll"""
    def __init__(self, cr):
        super().__init__(cr, self.show_poll_results, invocation="showpollresults")

    async def show_poll_results(self, ctx, message_id: int):
        """shows the preliminary results of a poll"""
        message_id = id_or_mention_to_id(message_id)
        if not message_id:
            self.send_error_msg(ctx.channel, "That's not a valid poll id")

        if str(message_id) not in running_polls:
            return

        poll = running_polls[str(message_id)]
        results = _get_poll_results_as_string(str(message_id))

        content = "preliminary results are as follows:"
        await self.send_msg(ctx.channel, embed=discord.Embed(title=poll["title"], content=content,
                                                             description=results))

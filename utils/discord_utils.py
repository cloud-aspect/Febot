"""utility function for discord emojis"""
import re

import emoji

import discord

def is_emoji(txt):
    """checks if given string is an emoji"""
    if txt in emoji.UNICODE_EMOJI:
        return True

    custom_emoji_pattern = re.compile(r"<:[^:\s]{2,32}:[0-9]{18}>")
    return re.match(custom_emoji_pattern, txt)

def contains_emoji(txt):
    """checks if a string contains an emoji"""
    has_emoji = bool(emoji.get_emoji_regexp().search(txt))

    custom_emoji_pattern = re.compile(r"<:[^:\s]{2,32}:[0-9]{18}>")
    has_custom_emoji = re.search(custom_emoji_pattern, txt)

    return has_emoji or has_custom_emoji

def partial_emoji_to_string(partial_emoji):
    """converts a partial emoji object to a string usable in discord messages"""
    if partial_emoji.is_unicode_emoji():
        return partial_emoji.name
    return "<:{}:{}>".format(partial_emoji.name, partial_emoji.id)


def id_or_mention_to_id(text):
    """"converts a discord mention or direct id to an int usable by discord.py"""
    # @mention format <@!123456789123456789>
    # @role format <@&539862637241171969>
    # #channel format <#643557823912869889>
    text = str(text)
    hastag_mention_len = 21
    at_mention_len = 22

    user_id = "id"
    if hastag_mention_len == len(text) or at_mention_len == len(text):
        user_id = text[-19:-1]
    #user id send directly
    elif len(text) == 18:
        user_id = text

    try:
        user_id = int(user_id)
    except ValueError:
        return None
    return user_id

def to_int(_, text):
    return int(text) 

def to_bool(_, text):
    return text != "0" and text.lower() != "false"

def to_role(guild, text):
    role_id = id_or_mention_to_id(text)
    role = guild.get_role(role_id)
    if role:
        return role
    raise ValueError("can't find that role")

def to_channel(guild, text):
    channel_id = id_or_mention_to_id(text)
    channel = guild.get_channel(channel_id)
    if channel:
        return channel
    raise ValueError("can't find that channel")

def to_member(guild, text):
    user_id = id_or_mention_to_id(text)
    member = guild.get_member(user_id)
    if member:
        return member
    raise ValueError("can't find that member")

def to_str(_, text):
    return text

def cast_from_string(guild, text, to_type):
    caster = {
        int:to_int,
        discord.TextChannel:to_channel,
        discord.Member:to_member,
        discord.member.Member:to_member,
        discord.Role:to_role,
        to_bool:to_bool,
        str:to_str
    }
    return caster[to_type](guild, text)

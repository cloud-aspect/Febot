"""Help command class implementation"""
import json

from commands.command import InvocationCommand
from collections import OrderedDict

import discord

class HelpCommand(InvocationCommand):
    """Help command class implementation"""

    COMMAND_DESCRIPTION_FILE = "commands/commanddescriptions.json"

    def __init__(self, cr):
        super().__init__(cr, self.help, "help")
        with open(self.COMMAND_DESCRIPTION_FILE) as commandfp:
            self.description = json.load(commandfp, object_pairs_hook=OrderedDict)

    async def help(self, ctx, commandname:str=None):
        """Command to explain the use of diffent commands"""
        title = None
        description = None

        if commandname is not None and commandname not in self.router.comlist:
            msg = "That command does not exist try to use: '{}help' for a list of all commands"
            msg = msg.format(self.router.settings[ctx.guild.id]["prefix"])
            await self.send_error_msg(ctx.channel, msg)
            return

        if commandname:
            title = self.description[commandname]["usage"]
            description = self.description[commandname]["description"]
            embed = discord.Embed(title=title, description=description)
            for arg, arg_desc in self.description[commandname]["options"].items():
                embed.add_field(name=arg, value=arg_desc, inline=False)
        else:
            title = "The following commands are available:"
            embed = discord.Embed(title=title)
            for command, command_dict in self.description.items():
                embed.add_field(name=command, value=command_dict["description"], inline=False)

            footnote = "You can use '{}{}' to get more information about a specific command"
            footnote = footnote.format(self.router.settings[ctx.guild.id]["prefix"],
                                       self.description["help"]["usage"])
            embed.set_footer(text=footnote)

        await self.send_msg(ctx.channel, embed=embed)

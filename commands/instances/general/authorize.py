"""command to authorize different discord roles to use different commands"""
from commands.command import InvocationCommand
import discord

class Authorize(InvocationCommand):
    """command to authorize different discord roles to use different commands"""
    def __init__(self, cr):
        super().__init__(cr, self.authorize, "authorize")

    async def authorize(self, ctx, role: discord.Role, command_name: str, add: bool = True):
        """command to authorize different discord roles to use different commands"""
        #adds allowed roles to commands
        if command_name not in self.router.commands:
            msg = "{} is not a command"
            msg.format(command_name)
            self.send_error_msg(ctx.channel, msg)
            return

        if add:
            #if it's not already in the allowed roles add it
            if role.id not in self.router.commands[ctx.guild.id][command_name]["role_req"]:
                self.router.commands[command_name].perms["role_req"].extend([role.id])
                await self.router.commands[command_name].save_permissions
            msg = "added {} to the allowed roles for {}".format(role.name, command_name)
        else:
            #if it is in the allowed roles remove it
            if role.id in self.router.commands[command_name]["role_req"]:
                self.router.commands[command_name].perms["role_req"].remove(role.id)
                await self.router.commands[command_name].save_permissions
            msg = "removed {} from the allowed roles for {}".format(role.name, command_name)

        await self.send_msg(ctx.channel, content=msg)

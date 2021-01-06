"""general command to set settings for the bot"""
from commands.command import InvocationCommand

class SetPrefix(InvocationCommand):
    """sets the prefix to anything you want"""
    def __init__(self, cr):
        super().__init__(cr, self.set_prefix, "setprefix")

    async def set_prefix(self, ctx, prefix: str):
        """sets a custom prefix for a guild"""
        if not 1 <= len(prefix) <= 3:
            await self.send_error_msg(ctx.channel, "{} is not a valid prefix".format(prefix))
            return

        self.router.settings[ctx.guild.id]["prefix"] = prefix

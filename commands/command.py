"""implements the base command"""
import json
from aiofile import AIOFile
from inspect import signature

from utils.discord_utils import cast_from_string, partial_emoji_to_string

class Command:
    """baseclass for a command"""
    PERMISSION_FILE = "commands/commandsettings.json"


    def __init__(self, router, send_error_msg=True):
        self.router = router
        self._send_errors = send_error_msg

        self.perms = ()
        self._load_permissions()
        self.commandtype = None

    async def send_error_msg(self, channel, msg, delete_after=10):
        """sends and deletes a msg to channel"""
        if self._send_errors:
            await self.send_msg(channel, msg, delete_after=delete_after)
        print(msg)

    async def send_msg(self, channel, content=None, embed=None, delete_after=None):
        """"wrapper for send message command"""
        await channel.send(content, embed=embed, delete_after=delete_after)

    async def _save_dict(self, file, saved_dict):
        async with AIOFile(file, "w+") as afp:
            await afp.write(json.dumps(saved_dict, indent=2))

    def _load_permissions(self):
        with open(self.PERMISSION_FILE) as afp:
            self.perms = json.load(afp)

    async def save_permissions(self):
        """saves the permissions after they've been updated"""
        async with AIOFile(self.PERMISSION_FILE, "w+") as afp:
            await afp.write(json.dumps(self.perms, indent=2))

    async def run(self, ctx, trigger):
        raise NotImplementedError

class InvocationCommand(Command):
    def __init__(self, router, function=None, invocation=None, send_error_msg=True):
        super().__init__(router, send_error_msg)

        if not function or not invocation:
            raise NotImplementedError

        self.req_param = []
        self.var_param = False
        self.kw_param = {}
        self.var_kw_param = False

        self.function = function
        self.__name__ = invocation
        self._parse_parameters()

        self.commandtype = "invocation"

    def _has_auth(self, ctx):
        guildperms = self.perms.get(ctx.guild.id, self.perms["default"])
        command_perms = guildperms.get(self.__name__)

        #either be admin, do not need auth, or have auth
        return (ctx.author.guild_permissions.administrator or
                command_perms["need_auth"] == 0 or
                not set(command_perms["role_req"]).isdisjoint(ctx.author.roles))

    def _parse_parameters(self):
        params = signature(self.function).parameters
        for name, param in list(params.items())[1:]:
            if param.kind == param.POSITIONAL_ONLY or param.kind == param.POSITIONAL_OR_KEYWORD:
                self.req_param += [param]
            elif param.kind == param.VAR_POSITIONAL:
                self.var_param = param
            elif param.kind == param.KEYWORD_ONLY:
                self.kw_param[param.name] = param
            elif param.kind == param.VAR_KEYWORD:
                self.var_kw_param = param

    def _check_and_cast_args(self, ctx, args_as_list):
        kwargs = {}

        for arg in args_as_list:
            if '=' in arg:
                args_as_list.remove(arg)
                arg = arg.split("=")
                kwargs[arg[0]] = arg[1]


        #args and kwargs of the command
        req_args = args_as_list[:len(self.req_param)]
        var_args = args_as_list[len(self.req_param):]

        for ite, (arg, param) in enumerate(zip(req_args, self.req_param)):
            if param.annotation is not param.empty:
                req_args[ite] = cast_from_string(ctx.guild, arg, param.annotation)

        if self.var_param:
            for ite, arg in enumerate(var_args):
                var_args[ite] = cast_from_string(ctx.guild, arg, self.var_param.annotation)

        for param_name, value in kwargs.items():
            if (param_name in self.kw_param and
                    self.kw_param[param_name].annotation is not self.kw_param[param_name].empty):
                kwargs[param_name] = cast_from_string(ctx.guild, value,
                                                      self.kw_param[param_name].annotation)
            elif self.var_kw_param and self.var_kw_param.annotation is not self.var_kw_param.empty:
                kwargs[param_name] = cast_from_string(ctx.guild, value, self.kw_param)

        return req_args + var_args, kwargs

    async def run(self, ctx, command_args):
        if not self._has_auth(ctx):
            await self.send_error_msg(ctx.channel,
                                      "You don't have the permissions for {}".format(self.__name__))
            return

        try:
            args, kwargs = self._check_and_cast_args(ctx, command_args)
            await self.function(ctx, *args, **kwargs)
        except ValueError:
            await self.send_error_msg(ctx.channel,
                                      "The provided armuments are of a wrong type".format(self.__name__))


class EmojiCommand(Command):
    """baseclass for a Emojicommand"""
    PERMISSION_FILE = "commands/commandsettings.json"
    def __init__(self, router, message_id=None, function=None, name=None, send_error_msg=True):
        super().__init__(router, send_error_msg)
        self.router.add_emoji_listener(message_id, self)
        self.__name__ = name
        self.function = function

    def _has_auth(self, ctx):
        guildperms = self.perms.get(ctx.guild.id, self.perms["default"])
        command_perms = guildperms.get(self.__name__, guildperms["default"])

        #either be admin, do not need auth, or have auth
        return (ctx.author.guild_permissions.administrator or
                command_perms["need_auth"] == 0 or
                not set(command_perms["role_req"]).isdisjoint(ctx.author.roles))

    async def run(self, message, payload):
        await self.function(message, payload)

        
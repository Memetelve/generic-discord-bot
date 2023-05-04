from discord.app_commands.errors import CheckFailure


class InvalidAdmin(Exception):
    pass


class InvalidGuild(Exception):
    pass


class InvalidId(Exception):
    pass


class DuplicateKey(Exception):
    pass


class InvalidKey(Exception):
    pass


class UnauthorizedAccess(Exception):
    pass


class MissingPremium(CheckFailure):
    def __init__(self, message: str = "You need premium to use this command", *args):
        self.message = message
        super().__init__(message, *args)

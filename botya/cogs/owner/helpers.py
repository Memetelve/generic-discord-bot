import enum


class Cogs(enum.Enum):
    all = "all"

    test = "botya.cogs.test"
    admin = "botya.cogs.admin"
    mod = "botya.cogs.mod"
    owner = "botya.cogs.owner"
    user = "botya.cogs.user"
    clash_of_clans = "botya.cogs.clash_of_clans"


class PremiumType(enum.Enum):
    user = "user"
    server = "server"

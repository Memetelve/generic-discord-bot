from uuid import UUID
import emoji


def bot_above(me, user, guild):
    # sourcery skip: assign-if-exp, reintroduce-else
    if user == guild.owner:
        return False

    return me.top_role > user.top_role


def author_above(author, user, guild):
    # sourcery skip: assign-if-exp, reintroduce-else
    if author == guild.owner:
        return True

    if user == guild.owner:
        return False

    return author.top_role > user.top_role


def check_uuid(uuid, version):
    try:
        uuid_obj = UUID(uuid, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid


def is_emoji(char):
    if char is None:
        return True

    return emoji.is_emoji(char)

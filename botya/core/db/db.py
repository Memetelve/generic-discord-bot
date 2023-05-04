import uuid
import json
import asyncio

from functools import wraps
from supabase import create_client

from botya.core.errors import (
    InvalidAdmin,
    InvalidGuild,
    InvalidId,
    DuplicateKey,
    InvalidKey,
    UnauthorizedAccess,
)

with open("config.json") as config:
    config = json.load(config)
    config = config["db_credentials"]

    url = config["url"]
    key = config["key"]


def async_wrap(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)

    return async_wrapper


class Database:
    def __init__(self):
        pass

    @async_wrap
    def create_guild(guild_id):
        supabase = create_client(url, key)
        try:
            supabase.table("guild_settings").insert(
                {"guild_id": guild_id, "timezone": "UTC"}
            ).execute()
        except Exception:
            pass

        try:
            supabase.table("guild_info").insert({"guild_id": guild_id}).execute()
        except Exception:
            pass

    @async_wrap
    def set_log_settings(guild_id, action, channel, active):
        asyncio.run(Database.create_guild(guild_id))

        supabase = create_client(url, key)
        if channel:
            supabase.table("guild_settings").update({action: channel.id}).eq(
                "guild_id", guild_id
            ).execute()
        if active:
            supabase.table("guild_settings").update({f"{action}_active": active}).eq(
                "guild_id", guild_id
            ).execute()

    @async_wrap
    def get_log_settings(guild_id, action):
        supabase = create_client(url, key)

        data = (
            supabase.table("guild_settings")
            .select("*")
            .eq("guild_id", guild_id)
            .execute()
        )

        try:
            ret = data.data[0][action]
        except IndexError:
            return 0, False

        return ret, data.data[0][f"{action}_active"]

    @async_wrap
    def create_warn(guild_id, user_id, admin_id, reason):
        supabase = create_client(url, key)

        warn_id = str(uuid.uuid4())

        supabase.table("warns").insert(
            {
                "id": warn_id,
                "guild_id": guild_id,
                "user_id": user_id,
                "admin_id": admin_id,
                "reason": reason,
            }
        ).execute()

        return warn_id

    @async_wrap
    def get_warns(guild_id, user_id=None):
        supabase = create_client(url, key)

        if user_id:
            data = (
                supabase.table("warns")
                .select("*")
                .eq("guild_id", guild_id)
                .eq("user_id", user_id)
                .execute()
            )
        else:
            data = (
                supabase.table("warns").select("*").eq("guild_id", guild_id).execute()
            )

        return data.data

    @async_wrap
    def edit_warn(guild_id, admin_id, warn_id, reason):
        supabase = create_client(url, key)

        warn = supabase.table("warns").select("*").eq("id", warn_id).execute()

        if len(warn.data) > 0:
            warn = warn.data[0]
        else:
            raise InvalidId("Warning with this id does not exist")

        if warn["guild_id"] != guild_id:
            raise InvalidGuild("Warning with this id does not exist")
        elif warn["admin_id"] != admin_id:
            raise InvalidAdmin("You are not the admin which issued this warning")

        supabase.table("warns").update({"reason": reason}).eq("id", warn_id).execute()

    @async_wrap
    def delete_warn(guild_id, warn_id):
        supabase = create_client(url, key)

        warn = supabase.table("warns").select("*").eq("id", warn_id).execute()

        if len(warn.data) > 0:
            warn = warn.data[0]
        else:
            raise InvalidId("Warning with this id does not exist")

        if warn["guild_id"] != guild_id:
            raise InvalidGuild("Warning with this id does not exist")

        supabase.table("warns").delete().eq("id", warn_id).execute()

    @async_wrap
    def add_autorole(guild_id, role):
        supabase = create_client(url, key)

        try:
            supabase.table("auto_roles").insert(
                {"guild_id": guild_id, "role_id": role.id}
            ).execute()
        except Exception as e:
            raise DuplicateKey(f"{role.mention} is already an autorole") from e

    @async_wrap
    def remove_autorole(guild_id, role):
        supabase = create_client(url, key)

        atrole = (
            supabase.table("auto_roles")
            .select("*")
            .eq("guild_id", guild_id)
            .eq("role_id", role.id)
            .execute()
        )
        if len(atrole.data) > 0:
            atrole = atrole.data[0]
        else:
            raise InvalidId(f"{role.mention} is not an autorole")

        supabase.table("auto_roles").delete().eq("role_id", role.id).execute()

    @async_wrap
    def get_autoroles(guild_id):
        supabase = create_client(url, key)
        roles = (
            supabase.table("auto_roles")
            .select("role_id")
            .eq("guild_id", guild_id)
            .execute()
        )

        return [role["role_id"] for role in roles.data]

    @async_wrap
    def set_welcome_message(guild_id, channel_id=None, message=None, active=None):
        asyncio.run(Database.create_guild(guild_id))

        supabase = create_client(url, key)

        if message:
            supabase.table("guild_settings").update({"welcome_message": message}).eq(
                "guild_id", guild_id
            ).execute()
        if channel_id:
            supabase.table("guild_settings").update({"welcome_channel": channel_id}).eq(
                "guild_id", guild_id
            ).execute()
        if active:
            supabase.table("guild_settings").update({"welcome_active": active}).eq(
                "guild_id", guild_id
            ).execute()

    @async_wrap
    def get_welcome_message(guild_id):
        supabase = create_client(url, key)

        data = (
            supabase.table("guild_settings")
            .select("*")
            .eq("guild_id", guild_id)
            .execute()
        )

        try:
            active = data.data[0]["welcome_active"]
        except IndexError:
            active = True

        try:
            msg = data.data[0]["welcome_message"]
            channel_id = data.data[0]["welcome_channel"]
        except IndexError:
            return "", 0, False

        return msg, channel_id, active

    @async_wrap
    def add_reaction_role(role_id):
        supabase = create_client(url, key)

        try:
            supabase.table("autoroles").insert({"role_id": role_id}).execute()
        except Exception:
            pass

    @async_wrap
    def get_reation_roles():
        supabase = create_client(url, key)

        data = supabase.table("autoroles").select("*").execute()

        return data.data

    @async_wrap
    def set_timezone(guild_id, zone):
        supabase = create_client(url, key)
        asyncio.run(Database.create_guild(guild_id))

        supabase.table("guild_settings").update({"timezone": zone}).eq(
            "guild_id", guild_id
        ).execute()

    @async_wrap
    def get_timezone(guild_id):
        supabase = create_client(url, key)
        asyncio.run(Database.create_guild(guild_id))

        data = (
            supabase.table("guild_settings")
            .select("timezone")
            .eq("guild_id", guild_id)
            .execute()
        )

        return data.data[0]["timezone"]

    @async_wrap
    def get_guild_settings(guild_id):
        supabase = create_client(url, key)
        asyncio.run(Database.create_guild(guild_id))

        data = (
            supabase.table("guild_settings")
            .select("*")
            .eq("guild_id", guild_id)
            .execute()
        )

        return data.data[0]

    @async_wrap
    def set_tickets(guild_id, cat1, cat2):
        supabase = create_client(url, key)
        asyncio.run(Database.create_guild(guild_id))

        supabase.table("guild_settings").update(
            {"tickets_cat1": cat1, "tickets_cat2": cat2}
        ).eq("guild_id", guild_id).execute()

    @async_wrap
    def get_open_tickets_category_id(guild_id):
        supabase = create_client(url, key)
        asyncio.run(Database.create_guild(guild_id))

        data = (
            supabase.table("guild_settings")
            .select("tickets_cat1")
            .eq("guild_id", guild_id)
            .execute()
        )

        return data.data[0]["tickets_cat1"]

    @async_wrap
    def get_closed_tickets_category_id(guild_id):
        supabase = create_client(url, key)
        asyncio.run(Database.create_guild(guild_id))

        data = (
            supabase.table("guild_settings")
            .select("tickets_cat2")
            .eq("guild_id", guild_id)
            .execute()
        )

        return data.data[0]["tickets_cat2"]

    @async_wrap
    def update_ticket_count(guild_id):
        supabase = create_client(url, key)
        asyncio.run(Database.create_guild(guild_id))

        # get current count
        data = (
            supabase.table("guild_info")
            .select("ticket_count")
            .eq("guild_id", guild_id)
            .execute()
        )
        count = data.data[0]["ticket_count"]

        # set count + 1
        supabase.table("guild_info").update({"ticket_count": count + 1}).eq(
            "guild_id", guild_id
        ).execute()

    @async_wrap
    def get_ticket_count(guild_id) -> int:
        supabase = create_client(url, key)
        asyncio.run(Database.create_guild(guild_id))

        data = (
            supabase.table("guild_info")
            .select("ticket_count")
            .eq("guild_id", guild_id)
            .execute()
        )

        return data.data[0]["ticket_count"]

    #
    # Invites tracking
    #

    @async_wrap
    def add_invite(guild_id, invited_user_id, inviting_user_id, invite_url):
        supabase = create_client(url, key)
        # add invite to database

        status = 2 if invited_user_id == inviting_user_id else 0
        # check if invite exists
        data = (
            supabase.table("invites")
            .select("invite_url")
            .eq("guild_id", guild_id)
            .eq("invited_user_id", invited_user_id)
            .execute()
        )
        if not data.data:
            supabase.table("invites").insert(
                {
                    "guild_id": guild_id,
                    "invited_user_id": invited_user_id,
                    "inviting_user_id": inviting_user_id,
                    "invite_url": invite_url,
                    "status": status,
                }
            ).execute()
        else:
            supabase.table("invites").update({"status": status}).eq(
                "guild_id", guild_id
            ).eq("invited_user_id", invited_user_id).execute()

        return

    @async_wrap
    def make_invite_leave(guild_id, user_id):
        supabase = create_client(url, key)
        # make invite leave
        try:
            supabase.table("invites").update({"status": 1}).eq("guild_id", guild_id).eq(
                "invited_user_id", user_id
            ).execute()
        except Exception:
            pass

    @async_wrap
    def get_invites(guild_id, user_id):
        supabase = create_client(url, key)
        # get all invites for user in guild
        data = (
            supabase.table("invites")
            .select("*")
            .eq("guild_id", guild_id)
            .eq("inviting_user_id", user_id)
            .execute()
        )

        return data.data

    @async_wrap
    def save_guild(guild_id, owner_id, json, save_name, note):
        supabase = create_client(url, key)

        data = (
            supabase.table("saves")
            .insert(
                {
                    "guild_id": guild_id,
                    "owner_id": owner_id,
                    "save": json,
                    "guild_name": save_name,
                    "notes": note,
                }
            )
            .execute()
        )

        return data.data[0]["id"]

    @async_wrap
    def get_saves(user_id):
        supabase = create_client(url, key)

        data = supabase.table("saves").select("*").eq("owner_id", user_id).execute()

        return data.data

    @async_wrap
    def load_guild(save_uuid, user_id):
        supabase = create_client(url, key)

        try:
            data = supabase.table("saves").select("*").eq("id", save_uuid).execute()
        except Exception as e:
            raise InvalidKey("Save not found") from e

        if data.data[0]["owner_id"] != user_id:
            raise UnauthorizedAccess("You are not the owner of this save")

        return data.data[0]["save"]

    @async_wrap
    def get_premium():
        supabase = create_client(url, key)
        data = supabase.table("premium").select("*").execute()
        return data.data

    @async_wrap
    def set_war_notifier(guild_id, channel_id, clan_tag, active):
        asyncio.run(Database.create_guild(guild_id))

        supabase = create_client(url, key)

        # update guild setting

        supabase.table("guild_settings").update(
            {
                "coc_war_active": active,
                "coc_war_channel": channel_id,
                "coc_clan_tag": clan_tag,
            }
        ).eq("guild_id", guild_id).execute()

    @async_wrap
    def set_war_status(guild_id, status):
        supabase = create_client(url, key)

        # update guild setting

        supabase.table("guild_settings").update(
            {
                "last_coc_war_status": status,
            }
        ).eq("guild_id", guild_id).execute()

    @async_wrap
    def get_all_wars():
        supabase = create_client(url, key)
        data = (
            supabase.table("guild_settings")
            .select("*")
            .eq("coc_war_active", True)
            .execute()
        )
        return data.data

    @async_wrap
    def generate_tokens(amount: int, type: str):
        supabase = create_client(url, key)

        tokens = []

        for _ in range(amount):
            token = str(uuid.uuid4())
            tokens.append(token)
            supabase.table("tokens").insert(
                {"token": token, "type": type, "used": False}
            ).execute()

        return tokens

    @async_wrap
    def update_last_war_start_time(guild_id, time):
        supabase = create_client(url, key)
        supabase.table("guild_settings").update(
            {
                "last_coc_war_start_time": time,
            }
        ).eq("guild_id", guild_id).execute()

    @async_wrap
    def set_premium(id, date, premium_type, premium_tier):
        supabase = create_client(url, key)

        # check if premium exists
        data = supabase.table("premium").select("id").eq("id", id).execute()
        if not data.data:
            supabase.table("premium").insert(
                {
                    "id": id,
                    "premium_until": date,
                    "premium_type": premium_type,
                    "premium_tier": premium_tier,
                }
            ).execute()
        else:
            supabase.table("premium").update(
                {
                    "premium_until": date,
                    "premium_type": premium_type,
                    "premium_tier": premium_tier,
                }
            ).eq("id", id).execute()

        return True

    @async_wrap
    def create_gpt_conversation(user_id):
        supabase = create_client(url, key)
        data = (
            supabase.table("gpt_conversations")
            .insert(
                {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "active": True,
                    "conversation": [],
                }
            )
            .execute()
        )

        return data.data

    @async_wrap
    def get_gpt_conversation(user_id):
        supabase = create_client(url, key)
        data = (
            supabase.table("gpt_conversations")
            .select("*")
            .eq("user_id", user_id)
            .eq("active", True)
            .execute()
        )

        if not data.data:
            return asyncio.run(Database.create_gpt_conversation(user_id))

        return data.data

    @async_wrap
    def edit_gpt_conversation(user_id, conversation, tokens):
        supabase = create_client(url, key)
        supabase.table("gpt_conversations").update(
            {"conversation": conversation, "tokens": tokens}
        ).eq("user_id", user_id).eq("active", True).execute()

    @async_wrap
    def render_gpt_conversation_inactive(user_id):
        supabase = create_client(url, key)
        supabase.table("gpt_conversations").update({"active": False}).eq(
            "user_id", user_id
        ).eq("active", True).execute()

    @async_wrap
    def get_gpt_conversations_by_user(user_id):
        supabase = create_client(url, key)

        data = (
            supabase.table("gpt_conversations")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        return data.data

    @async_wrap
    def add_admin_log(command):
        supabase = create_client(url, key)

        # uuid
        my_id = str(uuid.uuid4())

        supabase.table("admin_log").insert({"id": my_id, "command": command}).execute()

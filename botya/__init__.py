import json
import asyncio

from botya.core.db.db import Database
from botya.core.utils.types import tz

from dateutil import parser

with open("config.json", "r") as f:
    config = json.load(f)

    DEBUG = config["debug"]
    OPENAI_API_KEY = config["openai_api_key"]

__version__ = "v1.1"

# get premium users and servers


premium_users = asyncio.run(Database.get_premium())
premium_ent: dict = {}
for user in premium_users:
    premium_ent[user["id"]] = {
        "premium_tier": int(user["premium_tier"]),
        "premium_until": parser.parse(user["premium_until"]).replace(tzinfo=tz),
        "premium_type": user["premium_type"],
    }

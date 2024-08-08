from fastapi import APIRouter, Request
import sys

import os
import requests

# AWS DynamoDB
from db.models.bot.bot import Bots
from db.models.users.user import UserData

# add directory so it works without
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from utils.generate_id import generate_id
from dotenv import load_dotenv
load_dotenv()

test_mode = False

MAIN_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# secret used to authenticate a webhook
TELEGRAM_WEBHOOK_SECRET_TOKEN = os.getenv("TELEGRAM_WEBHOOK_SECRET_TOKEN")

WEBHOOK_URL = "https://youcorp.com/api/messaging/telegram_message"

# set to local ngrok url if test mode
if test_mode:
    WEBHOOK_URL = "https://4e5c-34-228-244-10.ngrok.io/messaging/telegram_message"



router = APIRouter(
    prefix="/api/messaging",
    tags=["messaging"],
    # dependencies=[Depends(validate_access_token)],
    # responses={404: {"description": "Not found"}},
)

async def set_webhook_2(
    token=MAIN_BOT_TOKEN,
    webhook_token=TELEGRAM_WEBHOOK_SECRET_TOKEN,
    webhook_url=WEBHOOK_URL,
):
    # setup webhook for telegram
    url = (
        f"https://api.telegram.org/bot{token}/setWebhook?url="
        + webhook_url
        + "&secret_token="
        + webhook_token
        + '&allowed_updates=["callback_query","message","pre_checkout_query","channel_post","chat_member"]'
    )

    r = requests.post(url)
    # print response data
    print(r.text)
    return r


async def unset_webhook(token=MAIN_BOT_TOKEN):
    # setup webhook for telegram
    url = f"https://api.telegram.org/bot{token}/setWebhook?url="

    r = requests.post(url)
    # print response data
    print(r.text)
    return r


# all the tokens possible for all the bots


async def unset_and_set_webhook(bot_id: str, bot_token: str):
    token = bot_token
    webhook_token = TELEGRAM_WEBHOOK_SECRET_TOKEN+'--'+ bot_id
    webhook_url = WEBHOOK_URL + "/" + bot_id

    print('token', webhook_token, webhook_url)

    # set main bot webhook
    await unset_webhook(token)
    await set_webhook_2(token, webhook_token, webhook_url)

# https://telegram.me/MeebleBot?start=taayjus
@router.post("/tg_setting")
async def handle_telegram_setting(request: Request) -> str:
    try:
        incoming_data = await request.json()
        print('start for setting telegram webhook', incoming_data)
        await unset_and_set_webhook(incoming_data['bot_id'], incoming_data['bot_token'])
        return "success"
    except Exception as e:
        print(e)
        return "error"

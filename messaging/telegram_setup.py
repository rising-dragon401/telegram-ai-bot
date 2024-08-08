test_mode = False
import sys

import os
import asyncio
import requests

# add directory so it works without
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))


from messaging.platforms_data import telegram_creator_ids_to_tokens
from dotenv import load_dotenv
load_dotenv()

MAIN_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# secret used to authenticate a webhook
TELEGRAM_WEBHOOK_SECRET_TOKEN = os.getenv("TELEGRAM_WEBHOOK_SECRET_TOKEN")

WEBHOOK_URL = "https://youcorp.com/api/messaging/telegram_message"

# set to local ngrok url if test mode
if test_mode:
    WEBHOOK_URL = "https://4e5c-34-228-244-10.ngrok.io/messaging/telegram_message"


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


async def unset_and_set_webhook():
    await unset_webhook()
    await set_webhook_2()


# all the tokens possible for all the bots


async def unset_and_set_webhook_for_all_bots():
    # set main bot webhook
    await unset_webhook()
    await set_webhook_2()

    # set each creator bot token
    for creator_id, creator_data in telegram_creator_ids_to_tokens.items():
        token = creator_data["token"]
        webhook_token = creator_data["webhook_token"]
        webhook_url = WEBHOOK_URL + "/" + creator_id

        await unset_webhook(token)
        await set_webhook_2(token, webhook_token, webhook_url)


asyncio.run(unset_and_set_webhook_for_all_bots())

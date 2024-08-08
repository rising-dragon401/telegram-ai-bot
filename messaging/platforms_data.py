import os
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_WEBHOOK_SECRET_TOKEN = os.getenv("TELEGRAM_WEBHOOK_SECRET_TOKEN")

# creator id to telegram bot data
telegram_bot_ids_to_tokens = {
  'NMjinyaIHJVrmTNYm4XTYlwqsQ02': {
    'token': '6156744908:AAE7zoPE0LtK7Pxq1l4nQtWjCE_3B7G97DI',
    'webhook_token': TELEGRAM_WEBHOOK_SECRET_TOKEN+'--'+ 'NMjinyaIHJVrmTNYm4XTYlwqsQ02',
    'stripe_token': '284685063:TEST:MzVkYjhlYTIzMTZh'
  },
  'oTSM6Kyjqaesnw663LGyFFvtBEH2': {
    'token': '6169419402:AAED2MNWaRK6p_S-tWhl_n0C-y2ZOrk_eU8',
    'webhook_token': TELEGRAM_WEBHOOK_SECRET_TOKEN + '--'+ 'oTSM6Kyjqaesnw663LGyFFvtBEH2',
    'stripe_token': '350862534:LIVE:N2VlMWMyNGI5NmMw'
  },
  '2DvPhc81QaavmVQ1igPtQIjtfQj2': {
    'token': '6066961687:AAEy_COG9rsdRTWAih12PzCXsvYfbk4uDJs',
    'webhook_token': TELEGRAM_WEBHOOK_SECRET_TOKEN + '--'+ '2DvPhc81QaavmVQ1igPtQIjtfQj2',
    'stripe_token': '284685063:TEST:MzVkYjhlYTIzMTZh'
  }
}

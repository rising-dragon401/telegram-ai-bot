import os
import logging

# Third Party API
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create client
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)

# Phone number to send from
from_phone_number = "+18559301985"


def send_message(to, body):
  message = client.messages.create(
    body=body,
    from_=from_phone_number,
    to=to
  )
  print(message.sid)

def send_message_to_whatsApp(to_number, from_number, body = '', url = ''):
    try:
        if url == '':
          message = client.messages.create(
              from_=from_number,
              body=f'{body}',
              to=to_number,
            )
        else: 
          message = client.messages.create(
              from_=from_number,
              body=f'{body}',
              media_url=f'{url}',
              to=to_number,
            )
        logger.info(f"Message sent to {to_number}: {message.body} {url}")
    except Exception as e:
        logger.error(f"Error sending message to {to_number}: {e}")
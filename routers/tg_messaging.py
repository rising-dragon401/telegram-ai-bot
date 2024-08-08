from fastapi import APIRouter, Request, Form, Response, Path
from urllib.parse import quote

# AWS DynamoDB
from db.models.bot.bot import Bots
from db.models.users.user import UserData
from db.models.todo.todo import Todo
from db.models.qna.qna import QnAData
from db.models.qna.notion import NotionCRUD

from messaging.platforms_data import telegram_bot_ids_to_tokens

from pydub import AudioSegment
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

import os
import requests
from datetime import datetime
from ai.ai_api import transcribe_audio

import traceback
from ai.ai_api import create_chat_completion, create_chat_message
from ai.langchain import get_ai_response_by_pinecone, get_ai_response_by_pinecone_to_do, get_to_do, compare_message_chat_history, get_ai_response_qa, get_qna

from voice.generator import generate_voice

from dotenv import load_dotenv
load_dotenv()

RESPONSE_LENGTH = ['Concise', 'Normal', 'Detailed']

CREATOR_NAME = "Roger Elliott"

# Token from bot fateher
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Secret key set to verify webhook
TELEGRAM_WEBHOOK_SECRET_TOKEN = os.getenv("TELEGRAM_WEBHOOK_SECRET_TOKEN")

# Token that bot father gives after connecting stripe
STRIPE_TOKEN = os.getenv("TELEGRAM_STRIPE_TOKEN")
telegram_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

router = APIRouter(
    prefix="/api/messaging",
    tags=["messaging"],
    # dependencies=[Depends(validate_access_token)],
    # responses={404: {"description": "Not found"}},
)


def get_telegram_bot_token(bot_id=""):
    if bot_id:
        bot = Bots.get_bot_by_id(bot_id)
        return bot['token']
    else:
        # if no bot_id provided, return main bot token
        return TELEGRAM_BOT_TOKEN


def get_stripe_token_for_bot(bot_id=""):
    if bot_id:
        return telegram_bot_ids_to_tokens[bot_id]["stripe_token"]
    else:
        # if no bot_id provided, return main bot token
        return STRIPE_TOKEN


@router.post("/handle_sms")
async def handle_sms(From: str = Form(...), Body: str = Form(...)) -> str:
    print("HERE!")

    # see if user first
    return Response(content=str(''), media_type="application/xml")


def tel_send_chat_action(chat_id, action="typing", bot_id=""):
    """
    An action such as typing, recording, uploading, etc.
    """
    url = f"https://api.telegram.org/bot{get_telegram_bot_token(bot_id)}/sendChatAction"
    payload = {"chat_id": chat_id, "action": action}

    r = requests.post(url, json=payload, timeout=120)

    return r


def tel_set_chat_title(chat_id, title, bot_id=""):
    """
    Change the title of a chat. Titles can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns True on success.
    """
    url = (
        f"https://api.telegram.org/bot{get_telegram_bot_token(bot_id)}/setChatTitle"
    )
    payload = {"chat_id": chat_id, "title": title}

    r = requests.post(url, json=payload, timeout=120)

    return r


def tel_send_message(
    chat_id, text, reply_to_message_id="", reply_markup=None, bot_id=""
):
    url = (
        f"https://api.telegram.org/bot{get_telegram_bot_token(bot_id)}/sendMessage"
    )

    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_to_message_id": reply_to_message_id,
        "allow_sending_without_reply": False,
    }

    # if reply_markup:
    #   payload['reply_markup'] = reply_markup

    r = requests.post(url, json=payload, timeout=120)

    return r


def tel_send_image(chat_id, photo_url, message="", bot_id=""):
    url = f"https://api.telegram.org/bot{get_telegram_bot_token(bot_id)}/sendPhoto"

    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": message,
    }

    r = requests.post(url, json=payload, timeout=120)
    # print response as text
    print(r.text)

    # if response is not ok, print error
    if not r.ok:
        return tel_send_message(chat_id, message, bot_id=bot_id)

    return r


def tel_set_chat_photo(chat_id, photo_url, bot_id=""):
    # download photo locally from photo_url
    response = requests.get(photo_url, timeout=120)

    with open(f"temp/{chat_id}-chat-photo.jpg", "wb") as f:
        f.write(response.content)

    url = (
        f"https://api.telegram.org/bot{get_telegram_bot_token(bot_id)}/setChatPhoto"
    )
    payload = {
        "chat_id": chat_id,
    }

    files = {"photo": response.content}

    r = requests.post(url, data=payload, files=files, timeout=120).json()

    print(r)

    return r


def tel_send_voice(chat_id, audio, bot_id="", reply_to_message_id=""):
    # get current datetime and convert to string

    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

    payload = {
        "chat_id": chat_id,
        "title": dt_string,
        "parse_mode": "HTML",
        "reply_to_message_id": reply_to_message_id,
        "allow_sending_without_reply": True,
    }
    files = {
        "voice": audio,
    }
    resp = requests.post(
        f"https://api.telegram.org/bot{get_telegram_bot_token(bot_id)}/sendVoice",
        data=payload,
        files=files, timeout=120
    ).json()
    return resp


def handle_command(chat_id, message, full_data, user_id, bot, group_chat=False):
    print("handling command")

    message_id = full_data["message"]["message_id"]

    # if start, add chat_id to the user with user_id provided
    if "/start" in message:
        tel_send_image(chat_id, bot["botAvatar"], f'{bot["botName"]}', bot['botID'])

        bot_type = bot['botType']
        if bot_type == 3:
            if group_chat == True:
                is_group_data = UserData.user_data_exists(chat_id, chat_id, bot['botID'])

                if is_group_data == True:
                    group_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
                    chat_history = group_data['chat_history']
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    UserData.update_chat_history(chat_id, chat_id, bot['botID'], chat_history)
                else:
                    chat_history = []
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    
                    chat_title = full_data['message']['chat']['title']
                    UserData.save(chat_id, chat_id, chat_title, bot['botID'], chat_history)
            else:
                # Check existing user data
                is_user_data = UserData.user_data_exists(chat_id, user_id, bot['botID'])
                
                if is_user_data == True: 
                    user_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, user_id, bot['botID'])
                    chat_history = user_data['chat_history']
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    
                    UserData.update_chat_history(chat_id, user_id, bot['botID'], chat_history)
                else:     
                    chat_history = []
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    
                    chat_title = full_data['message']['from']['first_name'] + ' & ' + bot['botName']
                    UserData.save(chat_id, user_id, chat_title, bot['botID'], chat_history)
        elif bot_type == 2:
            if group_chat == True:
                is_group_data = UserData.user_data_exists(chat_id, chat_id, bot['botID'])

                if is_group_data == True:
                    group_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
                    chat_history = group_data['chat_history']
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    UserData.update_chat_history(chat_id, chat_id, bot['botID'], chat_history)
                    
                else:
                    chat_history = []
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    
                    chat_title = full_data['message']['chat']['title']
                    UserData.save(chat_id, chat_id, chat_title, bot['botID'], chat_history)
                    QnAData.save(chat_id, chat_id, bot['botID'])
                    NotionCRUD.create(chat_title, chat_id, chat_id, bot['botID'], bot['notionID'])
            else:
                # Check existing user data
                is_user_data = UserData.user_data_exists(chat_id, user_id, bot['botID'])
                
                if is_user_data == True: 
                    user_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, user_id, bot['botID'])
                    chat_history = user_data['chat_history']
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    
                    UserData.update_chat_history(chat_id, user_id, bot['botID'], chat_history)
                else:     
                    chat_history = []
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    
                    chat_title = full_data['message']['from']['first_name'] + ' & ' + bot['botName']
                    
                    UserData.save(chat_id, user_id, chat_title, bot['botID'], chat_history)
                    QnAData.save(chat_id, user_id, bot['botID'])
                    NotionCRUD.create(chat_title, chat_id, user_id, bot['botID'], bot['notionID'])
        elif bot_type == 1:
            if group_chat == True:
                is_group_data = UserData.user_data_exists(chat_id, chat_id, bot['botID'])

                if is_group_data == True:
                    group_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
                    chat_history = group_data['chat_history']
                    if bot["greettingEnable"]:
                        
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                        
                    UserData.update_chat_history(chat_id, chat_id, bot['botID'], chat_history)
                else:
                    chat_history = []
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    
                    chat_title = full_data['message']['chat']['title']
                    UserData.save(chat_id, chat_id, chat_title, bot['botID'], chat_history)
                    Todo.save(chat_id, chat_id, bot['botID'])
            else:
                # Check existing user data
                is_user_data = UserData.user_data_exists(chat_id, user_id, bot['botID'])
                
                if is_user_data == True: 
                    user_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, user_id, bot['botID'])
                    chat_history = user_data['chat_history']
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    
                    UserData.update_chat_history(chat_id, user_id, bot['botID'], chat_history)
                else:     
                    chat_history = []
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    
                    chat_title = full_data['message']['from']['first_name'] + ' & ' + bot['botName']
                    UserData.save(chat_id, user_id, chat_title, bot['botID'], chat_history)
                    Todo.save(chat_id, chat_id, bot['botID'])
        else:
            if group_chat == True:
                is_group_data = UserData.user_data_exists(chat_id, chat_id, bot['botID'])

                if is_group_data == True:
                    group_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
                    chat_history = group_data['chat_history']
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    UserData.update_chat_history(chat_id, chat_id, bot['botID'], chat_history)
                else:
                    chat_history = []
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    
                    chat_title = full_data['message']['chat']['title']
                    UserData.save(chat_id, chat_id, chat_title, bot['botID'], chat_history)
            else:
                # Check existing user data
                is_user_data = UserData.user_data_exists(chat_id, user_id, bot['botID'])
                
                if is_user_data == True: 
                    user_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, user_id, bot['botID'])
                    chat_history = user_data['chat_history']
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    
                    UserData.update_chat_history(chat_id, user_id, bot['botID'], chat_history)
                else:     
                    chat_history = []
                    if bot["greettingEnable"]:
                        handleResponseWithChatCommand(chat_id, bot["greetting"], bot)
                        chat_history.append(create_chat_message("assistant", bot["greetting"]))
                    
                    chat_title = full_data['message']['from']['first_name'] + ' & ' + bot['botName']
                    UserData.save(chat_id, user_id, chat_title, bot['botID'], chat_history)

        return "success"
    elif "/purchase" in message:
        pass
    elif "/balance" in message:
        return tel_send_message(
            chat_id,
            f"Your balance is $500",
            message_id,
        )
    elif "/help" in message:
        return tel_send_message(
            chat_id,
            "Need help with something? Send us a message @BeemoHelp",
            message_id,
        )


# Gets the message text from incoming_data
# If it is an audio type, uses Whisper to transcribe
def get_message_text_from_update(incoming_data):

    # otherwise, just get the text element if channel_post or message
    if "channel_post" in incoming_data and "text" in incoming_data["channel_post"]:
        message = incoming_data["channel_post"]["text"]
    elif "message" in incoming_data and "text" in incoming_data["message"]:
        message = incoming_data["message"]["text"]
    else:
        message = ""
    return message

def verify_secure_webhook(headers):
    # verify webhook
    if "x-telegram-bot-api-secret-token" in headers:
        if (
            os.getenv("TELEGRAM_WEBHOOK_SECRET_TOKEN")
            in headers["x-telegram-bot-api-secret-token"]
        ):
            return True
        else:
            return False
    else:
        return False


def answer_pre_checkout_query(incoming_data):
    id = incoming_data["pre_checkout_query"]["id"]
    telegram_bot.answer_pre_checkout_query(id, True)
    return "success"


def get_respond_training_prompt(user_message, current_context, bot):
  cite_prompt = ""
  if(bot["isCitingSource"]): cite_prompt = "You have to cite sources when answering."
  else: cite_prompt=""

  respond_training_prompt = (
    f"{bot['rolePrompt']}\n"
    f"Your response must be {RESPONSE_LENGTH[int(bot['responseLength'])]}."
    f"{cite_prompt}"
    f"You have to speak in {bot['language']} throughout the conversation.\n"
    f"{current_context}"
    f"You will take into account the whole conversation, focusing on what is asked in the last user message."
    f"Your user has just sent you this message:"
    f"{user_message}"
    f"Your response:"
  )
  return respond_training_prompt

def get_ai_response(message, chat_history, bot):
    # Keep track of current context

    current_context = chat_history

    cite_prompt = ""
    if(bot["isCitingSource"]): cite_prompt = "You have to cite sources when answering."
    else: cite_prompt=""

    initial_response_prompt = (
        f"{bot['rolePrompt']}\n"
        f"Your response must be {RESPONSE_LENGTH[int(bot['responseLength'])]}."
        f"{cite_prompt}"
        f"You have to speak in {bot['language']} throughout the conversation.\n"
        f"{current_context}"
        f"You will take into account the whole conversation, focusing on what is asked in the last user message."
    )

    current_context = [create_chat_message("system", initial_response_prompt)]

    # get first ai message
    last_ai_message = create_chat_completion(current_context, float(bot['creativity']), 500, bot['model'])

    # add assistant message to context
    current_context.append(create_chat_message("assistant", last_ai_message))

    # Add the user input to the context
    current_context.append(create_chat_message("user", message))
    

    # # Now add a system prompt to instruct AI to respond to last user's message
    current_context.append(create_chat_message("system", get_respond_training_prompt(message, current_context, bot)))

    # Set the last_ai_message as the response to the user's message
    last_ai_message = create_chat_completion(current_context, float(bot['creativity']), 500, bot['model'])
    # Add the assistant response to the context
    current_context.append(create_chat_message("assistant", last_ai_message))

    filtered_data = [d for d in current_context if d['role'] != 'system']

    # save training_data list to text file to be loaded later

    return { 'ai_response': last_ai_message, 'chat_history': filtered_data }


def handle_user_message(incoming_data,
    chat_id, message, message_id, user_id, bot, group_chat=False
):
    # print current time milis
    print("\n**********CURRENT TIME**********\n", message)
    print(datetime.now().timestamp())

    try:
        if message != '':
            bot_type = bot['botType']
            if bot_type == 3:
                if group_chat == True:
                    is_group_data = UserData.user_data_exists(chat_id, chat_id, bot['botID'])
                    if is_group_data == True:
                        group_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
                        chat_history = group_data['chat_history']    
                        summary = group_data['summary']
                        history_cursor = group_data['history_cursor']

                        tel_send_chat_action(chat_id, 'typing', bot['botID'])

                        is_repeat_request = compare_message_chat_history(message, chat_history)
                        if is_repeat_request:
                            return 'success'
                        
                        response = get_ai_response_by_pinecone(message, chat_history, bot, summary, history_cursor)
                        ai_response = response['ai_response']
                        new_chat_history = response['chat_history']
                        new_summary = response['summary']
                        new_history_cursor = response['history_cursor']
                        UserData.update_chat_history(chat_id, chat_id, bot['botID'], new_chat_history, new_summary, new_history_cursor)
                        audio = generate_voice(CREATOR_NAME, ai_response)
                        tel_send_voice(chat_id, audio, bot['botID'])
                        # handleResponseWithChatCommand(chat_id, ai_response, bot)
                    else: 
                        tel_send_message(
                            chat_id,
                            "Please start conversation with '/start' chat command.",
                            message_id,
                            bot_id=bot["botID"],
                        )
                else:
                    # Check existing user data
                    is_user_data = UserData.user_data_exists(chat_id, user_id, bot['botID'])
                    
                    if is_user_data == True: 
                        user_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, user_id, bot['botID'])
                        chat_history = user_data['chat_history']    
                        summary = user_data['summary']
                        history_cursor = user_data['history_cursor']

                        tel_send_chat_action(chat_id, 'typing', bot['botID'])

                        is_repeat_request = compare_message_chat_history(message, chat_history)
                        if is_repeat_request:
                            return 'success'

                        response = get_ai_response_by_pinecone(message, chat_history, bot, summary, history_cursor)
                        ai_response = response['ai_response']
                        new_chat_history = response['chat_history']
                        new_summary = response['summary']
                        new_history_cursor = response['history_cursor']
                        UserData.update_chat_history(chat_id, user_id, bot['botID'], new_chat_history, new_summary, new_history_cursor)
                        audio = generate_voice(CREATOR_NAME, ai_response)
                        tel_send_voice(chat_id, audio, bot['botID'])
                        # handleResponseWithChatCommand(chat_id, ai_response, bot)
                    else:     
                        tel_send_message(
                            chat_id,
                            "Please start conversation with '/start' chat command.",
                            message_id,
                            bot_id=bot["botID"],
                        )
            elif bot_type == 2:
                if group_chat == True:
                    is_group_data = UserData.user_data_exists(chat_id, chat_id, bot['botID'])
                    if is_group_data == True:
                        group_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
                        chat_history = group_data['chat_history']    
                        summary = group_data['summary']
                        history_cursor = group_data['history_cursor']

                        tel_send_chat_action(chat_id, 'typing', bot['botID'])

                        # is_repeat_request = compare_message_chat_history(message, chat_history)
                        # if is_repeat_request:
                        #     return 'success'
                        response_qa = get_qna(message, chat_history, bot, summary, history_cursor)
                        if response_qa != None:
                            print('response_qa:', response_qa)
                            QnAData.update_qna(chat_id, chat_id, bot['botID'], bot['notionID'], response_qa)
                        
                        response = get_ai_response_qa(message, chat_history, bot, summary, history_cursor)
                        ai_response = response['ai_response']
                        new_chat_history = response['chat_history']
                        new_summary = response['summary']
                        new_history_cursor = response['history_cursor']
                        UserData.update_chat_history(chat_id, chat_id, bot['botID'], new_chat_history, new_summary, new_history_cursor)

                        handleResponseWithChatCommand(chat_id, ai_response, bot)
                    else: 
                        tel_send_message(
                            chat_id,
                            "Please start conversation with '/start' chat command.",
                            message_id,
                            bot_id=bot["botID"],
                        )
                else:
                    # Check existing user data
                    is_user_data = UserData.user_data_exists(chat_id, user_id, bot['botID'])
                    
                    if is_user_data == True: 
                        user_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, user_id, bot['botID'])
                        chat_history = user_data['chat_history']    
                        summary = user_data['summary']
                        history_cursor = user_data['history_cursor']

                        tel_send_chat_action(chat_id, 'typing', bot['botID'])

                        # is_repeat_request = compare_message_chat_history(message, chat_history)
                        # if is_repeat_request:
                        #     return 'success'
                        response_qa = get_qna(message, chat_history, bot, summary, history_cursor)
                        if response_qa != None:
                            print('response_qa:', response_qa)
                            QnAData.update_qna(chat_id, user_id, bot['botID'],bot['notionID'], response_qa)
                        
                        response = get_ai_response_qa(message, chat_history, bot, summary, history_cursor)
                        ai_response = response['ai_response']
                        new_chat_history = response['chat_history']
                        new_summary = response['summary']
                        new_history_cursor = response['history_cursor']
                        UserData.update_chat_history(chat_id, user_id, bot['botID'], new_chat_history, new_summary, new_history_cursor)

                        handleResponseWithChatCommand(chat_id, ai_response, bot)
                    else:     
                        tel_send_message(
                            chat_id,
                            "Please start conversation with '/start' chat command.",
                            message_id,
                            bot_id=bot["botID"],
                        )
        
            elif bot_type == 1:
                if group_chat == True:
                    is_group_data = UserData.user_data_exists(chat_id, chat_id, bot['botID'])
                    is_to_do = Todo.to_do_exists(chat_id, chat_id, bot['botID'])

                    if is_group_data == True and is_to_do == True:
                        group_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
                        group_to_do_data = Todo.get_to_do_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
                        chat_history = group_data['chat_history']    
                        to_do = group_to_do_data['to_do']      

                        tel_send_chat_action(chat_id, 'typing', bot['botID'])
                        
                        is_repeat_request = compare_message_chat_history(message, chat_history)
                        if is_repeat_request:
                            return 'success'
                        
                        response = get_to_do(message, chat_history, bot, to_do)
                        ai_response = response['ai_response']
                        new_chat_history = response['chat_history']
                        UserData.update_chat_history(chat_id, chat_id, bot['botID'], new_chat_history)

                        Todo.update_to_do(chat_id, chat_id, bot['botID'], response['to_do_data'])

                        handleResponseWithChatCommand(chat_id, ai_response, bot)
                    else: 
                        tel_send_message(
                            chat_id,
                            "Please start conversation with '/start' chat command.",
                            message_id,
                            bot_id=bot["botID"],
                        )
                else:
                    # Check existing user data
                    is_user_data = UserData.user_data_exists(chat_id, user_id, bot['botID'])
                    is_to_do = Todo.to_do_exists(chat_id, user_id, bot['botID'])
                    
                    if is_user_data == True and is_to_do == True: 
                        user_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, user_id, bot['botID'])
                        to_do_data = Todo.get_to_do_by_chat_user_bot_id(chat_id, user_id, bot['botID'])
                        chat_history = user_data['chat_history']    
                        to_do = to_do_data['to_do']      

                        tel_send_chat_action(chat_id, 'typing', bot['botID'])

                        is_repeat_request = compare_message_chat_history(message, chat_history)

                        if is_repeat_request:
                            return 'success'
                        response = get_to_do(message, chat_history,  bot, to_do)  

                        ai_response = response['ai_response']
                        new_chat_history = response['chat_history']
                        UserData.update_chat_history(chat_id, user_id, bot['botID'], new_chat_history)

                        Todo.update_to_do(chat_id, user_id, bot['botID'], response['to_do_data'])

                        handleResponseWithChatCommand(chat_id, ai_response, bot)
                    else:     
                        tel_send_message(
                            chat_id,
                            "Please start conversation with '/start' chat command.",
                            message_id,
                            bot_id=bot["botID"],
                        )
            else:
                if group_chat == True:
                    is_group_data = UserData.user_data_exists(chat_id, chat_id, bot['botID'])
                    if is_group_data == True:
                        group_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
                        chat_history = group_data['chat_history']    
                        summary = group_data['summary']
                        history_cursor = group_data['history_cursor']

                        tel_send_chat_action(chat_id, 'typing', bot['botID'])

                        # is_repeat_request = compare_message_chat_history(message, chat_history)
                        # if is_repeat_request:
                        #     return 'success'
                        
                        response = get_ai_response_by_pinecone(message, chat_history, bot, summary, history_cursor)
                        ai_response = response['ai_response']
                        new_chat_history = response['chat_history']
                        new_summary = response['summary']
                        new_history_cursor = response['history_cursor']
                        UserData.update_chat_history(chat_id, chat_id, bot['botID'], new_chat_history, new_summary, new_history_cursor)

                        handleResponseWithChatCommand(chat_id, ai_response, bot)
                    else: 
                        tel_send_message(
                            chat_id,
                            "Please start conversation with '/start' chat command.",
                            message_id,
                            bot_id=bot["botID"],
                        )
                else:
                    # Check existing user data
                    is_user_data = UserData.user_data_exists(chat_id, user_id, bot['botID'])
                    
                    if is_user_data == True: 
                        user_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, user_id, bot['botID'])
                        chat_history = user_data['chat_history']    
                        summary = user_data['summary']
                        history_cursor = user_data['history_cursor']

                        tel_send_chat_action(chat_id, 'typing', bot['botID'])

                        # is_repeat_request = compare_message_chat_history(message, chat_history)
                        # if is_repeat_request:
                        #     return 'success'

                        response = get_ai_response_by_pinecone(message, chat_history, bot, summary, history_cursor)
                        ai_response = response['ai_response']
                        new_chat_history = response['chat_history']
                        new_summary = response['summary']
                        new_history_cursor = response['history_cursor']
                        UserData.update_chat_history(chat_id, user_id, bot['botID'], new_chat_history, new_summary, new_history_cursor)

                        handleResponseWithChatCommand(chat_id, ai_response, bot)
                    else:     
                        tel_send_message(
                            chat_id,
                            "Please start conversation with '/start' chat command.",
                            message_id,
                            bot_id=bot["botID"],
                        )
        else:
            print('message is empty')
            if group_chat:
                if 'new_chat_title' in incoming_data['message']:
                    new_chat_title = incoming_data['message']['new_chat_title']
                    print('new_chat_title', new_chat_title)
                    UserData.update_chat_title(chat_id, chat_id, bot['botID'], new_chat_title)

            return 'success'
    except Exception as e:
        print(e)
        traceback.print_exc()
        return tel_send_message(
            chat_id,
            "Sorry, something went wrong. Please try again later.",
            message_id,
            bot_id=bot["botID"],
        )


def parse_telegram_data(incoming_data: dict, bot_id="") -> dict:
    parsed_output = {}

    if "channel_post" in incoming_data:  # Channel message
        parsed_output = {
            "chat_id": incoming_data["channel_post"]["chat"]["id"],
            "chat_title": incoming_data["channel_post"]["chat"]["title"],
            "message": incoming_data["channel_post"]["text"],
            "message_id": incoming_data["channel_post"]["message_id"],
            "user_id": "",
        }
    elif "message" in incoming_data:  # Normal message
        parsed_output = {
            "chat_id": incoming_data["message"]["chat"]["id"],
            "message_id": incoming_data["message"]["message_id"],
            "user_id": incoming_data["message"]["from"]["id"],
            "group_chat": incoming_data["message"]["chat"]["type"] == "group" or incoming_data["message"]["chat"]["type"] == "supergroup",
        }
    elif "callback_query" in incoming_data:  # Callback query
        parsed_output = {
            "chat_id": incoming_data["callback_query"]["message"]["chat"]["id"],
            "message": "",
            "message_id": incoming_data["callback_query"]["message"]["message_id"],
            "user_id": incoming_data["callback_query"]["from"]["id"],
            "group_chat": incoming_data["callback_query"]["message"]["chat"]["type"] == "group" or incoming_data["callback_query"]["message"]["chat"]["type"] == "supergroup",
        }

    parsed_output["message"] = get_message_text_from_update(
        incoming_data
    )

    return parsed_output


def handleResponseWithChatCommand(chat_id, text, bot):
    print("ADDING HERE!")
    markup = InlineKeyboardMarkup(row_width=2)

    for prompt in bot['suggestPrompts']:
        markup.add(InlineKeyboardButton(prompt, callback_data=prompt))
    
    # markup.add(InlineKeyboardButton("Paypal", callback_data="paypal"))
    bot_token = bot['token']
    telegram_bot = telebot.TeleBot(bot_token)
    telegram_bot.send_message(chat_id, text, reply_markup=markup)

    return "success" 

def handleResponseWithBotList(chat_id, text, bots):
    print("Here are my bots")
    markup = InlineKeyboardMarkup(row_width=2)
    for bot in bots:
        if bot['status']:
            markup.add(InlineKeyboardButton(bot["botName"], callback_data=f'/start {bot["botID"]}'))
    
    telegram_bot.send_message(chat_id, text, reply_markup=markup)

    return "success" 

# handles callback from inline buttons
def handle_callback(incoming_data, user_id, bot, group_chat=False):
    try:
        chat_id = incoming_data["callback_query"]["message"]["chat"]["id"]
        callback_data = incoming_data["callback_query"]["data"]

        tel_send_chat_action(chat_id, 'typing', bot['botID'])
        
        message = callback_data
        
        bot_type = bot['botType']
        if bot_type == 2:
            if group_chat == True:
                is_group_data = UserData.user_data_exists(chat_id, chat_id, bot['botID'])

                if is_group_data == True:
                    group_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
                    chat_history = group_data['chat_history']    
                    summary = group_data['summary']
                    history_cursor = group_data['history_cursor']

                    tel_send_chat_action(chat_id, 'typing', bot['botID'])

                    response_qa = get_qna(message, chat_history, bot, summary, history_cursor)
                    if response_qa != None:
                        print('response_qa:', response_qa)
                        QnAData.update_qna(chat_id, chat_id, bot['botID'],bot['notionID'], response_qa)
                    
                    response = get_ai_response_qa(message, chat_history, bot, summary, history_cursor)
                    ai_response = response['ai_response']
                    new_chat_history = response['chat_history']
                    new_summary = response['summary']
                    new_history_cursor = response['history_cursor']
                    UserData.update_chat_history(chat_id, chat_id, bot['botID'], new_chat_history, new_summary, new_history_cursor)
                    
                    handleResponseWithChatCommand(chat_id, ai_response, bot)
                else:
                    return
            else:
                
                user_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, user_id, bot['botID'])
                chat_history = user_data['chat_history']    
                summary = user_data['summary']
                history_cursor = user_data['history_cursor']
                tel_send_chat_action(chat_id, 'typing', bot['botID'])

                response_qa = get_qna(message, chat_history, bot, summary, history_cursor)
                if response_qa != None:
                    print('response_qa:', response_qa)
                    QnAData.update_qna(chat_id, user_id, bot['botID'], bot['notionID'],response_qa)
                
                response = get_ai_response_qa(message, chat_history, bot, summary, history_cursor)
                ai_response = response['ai_response']
                new_chat_history = response['chat_history']
                new_summary = response['summary']
                new_history_cursor = response['history_cursor']
                UserData.update_chat_history(chat_id, user_id, bot['botID'], new_chat_history, new_summary, new_history_cursor)
                
                handleResponseWithChatCommand(chat_id, ai_response, bot)
        elif bot_type == 1:
            if group_chat == True:
                is_group_data = Todo.to_do_exists(chat_id, chat_id, bot['botID'])

                if is_group_data == True:
                    group_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
                    group_to_do_data = Todo.get_to_do_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])

                    chat_history = group_data['chat_history']    
                    to_do = group_to_do_data['to_do']      

                    tel_send_chat_action(chat_id, 'typing', bot['botID'])
                    
                    response = get_ai_response_by_pinecone_to_do(message, chat_history, bot, to_do)
                    ai_response = response['ai_response']
                    new_chat_history = response['chat_history']
                    UserData.update_chat_history(chat_id, chat_id, bot['botID'], new_chat_history)
                    
                    handleResponseWithChatCommand(chat_id, ai_response, bot)
                else:
                    return
            else:
                user_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, user_id, bot['botID'])
                to_do_data = Todo.get_to_do_by_chat_user_bot_id(chat_id, user_id, bot['botID'])
                chat_history = user_data['chat_history']    
                to_do = to_do_data['to_do']      

                tel_send_chat_action(chat_id, 'typing', bot['botID'])

                response = get_ai_response_by_pinecone_to_do(message, chat_history, bot, to_do)
                
                ai_response = response['ai_response']
                new_chat_history = response['chat_history']
                UserData.update_chat_history(chat_id, user_id, bot['botID'], new_chat_history)

                handleResponseWithChatCommand(chat_id, ai_response, bot)
        else:
            if group_chat == True:
                is_group_data = UserData.user_data_exists(chat_id, chat_id, bot['botID'])

                if is_group_data == True:
                    group_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
                    chat_history = group_data['chat_history']    

                    tel_send_chat_action(chat_id, 'typing', bot['botID'])
                    
                    response = get_ai_response_by_pinecone(message, chat_history, bot)
                    ai_response = response['ai_response']
                    new_chat_history = response['chat_history']
                    UserData.update_chat_history(chat_id, chat_id, bot['botID'], new_chat_history)
                    
                    handleResponseWithChatCommand(chat_id, ai_response, bot)
                else:
                    return
            else:
                
                user_data = UserData.get_user_data_by_chat_user_bot_id(chat_id, user_id, bot['botID'])
                chat_history = user_data['chat_history']    

                tel_send_chat_action(chat_id, 'typing', bot['botID'])

                response = get_ai_response_by_pinecone(message, chat_history, bot)
                ai_response = response['ai_response']
                new_chat_history = response['chat_history']
                UserData.update_chat_history(chat_id, user_id, bot['botID'], new_chat_history)
                
                handleResponseWithChatCommand(chat_id, ai_response, bot)

        return "success"
    except Exception as e:
        # print stacktrace
        traceback.print_exc()
        return "error"

def extractBotDataFromWebhook(headers):
  botToken = headers['x-telegram-bot-api-secret-token']
  
  # split "--" on botToken
  splitTokens = botToken.split('--')

  if len(splitTokens) < 2:
    return None

  # creator_id is second element
  bot_id = splitTokens[1]

  # get creator data
  bot = Bots.get_bot_by_id(bot_id)

  return bot

# https://telegram.me/MeebleBot?start=taayjus
@router.post("/telegram_message")
async def handle_telegram_message(request: Request) -> str:
    try:
        if not verify_secure_webhook(request.headers):
            return "error"

        bot = extractBotDataFromWebhook(request.headers)

        incoming_data = await request.json()
        parsedTgData = parse_telegram_data(incoming_data)

        print('incoming_data', incoming_data)


        message = parsedTgData["message"]
        message_id = parsedTgData["message_id"]
        user_id = parsedTgData["user_id"]
        group_chat = parsedTgData["group_chat"]

        print('group_chat', group_chat)

        # Handle pre checkout query
        if "pre_checkout_query" in incoming_data:
            return answer_pre_checkout_query(incoming_data)

        # Handle callback
        if "callback_query" in incoming_data:
            return handle_callback(incoming_data, user_id, bot, group_chat)

        chat_id = parsedTgData["chat_id"]

        # # get fields that may not exist
        # try:
        #     telegram_username = incoming_data["message"]["chat"]["username"]
        # except Exception as e:
        #     print("no username")

        if message.startswith("/"):
            handle_command(
                chat_id,
                message,
                incoming_data,
                user_id,
                bot,
                group_chat
            )
            return "success"

        # respond to user message
        handle_user_message(
            incoming_data,
            chat_id,
            message,
            message_id,
            user_id,
            bot,
            group_chat
        )

        return "success"
    except Exception as e:
        print(e)
        return "error"


# https://telegram.me/MeebleBot?start=taayjus
@router.post("/telegram_message/{bot_id}")
async def telegram_message(request: Request):
    resp = await handle_telegram_message(request)
    return resp

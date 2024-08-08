from fastapi import APIRouter, Form, Request
from typing import Union, Optional

import traceback

from messaging.sending import send_message_to_whatsApp

from db.models.wa.users.user import WaUserData
from db.models.todo.todo import Todo
from db.models.wa.bot.bot import WaBots
from db.models.qna.qna import QnAData
from db.models.qna.notion import NotionCRUD

from datetime import datetime
import requests

from ai.ai_api import transcribe_audio
from ai.ai_api import create_chat_message
from ai.langchain import get_ai_response_by_pinecone
from ai.langchain import get_ai_response_by_pinecone, get_ai_response_by_pinecone_to_do, get_to_do, compare_message_chat_history, get_ai_response_qa, get_qna

import os

router = APIRouter(
    prefix="/api/wa_messaging",
    tags=["wa_messaging"],
    # dependencies=[Depends(validate_access_token)],
    # responses={404: {"description": "Not found"}},
)

def handle_command(chat_id, bot_phone_number, user_name, message, from_number, to_number, bot, group_chat=False):
  print('handling command')

  # if start, add chat_id to the user with user_id provided
  if '/start' in message:    
    if bot['botAvatar'] != '':
       send_message_to_whatsApp(from_number, to_number, bot['botName'], bot['botAvatar'])
    else:
      send_message_to_whatsApp(from_number, to_number, bot['botName'])
    
    bot_type = bot['botType']

    if bot_type == 2:
      if group_chat == True:
        is_group_data = WaUserData.user_data_exists(chat_id, chat_id, bot['botID'])

        if is_group_data == True:
            group_data = WaUserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
            chat_history = group_data['chat_history']
            
            if bot["greettingEnable"]:
                send_message_to_whatsApp(from_number, to_number, bot["greetting"])
                chat_history.append(create_chat_message("assistant", bot["greetting"]))
            WaUserData.update_chat_history(chat_id, chat_id, bot['botID'], chat_history)
            
        else:
            chat_history = []
            if bot["greettingEnable"]:
                send_message_to_whatsApp(from_number, to_number, bot["greetting"])
                chat_history.append(create_chat_message("assistant", bot["greetting"]))
            
            chat_title = user_name + "&" + bot['botName']
            WaUserData.save(chat_id, chat_id, chat_title, bot['botID'], chat_history)
            QnAData.save(chat_id, chat_id, bot['botID'])
            NotionCRUD.create(chat_title, chat_id, chat_id, bot['botID'], bot['notionID'])
      else:
        # Check existing user data
        is_user_data = WaUserData.user_data_exists(chat_id, bot_phone_number, bot['botID'])
        
        if is_user_data == True: 
            user_data = WaUserData.get_user_data_by_chat_user_bot_id(chat_id, bot_phone_number, bot['botID'])
            chat_history = user_data['chat_history']
            if bot["greettingEnable"]:
                send_message_to_whatsApp(from_number, to_number, bot["greetting"])
                chat_history.append(create_chat_message("assistant", bot["greetting"]))
            
            WaUserData.update_chat_history(chat_id, bot_phone_number, bot['botID'], chat_history)
        else:     
            chat_history = []
            if bot["greettingEnable"]:
                send_message_to_whatsApp(from_number, to_number, bot["greetting"])
                chat_history.append(create_chat_message("assistant", bot["greetting"]))
            
            chat_title = user_name + "&" + bot['botName']
            
            WaUserData.save(chat_id, bot_phone_number, chat_title, bot['botID'], chat_history)
            QnAData.save(chat_id, bot_phone_number, bot['botID'])
            NotionCRUD.create(chat_title, chat_id, bot_phone_number, bot['botID'], bot['notionID'])

    elif bot_type == 1:
      if group_chat == True:
          is_group_data = WaUserData.user_data_exists(chat_id, chat_id, bot['botID'])

          if is_group_data == True:
              group_data = WaUserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
              chat_history = group_data['chat_history']
              if bot["greettingEnable"]:
                send_message_to_whatsApp(from_number, to_number, bot["greetting"])
                chat_history.append(create_chat_message("assistant", bot["greetting"]))
                  
              WaUserData.update_chat_history(chat_id, chat_id, bot['botID'], chat_history)
          else:
              chat_history = []
              if bot["greettingEnable"]:
                send_message_to_whatsApp(from_number, to_number, bot["greetting"])
                chat_history.append(create_chat_message("assistant", bot["greetting"]))
              
              chat_title = user_name + "&" + bot['botName']
              WaUserData.save(chat_id, chat_id, chat_title, bot['botID'], chat_history)
              Todo.save(chat_id, chat_id, bot['botID'])
      else:
          # Check existing user data
          is_user_data = WaUserData.user_data_exists(chat_id, bot_phone_number, bot['botID'])
          
          if is_user_data == True: 
              user_data = WaUserData.get_user_data_by_chat_user_bot_id(chat_id, bot_phone_number, bot['botID'])
              chat_history = user_data['chat_history']
              if bot["greettingEnable"]:
                send_message_to_whatsApp(from_number, to_number, bot["greetting"])
                chat_history.append(create_chat_message("assistant", bot["greetting"]))
              
              WaUserData.update_chat_history(chat_id, bot_phone_number, bot['botID'], chat_history)
          else:     
              chat_history = []
              if bot["greettingEnable"]:
                send_message_to_whatsApp(from_number, to_number, bot["greetting"])
                chat_history.append(create_chat_message("assistant", bot["greetting"]))
              
              chat_title = user_name + "&" + bot['botName']
              WaUserData.save(chat_id, bot_phone_number, chat_title, bot['botID'], chat_history)
              Todo.save(chat_id, chat_id, bot['botID'])
    else:
      if group_chat == True:
        is_group_data = WaUserData.user_data_exists(chat_id, chat_id, bot['botID'])

        if is_group_data == True:
            group_data = WaUserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
            chat_history = group_data['chat_history']
            if bot["greettingEnable"]:
                send_message_to_whatsApp(from_number, to_number, bot["greetting"])
                chat_history.append(create_chat_message("assistant", bot["greetting"]))
            WaUserData.update_chat_history(chat_id, chat_id, bot['botID'], chat_history)
        else:
            chat_history = []
            if bot["greettingEnable"]:
                send_message_to_whatsApp(from_number, to_number, bot["greetting"])
                chat_history.append(create_chat_message("assistant", bot["greetting"]))
            
            chat_title = user_name + "&" + bot['botName']
            WaUserData.save(chat_id, chat_id, chat_title, bot['botID'], chat_history)
      else:
        # Check existing user data
        is_user_data = WaUserData.user_data_exists(chat_id, bot_phone_number, bot['botID'])
        
        if is_user_data == True: 
            user_data = WaUserData.get_user_data_by_chat_user_bot_id(chat_id, bot_phone_number, bot['botID'])
            chat_history = user_data['chat_history']
            if bot["greettingEnable"]:
                send_message_to_whatsApp(from_number, to_number, bot["greetting"])
                chat_history.append(create_chat_message("assistant", bot["greetting"]))
            
            WaUserData.update_chat_history(chat_id, bot_phone_number, bot['botID'], chat_history)
        else:     
            chat_history = []
            if bot["greettingEnable"]:
                send_message_to_whatsApp(from_number, to_number, bot["greetting"])
                chat_history.append(create_chat_message("assistant", bot["greetting"]))
            
            chat_title = user_name + "&" + bot['botName']
            WaUserData.save(chat_id, bot_phone_number, chat_title, bot['botID'], chat_history)
    return 
  elif '/purchase' in message:
    pass
    return 
  elif '/balance' in message:
    send_message_to_whatsApp(from_number, to_number, f'Your balance is {"balance"}')
    return 
  elif '/help' in message:
    send_message_to_whatsApp(from_number, to_number, 'Need help with something? Send us a message @BeemoHelp')
    return 

async def handle_user_message(chat_id, bot_phone_number, message, from_number, to_number, bot, group_chat=False):
  # print current time milis
  print("\n**********CURRENT TIME**********\n", message)
  print(datetime.now().timestamp())

  try:
    bot_type = bot['botType']

    if bot_type == 2:
      if group_chat == True:
          is_group_data = WaUserData.user_data_exists(chat_id, chat_id, bot['botID'])
          if is_group_data == True:
              group_data = WaUserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
              chat_history = group_data['chat_history']    
              summary = group_data['summary']
              history_cursor = group_data['history_cursor']

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
              WaUserData.update_chat_history(chat_id, chat_id, bot['botID'], new_chat_history, new_summary, new_history_cursor)

              send_message_to_whatsApp(from_number, to_number, ai_response)
          else: 
              send_message_to_whatsApp(from_number, to_number, "Please start conversation with '/start' chat command.")
      else:
          # Check existing user data
          is_user_data = WaUserData.user_data_exists(chat_id, bot_phone_number, bot['botID'])
          
          if is_user_data == True: 
              user_data = WaUserData.get_user_data_by_chat_user_bot_id(chat_id, bot_phone_number, bot['botID'])
              chat_history = user_data['chat_history']    
              summary = user_data['summary']
              history_cursor = user_data['history_cursor']

              # is_repeat_request = compare_message_chat_history(message, chat_history)
              # if is_repeat_request:
              #     return 'success'
              response_qa = get_qna(message, chat_history, bot, summary, history_cursor)
              if response_qa != None:
                  print('response_qa-1:', response_qa, bot_phone_number)
                  QnAData.update_qna(chat_id, bot_phone_number, bot['botID'], bot['notionID'], response_qa)
              
              response = get_ai_response_qa(message, chat_history, bot, summary, history_cursor)
              ai_response = response['ai_response']
              new_chat_history = response['chat_history']
              new_summary = response['summary']
              new_history_cursor = response['history_cursor']
              WaUserData.update_chat_history(chat_id, bot_phone_number, bot['botID'], new_chat_history, new_summary, new_history_cursor)

              send_message_to_whatsApp(from_number, to_number, ai_response)
          else:     
              send_message_to_whatsApp(from_number, to_number, "Please start conversation with '/start' chat command.")

    elif bot_type == 1:
      if group_chat == True:
          is_group_data = WaUserData.user_data_exists(chat_id, chat_id, bot['botID'])
          is_to_do = Todo.to_do_exists(chat_id, chat_id, bot['botID'])

          if is_group_data == True and is_to_do == True:
              group_data = WaUserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
              group_to_do_data = Todo.get_to_do_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
              chat_history = group_data['chat_history']    
              to_do = group_to_do_data['to_do']      

              is_repeat_request = compare_message_chat_history(message, chat_history)
              if is_repeat_request:
                  return 'success'
              
              response = get_to_do(message, chat_history, bot, to_do)
              ai_response = response['ai_response']
              new_chat_history = response['chat_history']
              WaUserData.update_chat_history(chat_id, chat_id, bot['botID'], new_chat_history)

              Todo.update_to_do(chat_id, chat_id, bot['botID'], response['to_do_data'])

              send_message_to_whatsApp(from_number, to_number, ai_response)
          else: 
              send_message_to_whatsApp(from_number, to_number, "Please start conversation with '/start' chat command.")
      else:
          # Check existing user data
          is_user_data = WaUserData.user_data_exists(chat_id, bot_phone_number, bot['botID'])
          is_to_do = Todo.to_do_exists(chat_id, bot_phone_number, bot['botID'])
          
          if is_user_data == True and is_to_do == True: 
              user_data = WaUserData.get_user_data_by_chat_user_bot_id(chat_id, bot_phone_number, bot['botID'])
              to_do_data = Todo.get_to_do_by_chat_user_bot_id(chat_id, bot_phone_number, bot['botID'])
              chat_history = user_data['chat_history']    
              to_do = to_do_data['to_do']      

              is_repeat_request = compare_message_chat_history(message, chat_history)

              if is_repeat_request:
                  return 'success'
              response = get_to_do(message, chat_history,  bot, to_do)  

              ai_response = response['ai_response']
              new_chat_history = response['chat_history']
              WaUserData.update_chat_history(chat_id, bot_phone_number, bot['botID'], new_chat_history)

              Todo.update_to_do(chat_id, bot_phone_number, bot['botID'], response['to_do_data'])

              send_message_to_whatsApp(from_number, to_number, ai_response)
          else:     
              send_message_to_whatsApp(from_number, to_number, "Please start conversation with '/start' chat command.")
    else:
      if group_chat == True:
          is_group_data = WaUserData.user_data_exists(chat_id, chat_id, bot['botID'])
          if is_group_data == True:
              group_data = WaUserData.get_user_data_by_chat_user_bot_id(chat_id, chat_id, bot['botID'])
              chat_history = group_data['chat_history']    
              summary = group_data['summary']
              history_cursor = group_data['history_cursor']
              
              response = get_ai_response_by_pinecone(message, chat_history, bot, summary, history_cursor)
              ai_response = response['ai_response']
              new_chat_history = response['chat_history']
              new_summary = response['summary']
              new_history_cursor = response['history_cursor']
              WaUserData.update_chat_history(chat_id, chat_id, bot['botID'], new_chat_history, new_summary, new_history_cursor)

              send_message_to_whatsApp(from_number, to_number, ai_response)
          else: 
            send_message_to_whatsApp(from_number, to_number, "Please start conversation with '/start' chat command.")
      else:
          # Check existing user data
          is_user_data = WaUserData.user_data_exists(chat_id, bot_phone_number, bot['botID'])
          
          if is_user_data == True: 
              user_data = WaUserData.get_user_data_by_chat_user_bot_id(chat_id, bot_phone_number, bot['botID'])
              chat_history = user_data['chat_history']    
              summary = user_data['summary']
              history_cursor = user_data['history_cursor']

              response = get_ai_response_by_pinecone(message, chat_history, bot, summary, history_cursor)
              ai_response = response['ai_response']
              new_chat_history = response['chat_history']
              new_summary = response['summary']
              new_history_cursor = response['history_cursor']
              WaUserData.update_chat_history(chat_id, bot_phone_number, bot['botID'], new_chat_history, new_summary, new_history_cursor)

              send_message_to_whatsApp(from_number, to_number, ai_response)
          else:     
              send_message_to_whatsApp(from_number, to_number, "Please start conversation with '/start' chat command.")
    
  except Exception as e:
    traceback.print_exc()
    print('ERROR')

@router.post("/whatsapp_message")
async def handle_whatsapp(request: Request, From: str = Form(), To: str = Form(), WaId: str = Form(), ProfileName: Optional[str]  = Form(''), Body: Optional[str]  = Form(''), sageSid: Optional[str] = Form(None), NumMedia: Optional[int] = Form(0), MediaUrl: Optional[str] = Form(None), MediaContentType: Optional[str] = Form(None)) -> str:
  try:
    form_data = await request.form()
    user_name = ProfileName
    bot_phone_number = To.split('+')[1]
    bot = WaBots.get_bot_by_phone_number(bot_phone_number)
    from_number = From
    to_number = To
    chat_id = WaId
    message = Body

    # if chat_id begins with +, remove it
    if chat_id.startswith('+'):
      chat_id = chat_id[1:]

    print('chat_id', chat_id)
    
    if (message.startswith('/')):
      handle_command(chat_id, bot_phone_number, user_name, message, from_number, to_number, bot)
      return "success"
    
    # respond to user message
    await handle_user_message(chat_id, bot_phone_number, message, from_number, to_number, bot)

    return "success"
  except Exception as e:
    print(e)
    return "error" 

# on server cleanup
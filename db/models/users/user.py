import boto3
from boto3.dynamodb.conditions import Attr
from db.dynamodb import tg_user_data_table
from datetime import datetime
from utils.generate_id import generate_id



class UserData:
    def __init__(self):
        pass
        
    # Create User
    @staticmethod
    def save(chat_id: str, user_id: str, chat_title: str, bot_id: str, chat_history: list):
        new_user = {
            'id': generate_id(20),
            'chat_id': chat_id,
            'user_id': user_id,
            'chat_title': chat_title,
            'bot_id': bot_id,
            'chat_history': chat_history,
            'summary': '',
            'history_cursor': 0,
            'created_at': str(datetime.utcnow()),
            'updated_at': str(datetime.utcnow()),

        }
        tg_user_data_table.put_item(Item=new_user)
        return {"status": "User created successfully"}

    # if user data exist, return value is true, otherwise false
    @staticmethod
    def user_data_exists(chat_id: str, user_id: str, bot_id: str):
        response = tg_user_data_table.scan(
            FilterExpression=Attr('chat_id').eq(chat_id) & Attr('user_id').eq(user_id) & Attr('bot_id').eq(bot_id)
        )
        items = response['Items']
        if items:
            return True
        else:
            return False

    # Get active user's data
    def get_user_data_by_chat_user_bot_id(chat_id: str, user_id: str, bot_id:str):
        response = tg_user_data_table.scan(
            FilterExpression=(Attr('chat_id').eq(chat_id) & Attr('user_id').eq(user_id) & Attr('bot_id').eq(bot_id))
        )
        items = response['Items']
        
        if not items:
            return None

        # Assuming that user_id and active combination is unique and only returns one item
        return items[0]

    def update_chat_history(chat_id: str, user_id: str, bot_id: str, chat_history: list, summary: str = '', history_cursor: int = 0):
    # Step 1: Scan the table to find the item
        response = tg_user_data_table.scan(
            FilterExpression=(Attr('chat_id').eq(chat_id) & Attr('user_id').eq(user_id) & Attr('bot_id').eq(bot_id))
        )
        items = response['Items']

        if not items:
            return {"status": "No matching user found"}

        # Assuming that user_id and bot_id combination is unique and only returns one item
        item = items[0]

        # Step 2: Update the 'active' field of the item
        tg_user_data_table.update_item(
            Key={'id': item['id']},
            UpdateExpression="set chat_history = :chat, summary = :sum, history_cursor = :hcur, updated_at = :updated_at",
            ExpressionAttributeValues={
                ':chat': chat_history,
                ':sum' : summary,
                ':hcur': history_cursor,
                ':updated_at': str(datetime.utcnow())
            },
            ReturnValues="UPDATED_NEW"
        )
        return {"status": "Active field updated successfully for the matching user"}

    def update_chat_title(chat_id: str, user_id: str, bot_id: str, chat_title: str = ''):
        # Step 1: Scan the table to find the item
        response = tg_user_data_table.scan(
            FilterExpression=(Attr('chat_id').eq(chat_id) & Attr('user_id').eq(user_id) & Attr('bot_id').eq(bot_id))
        )
        items = response['Items']

        if not items:
            return {"status": "No matching user found"}

        # Assuming that user_id and bot_id combination is unique and only returns one item
        item = items[0]

        # Step 2: Update the 'active' field of the item
        tg_user_data_table.update_item(
            Key={'id': item['id']},
            UpdateExpression="set chat_title = :chat, updated_at = :updated_at",
            ExpressionAttributeValues={
                ':chat': chat_title,
                ':updated_at': str(datetime.utcnow())
            },
            ReturnValues="UPDATED_NEW"
        )
        return {"status": "Active field updated successfully for the matching user"}


    

  

import boto3
from boto3.dynamodb.conditions import Attr
from db.dynamodb import tg_qna_list_table
from datetime import datetime
from utils.generate_id import generate_id
from db.models.qna.notion import NotionCRUD

class QnAData:
    def __init__(self):
        pass
        
    # Create to-do list
    @staticmethod
    def save(chat_id: str, user_id: str, bot_id: str, qna: list = []):
        new_user = {
            'id': generate_id(20),
            'chat_id': chat_id,
            'user_id': user_id,
            'bot_id': bot_id,
            'qna': qna,
            'created_at': str(datetime.utcnow()),
            'updated_at': str(datetime.utcnow()),
        }
        tg_qna_list_table.put_item(Item=new_user)
        return {"status": "User created successfully"}

    # if user data exist, return value is true, otherwise false
    @staticmethod
    def qna_exists(chat_id: str, user_id: str, bot_id: str):
        response = tg_qna_list_table.scan(
            FilterExpression=Attr('chat_id').eq(chat_id) & Attr('user_id').eq(user_id) & Attr('bot_id').eq(bot_id)
        )
        items = response['Items']
        if items:
            return True
        else:
            return False

    # Get active user's data
    def get_qna_by_chat_user_bot_id(chat_id: str, user_id: str, bot_id:str):
        response = tg_qna_list_table.scan(
            FilterExpression=(Attr('chat_id').eq(chat_id) & Attr('user_id').eq(user_id) & Attr('bot_id').eq(bot_id))
        )
        items = response['Items']
        
        if not items:
            return None

        # Assuming that user_id and active combination is unique and only returns one item
        return items[0]

    def update_qna(chat_id: str, user_id: str, bot_id: str, notion_id: str, qna: dict = {}):
    # Step 1: Scan the table to find the item
        response = tg_qna_list_table.scan(
            FilterExpression=(Attr('chat_id').eq(chat_id) & Attr('user_id').eq(user_id) & Attr('bot_id').eq(bot_id))
        )
        items = response['Items']

        if not items:
            return {"status": "No matching user found"}

        # Assuming that user_id and bot_id combination is unique and only returns one item
        item = items[0]
        print('items', item)
        update_qna = []
        if item['qna'] != None:
            update_qna = item['qna']

        dupulicated_flag = False
        for q in update_qna:
            if q['question'] == qna['question']:
                dupulicated_flag = True
                q['answer'] = qna['answer']
        
        if dupulicated_flag == False:
            update_qna.append(qna)

        converted_qna = NotionCRUD.convert_qna_to_str(update_qna)
        NotionCRUD.update(chat_id, user_id, bot_id, notion_id, converted_qna)

        # Step 2: Update the 'active' field of the item
        tg_qna_list_table.update_item(
            Key={'id': item['id']},
            UpdateExpression="set qna = :qna, updated_at = :updated_at",
            ExpressionAttributeValues={
                ':qna': update_qna,
                ':updated_at': str(datetime.utcnow())
            },
            ReturnValues="UPDATED_NEW"
        )
        return {"status": "Active field updated successfully for the matching user"}


    

  

import os
from datetime import datetime
from utils.generate_id import generate_id
from datetime import datetime

from notion_client import Client

# Initialize Notion client
token = os.getenv("NOTION_TOKEN")

client = Client(auth=token)

class NotionCRUD:

    @staticmethod
    def create(chat_title:str, chat_id: str, user_id: str, bot_id: str, notion_id: str, qna: list = []):
        # Create a new page in the database
        new_page = client.pages.create(
            parent={"database_id": notion_id},
            properties={
                "Chat Title": {"title": [{"text": {"content": chat_title}}]},
                "Chat ID": {"rich_text": [{"text": {"content": str(chat_id)}}]},
                "User ID": {"rich_text": [{"text": {"content": str(user_id)}}]},
                "Bot ID": {"rich_text": [{"text": {"content": str(bot_id)}}]},
                "QnA": {"rich_text": [{"text": {"content": str(qna)}}]},
                "Created At": {"date": {"start": datetime.utcnow().isoformat()}},
                "Updated At": {"date": {"start": datetime.utcnow().isoformat()}}
            },
        )
        return new_page['id']

    @staticmethod
    def read(chat_id: str, user_id: str, bot_id: str, notion_id: str):
        # Query the database
        response = client.databases.query(database_id=notion_id)

        # Search for the page with the given chat_id, user_id and bot_id
        for page in response['results']:
            if (page['properties']['Chat ID']['rich_text'][0]['text']['content'] == str(chat_id) and
                page['properties']['User ID']['rich_text'][0]['text']['content'] == str(user_id) and
                page['properties']['Bot ID']['rich_text'][0]['text']['content'] == str(bot_id)):
                return page
        return None

    @staticmethod
    def update(chat_id: str, user_id: str, bot_id: str, notion_id: str, new_qna: list):
        # Get the page_id of the page with the given chat_id, user_id, and bot_id
        print('chat_id', chat_id, user_id, bot_id, notion_id)
        page_id = NotionCRUD.get_page_id(chat_id, user_id, bot_id, notion_id)

        if page_id is None:
            print("No page found with the given chat_id, user_id, and bot_id.")
            return None

        # Update the QnA property of the page
        updated_page = client.pages.update(
            page_id=page_id, 
            properties={
                "QnA": {"rich_text": [{"text": {"content": str(new_qna)}}]},
                "Updated At": {"date": {"start": datetime.utcnow().isoformat()}}
            },
        )
        return updated_page

    @staticmethod
    def delete(page_id: str):
        # Currently, the Notion API does not support deleting pages.
        pass

    @staticmethod
    def get_page_id(chat_id: str, user_id: str, bot_id: str, notion_id: str):
        # Query the database
        response = client.databases.query(database_id=notion_id)

        # Search for the page with the given chat_id, user_id and bot_id
        for page in response['results']:
            if (page['properties']['Chat ID']['rich_text'][0]['text']['content'] == str(chat_id) and
                page['properties']['User ID']['rich_text'][0]['text']['content'] == str(user_id) and
                page['properties']['Bot ID']['rich_text'][0]['text']['content'] == str(bot_id)):
                return page['id']
        return None

    @staticmethod
    def convert_qna_to_str(qna: list):
        result = ''
        for item in qna:
            result += "- " + item['question'] + '\n' + "  " + item['answer'] + '\n'

        return result

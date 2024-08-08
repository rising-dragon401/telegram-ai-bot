import boto3
from boto3.dynamodb.conditions import Attr
from db.dynamodb import wa_bot_table


class WaBots:
    def __init__(self):
        pass
  
    @staticmethod
    def create_item(item: dict):
        wa_bot_table.put_item(Item=item)
        return {"status": "Item created successfully"}

    # Read  
    @staticmethod
    def get_bot_by_id(item_id: str):
        response = wa_bot_table.get_item(Key={'botID': item_id})
        item = response['Item']
        return item
    
    # Get Bot by phone number
    def get_bot_by_phone_number(phone_number: str):
        response = wa_bot_table.scan(
            FilterExpression=(Attr('phoneNumber').eq(phone_number))
        )
        items = response['Items']

        if not items:
            return {"status": "No matching user found"}

        # Assuming that user_id and bot_id combination is unique and only returns one item
        item = items[0]

        return item

    # Update
    @staticmethod
    def update_item(item_id: str, item: dict):
        wa_bot_table.update_item(
            Key={'id': item_id},
            UpdateExpression="set info=:i",
            ExpressionAttributeValues={':i': item},
            ReturnValues="UPDATED_NEW"
        )
        return {"status": "Item updated successfully"}

    # Delete
    @staticmethod
    def delete_item(item_id: str):
        wa_bot_table.delete_item(Key={'id': item_id})
        return {"status": "Item deleted successfully"}

    # Get all Bots
    @staticmethod
    def get_all_items():
        response = wa_bot_table.scan()
        items = response['Items']
        return items


  

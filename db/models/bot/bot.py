from db.dynamodb import tg_bot_table

class Bots:
    def __init__(self):
        pass
  
    @staticmethod
    def create_item(item: dict):
        tg_bot_table.put_item(Item=item)
        return {"status": "Item created successfully"}

    # Read  
    @staticmethod
    def get_bot_by_id(item_id: str):
        response = tg_bot_table.get_item(Key={'botID': item_id})
        item = response['Item']
        return item

    # Update
    @staticmethod
    def update_item(item_id: str, item: dict):
        tg_bot_table.update_item(
            Key={'id': item_id},
            UpdateExpression="set info=:i",
            ExpressionAttributeValues={':i': item},
            ReturnValues="UPDATED_NEW"
        )
        return {"status": "Item updated successfully"}

    # Delete
    @staticmethod
    def delete_item(item_id: str):
        tg_bot_table.delete_item(Key={'id': item_id})
        return {"status": "Item deleted successfully"}

    # Get all Bots
    @staticmethod
    def get_all_items():
        response = tg_bot_table.scan()
        items = response['Items']
        return items


  

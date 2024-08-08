import boto3

dynamodb = boto3.resource('dynamodb', region_name='ca-central-1')

tg_bot_table = dynamodb.Table('tgbot')
tg_user_data_table = dynamodb.Table('tg_user_data')
tg_active_data_table = dynamodb.Table('tg_active_data')
tg_to_do_list_table = dynamodb.Table('tg_to_do_list')
tg_qna_list_table = dynamodb.Table('tg_qna_list')
wa_user_data_table = dynamodb.Table('wa_user_data')
wa_bot_table = dynamodb.Table('wa_bot')
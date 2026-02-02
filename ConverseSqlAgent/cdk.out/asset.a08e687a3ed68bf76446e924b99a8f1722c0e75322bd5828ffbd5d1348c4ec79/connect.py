import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['CONNECTIONS_TABLE'])

def handler(event, context):
    print("Connecting to websocket!")
    connection_id = event['requestContext']['connectionId']
    
    # Store connection in DynamoDB
    table.put_item(Item={'connectionId': connection_id})
    
    return {
        'statusCode': 200,
        'body': json.dumps('Connected')
    }
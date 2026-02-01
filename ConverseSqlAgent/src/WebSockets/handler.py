import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['CONNECTIONS_TABLE'])

def handler(event, context):
    # Handle incoming messages and broadcast to other connections
    connection_id = event['requestContext']['connectionId']
    domain_name = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    
    # Get message from request body
    body = json.loads(event.get('body', '{}'))
    message = body.get('message', '')
    
    # Get all connections from DynamoDB
    response = table.scan()
    connections = response['Items']
    
    # Send message to all connected clients
    api_gateway_management = boto3.client(
        'apigatewaymanagementapi',
        endpoint_url=f'https://{domain_name}/{stage}'
    )
    
    for connection in connections:
        try:
            api_gateway_management.post_to_connection(
                ConnectionId=connection['connectionId'],
                Data=json.dumps({'message': message})
            )
        except Exception as e:
            # Connection might be stale, remove it
            table.delete_item(Key={'connectionId': connection['connectionId']})
    
    return {
        'statusCode': 200,
        'body': json.dumps('Message sent')
    }
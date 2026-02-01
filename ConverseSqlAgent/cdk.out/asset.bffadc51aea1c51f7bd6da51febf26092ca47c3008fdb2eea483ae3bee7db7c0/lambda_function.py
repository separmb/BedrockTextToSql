import os
import json
import boto3

from agent import BaseAgent

from tool_groups.sql import SQL_TOOL_GROUP
from tool_groups.memory import MEMORY_TOOL_GROUP

memory_table_name = os.environ.get('DynamoDbMemoryTable', 'advtext2sql_memory_tb')
model_id = os.environ.get('BedrockModelId', 'us.anthropic.claude-sonnet-4-20250514-v1:0')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['CONNECTIONS_TABLE'])

def lambda_handler(event, context):
    print(event)

    # Handle incoming messages and broadcast to other connections
    connection_id = event['requestContext']['connectionId']
    domain_name = event['requestContext']['domainName']
    stage = event['requestContext']['stage']

    # Extract information from the event
    http_method = event.get('httpMethod')
    path = event.get('path')
    headers = event.get('headers', {})
    query_params = event.get('queryStringParameters', {})
    
    # Parse the body (API Gateway passes body as string)
    body = None
    if event.get('body'):
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            body = event['body']  # Keep as string if not valid JSON
    
    input_text = body["prompt"]
    
    # Initialize SQL agent
    print("Initializing agent")
    agent = BaseAgent(model_id=model_id, memory_table_name=memory_table_name)
    agent.add_tool_group(SQL_TOOL_GROUP)
    agent.add_tool_group(MEMORY_TOOL_GROUP)
    
    print("Invoking agent")
    response = agent.invoke_agent(input_text)
    
    print("Completed agent execution")
    print(response)

    cors_headers = {
        "Access-Control-Allow-Origin": "*",  # Allow all origins; change to specific domain for security
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    }

    return_string = '{"sql": "' + response + '"}'

    response_json = {
        "sql": response
    }
  
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
                Data=json.dumps(response_json)
            )
        except Exception as e:
            # Connection might be stale, remove it
            table.delete_item(Key={'connectionId': connection['connectionId']})
    
    return {
        "statusCode": 200,
        "body": json.dumps(response_json),
        "headers": cors_headers
    }



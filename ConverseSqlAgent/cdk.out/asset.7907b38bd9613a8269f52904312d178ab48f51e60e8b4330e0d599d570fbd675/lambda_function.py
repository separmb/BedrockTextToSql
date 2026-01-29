import os
import json

from agent import BaseAgent

from tool_groups.sql import SQL_TOOL_GROUP
from tool_groups.memory import MEMORY_TOOL_GROUP

memory_table_name = os.environ.get('DynamoDbMemoryTable', 'advtext2sql_memory_tb')
model_id = os.environ.get('BedrockModelId', 'us.anthropic.claude-sonnet-4-20250514-v1:0')

def lambda_handler(event, context):
    print(event)

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
    
    input_text = body["input_text"]
    
    # Initialize SQL agent
    print("Initializing agent")
    agent = BaseAgent(model_id=model_id, memory_table_name=memory_table_name)
    agent.add_tool_group(SQL_TOOL_GROUP)
    agent.add_tool_group(MEMORY_TOOL_GROUP)
    
    print("Invoking agent")
    response = agent.invoke_agent(input_text)
    
    print("Completed agent execution")
    print(response)
    
    return {
        "statusCode": 200,
        "body": response
    }
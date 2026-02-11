import boto3
import botocore.auth
import botocore.awsrequest
import botocore.credentials
import datetime
import urllib.parse

def generate_signed_websocket_url(api_id, stage, region, expires_in=36000):
    """
    Generate a SigV4 signed WebSocket URL for API Gateway.
    """
    # Get AWS credentials from environment or IAM role
    session = boto3.Session()
    credentials = session.get_credentials().get_frozen_credentials()

    # Build the WebSocket endpoint
    endpoint = f"wss://{api_id}.execute-api.{region}.amazonaws.com/{stage}"

    # Create AWS request
    request = botocore.awsrequest.AWSRequest(
        method='GET',
        url=endpoint,
        headers={'host': f"{api_id}.execute-api.{region}.amazonaws.com"}
    )

    # Sign the request
    signer = botocore.auth.SigV4QueryAuth(
        credentials,
        "execute-api",
        region,
        expires=expires_in
    )
    signer.add_auth(request)

    # Return the signed URL
    return request.url

if __name__ == "__main__":
    # wss://wei9prw2f2.execute-api.us-east-1.amazonaws.com/dev/
    api_id = "wei9prw2f2"       # Your API Gateway WebSocket API ID
    stage = "dev"           # Stage name
    region = "us-east-1"    # AWS region

    signed_url = generate_signed_websocket_url(api_id, stage, region)
    print("Signed WebSocket URL:")
    print(signed_url)

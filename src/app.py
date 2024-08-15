import json
from datetime import datetime

import boto3
import os
from passageidentity import Passage, PassageError

# Initialize DynamoDB resource and table
dynamodb = boto3.resource('dynamodb', endpoint_url='http://dynamodb-local:8000')
table = dynamodb.Table(os.getenv('SESSIONS_TABLE', 'Sessions'))

# Initialize Passage for user authentication
passage = Passage(app_id='961JRDH4c4Sin8LYGGbI0Lb7', api_key='hIhBwnzQ12.COxGNaiI03RxEtl0vrkVEuTZtOjhimmowhfmhbic26usN3zHc7p92Pb2M5dPAcoQ')


def lambda_handler(event, context):
    print("hi")
    try:
        print("hi2")
        # Check if 'headers' and 'Authorization' are present in the event
        if 'headers' not in event or 'Authorization' not in event['headers']:
            return {
                'statusCode': 400,
                'body': json.dumps("Missing 'Authorization' header")
            }

        print("hi3")
        # Extract the JWT token from the 'Authorization' header
        token = event['headers'].get('Authorization').split(' ')[1]

        # Authenticate the token using Passage
        user_info = passage.getUser(token)

        # Accessing user information using dot notation
        email = user_info.email

        # Return the authenticated user's information for further processing
        return process_request(event, email)

    except PassageError as e:
        # Handle authentication failures
        return {
            'statusCode': 401,
            'body': json.dumps({"error": f"Authentication failed: {str(e)}"})
        }
    except Exception as e:
        # Handle general errors
        return {
            'statusCode': 500,
            'body': json.dumps({"error": f"Internal server error: {str(e)}"})
        }


def process_request(event, email):
    # This function should handle the processing of the request
    # after the user has been authenticated.

    # For example, you can check the HTTP method and route the request
    # to the appropriate handler (e.g., /report or /leaderboard).

    http_method = event['httpMethod']
    path = event['path']

    if http_method == 'POST' and path == '/report':
        return handle_report(event, email)

    elif http_method == 'GET' and path == '/leaderboard':
        return handle_leaderboard()

    else:
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid request')
        }


def handle_report(event, email):
    body = json.loads(event['body'])

    sessionid = body.get('sessionid')
    start = body.get('start')
    end = body.get('end')

    if start:
        # Convert start time to epoch time with 2 decimal places
        start_timestamp = round(datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ").timestamp(), 2)
        table.update_item(
            Key={'sessionid': sessionid},
            UpdateExpression="SET #s = :s, email = :e",
            ExpressionAttributeNames={"#s": "start"},
            ExpressionAttributeValues={":s": start_timestamp, ":e": email}
        )

    if end:
        # Convert end time to epoch time with 2 decimal places
        end_timestamp = round(datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ").timestamp(), 2)
        table.update_item(
            Key={'sessionid': sessionid},
            UpdateExpression="SET #e = :e",
            ExpressionAttributeNames={"#e": "end"},
            ExpressionAttributeValues={":e": end_timestamp}
        )

    return {
        'statusCode': 200,
        'body': json.dumps('Session data recorded successfully!')
    }


def handle_leaderboard():
    # Implement the logic to handle the /leaderboard request here
    pass

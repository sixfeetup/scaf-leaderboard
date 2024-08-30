import boto3
import json
import os
from datetime import datetime
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


def report(event: dict, context: LambdaContext) -> dict:
    """ Report timings """
    logger.info("Lambda function invoked", extra={"event": event})

    body = json.loads(event.get('body'))
    sessionid = body.get('sessionid')
    start = body.get('start')
    end = body.get('end')
    user_email = event.get("requestContext").get("authorizer").get("email")
    user_name = event.get("requestContext").get("authorizer").get("name")

    # Initialize DynamoDB resource and table
    endpoint_url = os.getenv('DYNAMODB_ENDPOINT')
    dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    table = dynamodb.Table(os.getenv('SESSIONS_TABLE', 'Sessions'))

    if start:
        start_timestamp = parse_datetime(start)
        table.update_item(
            Key={'sessionid': sessionid},
            UpdateExpression="SET #s = :s, email = :e, user_name = :u",
            ExpressionAttributeNames={"#s": "start"},
            ExpressionAttributeValues={
                ":s": start_timestamp,
                ":e": user_email,
                ":u": user_name
            }
        )

    if end:
        end_timestamp = parse_datetime(end)
        table.update_item(
            Key={'sessionid': sessionid},
            UpdateExpression="SET #e = :e",
            ExpressionAttributeNames={"#e": "end"},
            ExpressionAttributeValues={":e": end_timestamp}
        )

    logger.info("Lambda function completed successfully")

    return {"statusCode": 200, "body": "Session data recorded successfully!"}


def leaderboard(event: dict, context: LambdaContext) -> dict:
    """ Get Leaderboard Stats """
    # Initialize DynamoDB resource and table
    endpoint_url = os.getenv('DYNAMODB_ENDPOINT')
    dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    table = dynamodb.Table(os.getenv('SESSIONS_TABLE', 'Sessions'))

    try:
        # Scan DynamoDB table to get all items
        response = table.scan()
        items = response.get('Items', [])

        # Calculate duration for each item
        results = {}
        for item in items:
            email = item.get('email')
            user_name = item.get('user_name')
            start = item.get('start')
            end = item.get('end')
            if start and end:
                duration = end - start
                # Store the shortest duration for each email
                if email not in results or duration < results[email]:
                    results[email] = duration

        # Convert results to list and sort by duration (shortest to longest)
        sorted_results = sorted(
            [{'name': email, 'user_name': user_name, 'duration': duration} for email, user_name, duration in results.items()],
            key=lambda x: x['duration']
        )

        return {"statusCode": 200, "body": json.dumps(sorted_results)}

    except Exception as e:
        return {"statusCode": 500, 'body': f"Internal server error: {str(e)}"}


def parse_datetime(dt_str):
    """ Parse datetime string with or without milliseconds. """
    try:
        return int(datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp())
    except ValueError:
        return int(datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ").timestamp())

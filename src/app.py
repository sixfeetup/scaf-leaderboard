import time
from decimal import Decimal

import boto3
import json
import os
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from boto3.dynamodb.conditions import Key

logger = Logger()


def validate_time(timestamp_str):
    try:
        # Convert the timestamp string to a float
        timestamp = float(timestamp_str)

        # Get the current time
        current_time = time.time()

        # Calculate the difference in seconds
        time_difference = current_time - timestamp

        # Check if the difference is within 5 minutes (300 seconds)
        return 0 <= time_difference <= 300
    except ValueError:
        # Return False if the input can't be converted to a float
        return False


def report(event: dict, context: LambdaContext) -> dict:
    """ Report timings """
    logger.debug("Lambda function invoked", extra={"event": event})

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
        if not validate_time(start):
            return {"statusCode": 500, "body": json.dumps({"error": "Invalid start time"})}
        table.put_item(
            Item={
                'user_name': user_name,
                'sessionid': sessionid,
                'email': user_email,
                'start': start,
                'status': 'IN_PROGRESS',
            }
        )

    if end:
        if not validate_time(end):
            return {"statusCode": 500, "body": json.dumps({"error": "Invalid end time"})}
        response = table.get_item(
            Key={
                'user_name': user_name,
                'sessionid': sessionid
            },
            ProjectionExpression='#start_time',  # Use an expression attribute name
            ExpressionAttributeNames={
                '#start_time': 'start'  # Map the expression attribute name to the actual attribute name
            }
        )
        if 'Item' in response:
            start = response['Item'].get('start')
        else:
            print(f"No session found for user {user_name} with sessionid {sessionid}")
            return {"statusCode": 500, "body": json.dumps({"error": "No session found"})}

        duration = Decimal(end) - Decimal(start)
        table.update_item(
            Key={'user_name': user_name, 'sessionid': sessionid},
            UpdateExpression="SET #end = :end, #duration = :duration, #status = :status",
            ExpressionAttributeNames={
                '#end': 'end',
                '#duration': 'duration',
                '#status': 'status'
                },
            ExpressionAttributeValues={
                ':end': end,
                ':duration': duration,
                ':status': 'COMPLETED'
                },
        )

    logger.debug("Lambda function completed successfully")

    return {"statusCode": 200, "body": "Session data recorded successfully!"}


def leaderboard(event: dict, context: LambdaContext) -> dict:
    """ Get Leaderboard Stats """
    # Initialize DynamoDB resource and table
    endpoint_url = os.getenv('DYNAMODB_ENDPOINT')
    dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
    table = dynamodb.Table(os.getenv('SESSIONS_TABLE', 'Sessions'))

    try:
        # List to store the top 10 runs
        top_runs = list()
        unique_users = set()

        # Paginator for handling large result sets
        paginator = table.meta.client.get_paginator('query')

        # Query parameters
        query_params = {
            'TableName': 'Sessions',
            'IndexName': 'LeaderboardGSI',
            'KeyConditionExpression': Key('status').eq('COMPLETED'),
            'ProjectionExpression': '#user_name, #sessionid, #duration',
            'ExpressionAttributeNames': {"#user_name": "user_name", "#sessionid": "sessionid", "#duration": "duration"},
            'ScanIndexForward': True  # Ascending order (faster runs first)
        }

        # Paginate through the results
        for page in paginator.paginate(**query_params):
            logger.debug(f"Got {len(page['Items'])} items in the current page of the paginator")
            for item in page['Items']:
                logger.debug(f"Current item: {item}")
                run = {
                    'user_name': item['user_name'],
                    'sessionid': item['sessionid'],
                    'duration': str(item['duration'])
                }

                # keep going if we already have this user in the list
                if item['user_name'] in unique_users:
                    logger.debug(f"Not adding entry for {item['user_name']}, they are already in the list")
                    continue

                # Add run to the list if it's in the top 10
                if len(top_runs) < 10:
                    logger.debug(f"appending current {run}")
                    top_runs.append(run)
                    unique_users.add(item['user_name'])
                else:
                    # If we have 10 runs and the current run is slower than all of them,
                    # we can stop querying as all subsequent runs will be slower
                    break
            else:
                # This else clause belongs to the for loop, not the if statement
                # It's executed when the for loop completes normally (i.e., wasn't broken)
                continue
            # If we've broken out of the inner loop, break out of the pagination loop too
            break

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Headers" : "Content-Type",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
            },
            "body": json.dumps(top_runs)
        }

    except Exception as e:
        return {"statusCode": 500, 'body': f"Internal server error: {str(e)}"}

from flask import Flask, request, jsonify, send_from_directory
import boto3
import os
from dotenv import load_dotenv
from passageidentity import Passage, PassageError
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')

# Initialize DynamoDB resource and table
dynamodb = boto3.resource('dynamodb', endpoint_url=os.getenv('DYNAMODB_ENDPOINT'))
table = dynamodb.Table(os.getenv('SESSIONS_TABLE', 'Sessions'))

# Initialize Passage for user authentication
passage = Passage(app_id=os.getenv('PASSAGE_APP_ID'), api_key=os.getenv('PASSAGE_API_KEY'))

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/report', methods=['POST'])
def report():
    try:
        if 'Authorization' not in request.headers:
            return jsonify({'error': "Missing 'Authorization' header"}), 400

        token = request.headers.get('Authorization').split(' ')[1]
        user_info = passage.getUser(token)
        email = user_info.email

        return process_request(request, email)

    except PassageError as e:
        return jsonify({'error': f"Authentication failed: {str(e)}"}), 401
    except Exception as e:
        return jsonify({'error': f"Internal server error: {str(e)}"}), 500

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    try:
        # Scan DynamoDB table to get all items
        response = table.scan()
        items = response.get('Items', [])

        # Calculate duration for each item
        results = {}
        for item in items:
            email = item.get('email')
            start = item.get('start')
            end = item.get('end')
            if start and end:
                duration = end - start
                # Store the shortest duration for each email
                if email not in results or duration < results[email]:
                    results[email] = duration

        # Convert results to list and sort by duration (shortest to longest)
        sorted_results = sorted(
            [{'name': email, 'duration': duration} for email, duration in results.items()],
            key=lambda x: x['duration']
        )

        return jsonify(sorted_results)

    except Exception as e:
        return jsonify({'error': f"Internal server error: {str(e)}"}), 500

def process_request(req, email):
    http_method = req.method
    path = req.path

    if http_method == 'POST' and path == '/report':
        return handle_report(req, email)
    elif http_method == 'GET' and path == '/leaderboard':
        return leaderboard()
    else:
        return jsonify({'error': 'Invalid request'}), 400

def parse_datetime(dt_str):
    """ Parse datetime string with or without milliseconds. """
    try:
        return int(datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp())
    except ValueError:
        return int(datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ").timestamp())

def handle_report(req, email):
    body = req.get_json()

    sessionid = body.get('sessionid')
    start = body.get('start')
    end = body.get('end')

    if start:
        start_timestamp = parse_datetime(start)
        table.update_item(
            Key={'sessionid': sessionid},
            UpdateExpression="SET #s = :s, email = :e",
            ExpressionAttributeNames={"#s": "start"},
            ExpressionAttributeValues={":s": start_timestamp, ":e": email}
        )

    if end:
        end_timestamp = parse_datetime(end)
        table.update_item(
            Key={'sessionid': sessionid},
            UpdateExpression="SET #e = :e",
            ExpressionAttributeNames={"#e": "end"},
            ExpressionAttributeValues={":e": end_timestamp}
        )

    return jsonify({'message': 'Session data recorded successfully!'})


if __name__ == '__main__':
    app.run(debug=True)

import json
import os
from passageidentity import Passage, PassageError


PASSAGE_APP_ID = os.getenv("PASSAGE_APP_ID")
PASSAGE_API_KEY = os.getenv("PASSAGE_API_KEY")


def handler(event, context):
    token = event['authorizationToken'].split(' ')[1]
    try:
        passage = Passage(PASSAGE_APP_ID, PASSAGE_API_KEY)
        userid = passage.authenticateJWT(token)
        user_info = passage.getUser(userid)
        email = user_info.email

        response = generate_policy(email, 'Allow', event['methodArn'], user_info)
        return json.loads(response)
    except PassageError as e:
        return {'error': f"Authentication failed: {str(e)}"}


def generate_policy(principal_id, effect, resource, user_info):
    auth_response = {'principalId': principal_id}
    if effect and resource:
        policyDocument = {}
        policyDocument['Version'] = '2012-10-17'
        policyDocument['Statement'] = []
        statementOne = {}
        statementOne['Action'] = 'execute-api:Invoke'
        statementOne['Effect'] = effect
        statementOne['Resource'] = resource
        policyDocument['Statement'] = [statementOne]
        auth_response['policyDocument'] = policyDocument
    auth_response['context'] = {
        "name": user_info.user_metadata.get("name"),
        "email": user_info.email,
    }
    auth_response_json = json.dumps(auth_response)
    return auth_response_json

# Scaf Leaderboard

## Getting started

Start up a local DynamoDB

```$ docker run -p 8000:8000 amazon/dynamodb-local -jar DynamoDBLocal.jar -sharedDb```

Start the local SAM

```$ sam local start-api --env-vars env.json --debug```


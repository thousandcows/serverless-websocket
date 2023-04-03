def ping(event, context):
    response = {
        "statusCode": 200,
        "body": "PONG!"
    }
    return response

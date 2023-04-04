import boto3
import logging
import json

logger = logging.getLogger("handler_logger")
logger.setLevel(logging.DEBUG)

dynamodb = boto3.resource("dynamodb")

def send_message(event, context):

    # request body 가 제대로 왔는지 체크
    body = json.loads(event.get("body", ""))
    for attribute in ["content"]:
        if attribute not in body:
            logger.debug("Failed: f'{attribute}' not in message dict.")
            return {"statusCode": 400, "body": f"'{attribute}' not in message dict"}

    # 모든 연결을 가져온다
    table = dynamodb.Table("serverless-websocket-connections")
    response = table.scan(ProjectionExpression="connection_id")
    items = response.get("Items", [])
    connections = [x["connection_id"] for x in items if "connection_id" in x]

    # 모든 연결에게 broadcast
    message = {"content": content}
    logger.debug(f"Broadcasting message: {message}")
    data = {"messages": [message]}
    for connection_id in connections:
        endpoint_url = f"https://{event['requestContext']['domainName']}/{event['requestContext']['stage']}"
        gatewayapi = boto3.client("apigatewaymanagementapi", endpoint_url=endpoint_url)
        gatewayapi.post_to_connection(ConnectionId=connection_id, Data=json.dumps(data).encode('utf-8'))
    return {"statusCode": 200, "body": f"Message sent to all connections."}

def connection_manager(event, context):
    connection_id = event["requestContext"].get("connectionId")

    if event["requestContext"]["eventType"] == "CONNECT":
        logger.info("Connect requested")
        # connection_id 를 생성한다.
        table = dynamodb.Table("serverless-websocket-connections")
        table.put_item(Item={"connection_id": connection_id})
        return {"statusCode": 200, "body": "Connect successful."}

    elif event["requestContext"]["eventType"] == "DISCONNECT":
        logger.info("Disconnect requested")
        # connection_id 를 삭제한다.
        table = dynamodb.Table("serverless-websocket-connections")
        table.delete_item(Key={"connection_id": connection_id})
        return {"statusCode": 200, "body": "Disconnect successful."}
    else:
        # 정의되지 않은 이벤트 타입인 경우
        logger.error("Connection manager received unrecognized eventType '{}'")
        return {"statusCode": 500, "body": "Unrecognized eventType."}

def ping(event, context):
    response = {
        "statusCode": 200,
        "body": "PONG!"
    }
    return response

def default_message(event, context):
    logger.info("Unrecognized WebSocket action received.")
    return {"statusCode": 400, "body": "Unrecognized WebSocket action."}

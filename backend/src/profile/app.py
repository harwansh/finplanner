"""GET /profile and PUT /profile - reads/writes the user's financial profile."""
import json
import os
import sys
import time
from decimal import Decimal

import boto3

# Make ../common importable
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from common.utils import respond, get_user_id, parse_body  # noqa: E402

TABLE_NAME = os.environ["TABLE_NAME"]
ddb = boto3.resource("dynamodb")
table = ddb.Table(TABLE_NAME)


def _floats_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _floats_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_floats_to_decimal(v) for v in obj]
    return obj


def handler(event, context):
    method = event.get("httpMethod")
    user_id = get_user_id(event)
    if not user_id:
        return respond(401, {"error": "unauthorized"})

    if method == "GET":
        result = table.get_item(Key={"userId": user_id})
        item = result.get("Item")
        if not item:
            return respond(200, {"profile": None})
        return respond(200, {"profile": item.get("profile", {})})

    if method == "PUT":
        body = parse_body(event)
        profile = body.get("profile")
        if not isinstance(profile, dict):
            return respond(400, {"error": "profile object required"})
        item = {
            "userId": user_id,
            "profile": _floats_to_decimal(profile),
            "updatedAt": int(time.time()),
        }
        table.put_item(Item=item)
        return respond(200, {"ok": True})

    return respond(405, {"error": "method not allowed"})

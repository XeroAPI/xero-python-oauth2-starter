# -*- coding: utf-8 -*-
import json
import uuid
from datetime import datetime, date
from decimal import Decimal

from xero_python.api_client.serializer import serialize


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, date):
            return o.isoformat()
        if isinstance(o, (uuid.UUID, Decimal)):
            return str(o)
        return super(JSONEncoder, self).default(o)


def parse_json(data):
    return json.loads(data, parse_float=Decimal)


def serialize_model(model):
    return jsonify(serialize(model))


def jsonify(data):
    return json.dumps(data, sort_keys=True, indent=4, cls=JSONEncoder)

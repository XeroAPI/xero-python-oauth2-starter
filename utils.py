# -*- coding: utf-8 -*-
import json
import uuid
from datetime import datetime, date
from decimal import Decimal
from functools import singledispatch


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
    return jsonify(model.to_dict())


def jsonify(data):
    return json.dumps(data, sort_keys=True, indent=4, cls=JSONEncoder)


def nested_gettattr(value, path, default=None):
    paths = path.split(".")
    return get_nested(value, *paths, default=default)


@singledispatch
def get_nested(value, path, *paths, default=None):
    value = getattr(value, path, default)
    if paths:
        return get_nested(value, *paths, default=default)

    return value


@get_nested.register(dict)
def get_nested_dict(value, path, *paths, default=None):
    value = value.get(path, default)
    if paths:
        return get_nested(value, *paths, default=default)

    return value


@get_nested.register(list)
@get_nested.register(tuple)
def get_nested_dict(value, path, *paths, default=None):
    try:
        value = value[int(path)]
    except IndexError:
        value = default

    if paths:
        return get_nested(value, *paths, default=default)

    return value

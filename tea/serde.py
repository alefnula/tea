"""Serialization and deserialization library."""

import enum
import json
import dataclasses

from tea import timestamp as ts


class TeaJsonEncoder(json.JSONEncoder):
    """Tea JSON Encoder.

    It knows how to serialize:

        1. All objects that have a custom `to_dict` method.
        2. Decimal numbers.
        3. DateTime, Date adn Timezone objects.
        4. Enums.
        5. Dataclasses
        6. UUIDs.
    """

    to_float = frozenset(("decimal.Decimal",))
    to_datetime = frozenset(("datetime.datetime", "datetime.date"))
    to_list = frozenset(
        (
            "__builtin__.set",
            "builtins.set",
            "builtins.dict_keys",
            "builtins.dict_values",
        )
    )
    to_str = frozenset(("uuid.UUID",))

    def default(self, o):
        try:
            return super(TeaJsonEncoder, self).default(o)
        except TypeError:
            # First see if there is a to_dict method
            if hasattr(o, "to_dict"):
                return o.to_dict()
            # Then try out special classes
            cls = o.__class__
            path = "%s.%s" % (cls.__module__, cls.__name__)
            if path in self.to_float:
                return float(o)
            elif path in self.to_datetime:
                return ts.to_utc_str(o)
            elif path in self.to_list:
                return list(o)
            elif path in self.to_str:
                return str(o)
            elif isinstance(o, enum.Enum):
                return o.value
            elif dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            elif path.startswith("pytz.tzfile."):
                return o.zone
            raise TypeError("%s is not JSON serializable" % o)


json_loads = json.loads


def json_dumps(obj, indent=4) -> str:
    """Wrap `json.dumps` using the `TeaJsonEncoder`."""
    return json.dumps(
        obj,
        cls=TeaJsonEncoder,
        ensure_ascii=False,
        allow_nan=False,
        indent=indent,
        separators=(",", ":"),
    )

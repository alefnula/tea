import enum
import uuid
import decimal
import datetime
from dataclasses import dataclass, asdict

import pytz


from tea import serde
from tea import timestamp as ts


class MyEnum(enum.Enum):
    foo = "foo"
    bar = "bar"


@dataclass
class DC:
    x: int
    y: str


class Foo:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @property
    def sum(self):
        return self.x + self.y

    def to_dict(self):
        return {"x": self.x, "y": self.y, "sum": self.sum}


def test_json_encode():
    d = {"a": 1, "b": 2}
    foo = Foo(3, 4)
    uid = uuid.uuid4()
    dt = datetime.datetime(2017, 3, 16, 18, 30, 15)
    date = datetime.date(2017, 3, 16)
    dc = DC(x=3, y="foo")
    timezone = pytz.timezone("Europe/London")

    data = serde.json_loads(
        serde.json_dumps(
            {
                "to_dict": foo,
                "decimal": decimal.Decimal("3.0"),
                "datetime": dt,
                "date": date,
                "set": {1, 2, 3},
                "dict_keys": d.keys(),
                "dict_values": d.values(),
                "uuid": uid,
                "enum": MyEnum.foo,
                "dataclass": dc,
                "timezone": timezone,
            }
        )
    )
    assert data["to_dict"] == foo.to_dict()
    assert data["decimal"] == 3.0
    assert data["datetime"] == ts.to_utc_str(dt)
    assert data["date"] == ts.to_utc_str(date)
    assert set(data["set"]) == {1, 2, 3}
    assert set(data["dict_keys"]) == set(d.keys())
    assert set(data["dict_values"]) == set(d.values())
    assert data["uuid"] == str(uid)
    assert data["enum"] == MyEnum.foo.value
    assert data["dataclass"] == asdict(dc)
    assert data["timezone"] == timezone.zone

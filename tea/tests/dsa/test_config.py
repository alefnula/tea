import os
from unittest import mock

import pytest

from tea.dsa.config import Config


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

DICT_DATA = {"foo": {"bar": {"baz": 1}, "baz": 2}, "bar": {"baz": 3}, "baz": 4}

INI_DATA = open(os.path.join(DATA_DIR, "config.ini")).read()
JSON_DATA = open(os.path.join(DATA_DIR, "config.json")).read()


@pytest.fixture
def config():
    return Config(data=DICT_DATA)


def is_subset(dict1, dict2):
    """Is dict1 subset of dict2."""
    for key, value in dict1.items():
        if key not in dict2 or value != dict2[key]:
            return False
    return True


def check_values(config, foo=True, bar=True):
    if foo:
        assert is_subset({"bar": {"baz": 1}, "baz": 2}, config.get("foo"))
        assert is_subset({"baz": 1}, config.get("foo.bar"))
        assert config.get("foo.bar.baz") == 1
        assert config.get("foo.baz") == 2
    if bar:
        assert is_subset({"baz": 3}, config.get("bar"))
        assert config.get("bar.baz") == 3
    assert config.get("baz") == 4


def test_data_dict():
    check_values(Config(data=DICT_DATA))


def test_data_json():
    check_values(Config(data=JSON_DATA, fmt=Config.JSON))


def test_file_json():
    check_values(Config(filename=os.path.join(DATA_DIR, "config.json")))


def test_non_existing_file():
    config = Config(filename=os.path.join(DATA_DIR, "non_existin.json"))
    assert config.data == {}


def test_unsupported_format():
    config = Config(filename=os.path.join(DATA_DIR, "config.ini"))
    assert config.data == {}
    config = Config(data=INI_DATA, fmt="INI")
    assert config.data == {}


def test_invalid_format():
    config = Config(
        filename=os.path.join(DATA_DIR, "config.ini"), fmt=Config.JSON
    )
    assert config.data == {}
    config = Config(data=INI_DATA, fmt=Config.JSON)
    assert config.data == {}


@mock.patch("os.path.isdir", return_value=False)
@mock.patch("os.makedirs")
@mock.patch("io.open")
def test_save_json(io_open, makedirs, isdir):
    filename = "some_filename"
    dirname = os.path.abspath(os.path.dirname(filename))
    c = Config(data=JSON_DATA, fmt=Config.JSON)
    c.filename = filename
    c.save()
    isdir.assert_called_with(dirname)
    makedirs.assert_called_with(dirname, 0o755)
    io_open.assert_called_with(filename, "w", encoding="utf-8")
    io_open.result.write.asswert_called_with(JSON_DATA)


@mock.patch("os.path.isdir")
@mock.patch("os.makedirs")
@mock.patch("io.open")
def test_save_unsupported(io_open, makedirs, isdir):
    isdir.return_value = True
    filename = "some_filename"
    dirname = os.path.abspath(os.path.dirname(filename))
    c = Config(data=JSON_DATA, fmt=Config.JSON)
    c.filename = filename
    c.fmt = "INI"
    c.save()
    isdir.assert_called_with(dirname)
    assert not makedirs.called
    assert not io_open.called


def test_add_first_level(config):
    config.set("first", 5)
    assert config.get("first") == 5
    # the rest should be untouched
    check_values(config)


def test_add_second_level(config):
    config.set("first.second", 6)
    assert config.get("first") == {"second": 6}
    assert config.get("first.second") == 6
    # the rest should be untouched
    check_values(config)


def test_add_in_existing_first_level_one_level(config):
    config.set("foo.first", 7)
    assert config.get("foo.first") == 7
    # the rest should be untouched
    check_values(config)


def test_add_in_existing_first_level_two_levels(config):
    config.set("foo.first.second", 8)
    assert config.get("foo.first") == {"second": 8}
    assert config.get("foo.first.second") == 8
    # the rest should be untouched
    check_values(config)


def test_add_in_existing_second_level_one_level(config):
    config.set("foo.bar.first", 9)
    assert config.get("foo") == {"bar": {"baz": 1, "first": 9}, "baz": 2}
    assert config.get("foo.bar") == {"baz": 1, "first": 9}
    assert config.get("foo.bar.first") == 9
    # the rest should be untouched
    check_values(config, foo=False)


def test_add_in_existing_second_level_two_levels(config):
    config.set("foo.bar.first.second", 10)
    assert config.get("foo") == {
        "bar": {"baz": 1, "first": {"second": 10}},
        "baz": 2,
    }
    assert config.get("foo.bar") == {"baz": 1, "first": {"second": 10}}
    assert config.get("foo.bar.first") == {"second": 10}
    assert config.get("foo.bar.first.second") == 10
    # the rest should be untouched
    check_values(config, foo=False)


def test_list_insertion(config):
    config.set("foo.l", [])
    assert config.get("foo.l") == []
    config.insert("foo.l", 1)
    assert config.get("foo.l") == [1]
    assert config.get("foo.l.0") == 1
    config.insert("foo.l", 0, 0)
    assert config.get("foo.l") == [0, 1]
    assert config.get("foo.l.0") == 0
    assert config.get("foo.l.1") == 1
    config.set("foo.l.0", 2)
    assert config.get("foo.l") == [2, 1]
    assert config.get("foo.l.0") == 2
    assert config.get("foo.l.1") == 1


def test_insertion_in_non_list(config):
    pytest.raises(KeyError, lambda: config.insert("foo", 0))


def test_set_first_level(config):
    config.set("foo", 11)
    assert config.get("foo") == 11
    # the rest should be untouched
    check_values(config, foo=False)


def test_set_second_level(config):
    config.set("foo.bar", 12)
    assert config.get("foo") == {"bar": 12, "baz": 2}
    assert config.get("foo.bar") == 12
    # the rest should be untouched
    check_values(config, foo=False)


def test_set_third_level(config):
    config.set("foo.bar.baz", 13)
    assert config.get("foo") == {"bar": {"baz": 13}, "baz": 2}
    assert config.get("foo.bar") == {"baz": 13}
    assert config.get("foo.bar.baz") == 13
    # the rest should be untouched
    check_values(config, foo=False)


def test_delete_first_level(config):
    config.delete("foo")
    assert config.get("foo") is None
    # the rest should be untouched
    check_values(config, foo=False)


def test_delete_second_level(config):
    config.delete("foo.bar")
    assert config.get("foo") == {"baz": 2}
    assert config.get("foo.bar") is None
    # the rest should be untouched
    check_values(config, foo=False)


def test_delete_third_level(config):
    config.delete("foo.bar.baz")
    assert config.get("foo") == {"bar": {}, "baz": 2}
    assert config.get("foo.bar") == {}
    assert config.get("foo.bar.baz") is None
    # the rest should be untouched
    check_values(config, foo=False)


def test_delete_from_list(config):
    config.set("foo.l", [1, 2, 3])
    config.delete("foo.l.1")
    assert config.get("foo.l") == [1, 3]
    del config["foo.l.0"]
    assert config.get("foo.l") == [3]


def test_safe_delete(config):
    config.delete("non_existent")
    check_values(config)


def test_unsafe_key_error(config):
    pytest.raises(KeyError, lambda: config["nonexistant"])
    pytest.raises(KeyError, lambda: config["non.existant"])
    pytest.raises(KeyError, lambda: config["foo.nonexistant"])
    pytest.raises(KeyError, lambda: config["foo.non.existant"])
    pytest.raises(KeyError, lambda: config["foo.bar.nonexistant"])
    pytest.raises(KeyError, lambda: config["foo.bar.non.existant"])
    pytest.raises(KeyError, lambda: config["foo.bar.baz.nonexistant"])
    pytest.raises(KeyError, lambda: config["foo.bar.baz.non.existant"])


def test_unsafe_index_error(config):
    config["list"] = [1, 2]
    assert config["list.0"] == 1
    assert config["list.1"] == 2
    assert config["list.-1"] == 2
    assert config["list.-2"] == 1
    pytest.raises(IndexError, lambda: config["list.2"])
    pytest.raises(IndexError, lambda: config["list.-3"])


def test_keys(config):
    assert config.keys() == set(["foo", "bar", "baz"])


def test_contains(config):
    # Existing
    assert "foo" in config
    assert "foo.bar" in config
    assert "foo.bar.baz" in config
    assert "foo.baz" in config
    assert "bar" in config
    assert "bar.baz" in config
    assert "baz" in config
    # Non existing
    assert "oof" not in config
    assert "bar.foo" not in config
    assert "baz.foo" not in config
    assert "baz.bar" not in config
    assert "foo.baz.bar" not in config

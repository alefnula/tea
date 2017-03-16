__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '16 March 2017'
__copyright__ = 'Copyright (c) 2017 Viktor Kerkez'

import pytest
from tea.dsa.dicts import DictObject


@pytest.fixture
def do():
    return DictObject({
        'name': 'John Doe',
        'age': 34,
        'address': {
            'city': 'San Francisco',
            'street': 'Mission St'
        }
    })


def test_dictobject_get(do):
    assert do.name == 'John Doe'
    assert do.age == 34
    assert isinstance(do.address, DictObject)
    assert do.address.city == 'San Francisco'
    assert do.address.street == 'Mission St'


def test_dictobject_set(do):
    do.name = 'Jane Doe'
    do.address.street = 'Folsom St'
    assert do.name == 'Jane Doe'
    assert do['name'] == 'Jane Doe'
    assert do.address.city == 'San Francisco'
    assert do.address.street == 'Folsom St'
    do['address'].street = 'Hayes St'
    assert do.address.street == 'Hayes St'
    assert do.address['city'] == 'San Francisco'

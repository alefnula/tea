import pytest

from tea.version import Version


@pytest.fixture
def version():
    return Version(3, 4, 5)


def test_version_fields(version):
    assert version.major == 3
    assert version.minor == 4
    assert version.build == 5


def test_version_string(version):
    assert str(version) == "3.4.5"

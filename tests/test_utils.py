import pytest

from snowflake_manager.utils import plural, treat_metadata_value, format_params


def test_plural():
    assert plural("user") == "users"
    assert plural("warehouse") == "warehouses"
    assert plural("database") == "databases"
    assert plural("schema") == "schemas"
    assert plural("role") == "roles"


def test_treat_metadata_value():
    assert treat_metadata_value("true") == True
    assert treat_metadata_value("false") == False
    assert treat_metadata_value("TRUE") == True
    assert treat_metadata_value("FALSE") == False
    assert treat_metadata_value("Something") == "something"


def test_format_params():
    assert (
        format_params({"name": "test", "value": "test"})
        == "name = 'test', value = 'test'"
    )
    assert format_params({"name": 1, "value": 1}) == "name = 1, value = 1"
    assert format_params({"name": False, "value": True}) == "name = False, value = True"
    assert (
        format_params({"name": True, "value": "False"}) == "name = True, value = False"
    )

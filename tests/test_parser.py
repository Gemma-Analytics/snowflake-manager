import pytest
from yaml import load, Loader

from snowflake_manager.parser import parse_object_type
from snowflake_manager.objects import ConfigurationValueError


def test_required_params_user():
    """Asserts that parser object initialization checks for required parameters correctly for users"""
    correct_user_spec_path = "tests/data/correct_required_params_spec.yml"
    correct_permifrost_spec = load(open(correct_user_spec_path, "r"), Loader=Loader)
    parse_object_type(correct_permifrost_spec, "user")

    incorrect_user_spec_path = "tests/data/incorrect_required_params_spec.yml"
    incorrect_permifrost_spec = load(open(incorrect_user_spec_path, "r"), Loader=Loader)
    with pytest.raises(ConfigurationValueError) as exc:
        parse_object_type(incorrect_permifrost_spec, "user")
    assert "missing: ['default_role']" in str(exc.value)


def test_required_params_warehouse():
    """Asserts that parser object initialization checks for required parameters correctly for warehouses"""
    correct_warehouse_spec_path = "tests/data/correct_required_params_spec.yml"
    correct_permifrost_spec = load(
        open(correct_warehouse_spec_path, "r"), Loader=Loader
    )
    parse_object_type(correct_permifrost_spec, "warehouse")

    incorrect_warehouse_spec_path = "tests/data/incorrect_required_params_spec.yml"
    incorrect_permifrost_spec = load(
        open(incorrect_warehouse_spec_path, "r"), Loader=Loader
    )
    with pytest.raises(ConfigurationValueError) as exc:
        parse_object_type(incorrect_permifrost_spec, "warehouse")
    assert "missing: ['warehouse_size', 'auto_suspend']" in str(exc.value)

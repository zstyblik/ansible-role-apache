#!/usr/bin/env python3
"""Unit tests for filter_plugins.core."""
import pytest
from ansible.errors import AnsibleFilterError

import filter_plugins.core as fpc  # noqa


def test_fpc_available_filters():
    """Check retval of FilterModule.filters()."""
    expected_filters = [
        "file_exists",
        "parse_a2query",
        "to_vhost_filename",
    ]
    filter_module = fpc.FilterModule()
    available_filters = filter_module.filters()
    assert list(available_filters.keys()) == expected_filters


@pytest.mark.parametrize(
    "input_data,expected",
    [
        ({}, False),
        ({"stat": {}}, False),
        ({"stat": {"foo": "bar"}}, False),
        ({"stat": {"isreg": False, "islnk": False}}, False),
        ({"stat": {"isreg": True, "islnk": False}}, True),
        ({"stat": {"isreg": False, "islnk": True}}, True),
        ({"stat": {"isreg": True, "islnk": True}}, True),
    ],
)
def test_fpc_file_exists(input_data, expected):
    """Check that file_exists() works as expected."""
    result = fpc.file_exists(input_data)
    assert result is expected


@pytest.mark.parametrize(
    "input_data,expected",
    [
        (
            [
                "php8.2 (enabled by maintainer script)",
                "alias (enabled by maintainer script)",
                "env (enabled by maintainer script)",
            ],
            ["php8.2", "alias", "env"],
        ),
        (
            "",
            "",
        ),
    ],
)
def test_fpc_parse_a2query(input_data, expected):
    """Check that parse_a2query works as expected."""
    result = fpc.parse_a2query(input_data)
    assert sorted(result) == sorted(expected)


@pytest.mark.parametrize(
    "vhost,expected_fname",
    [
        (
            {"servername": "pytest"},
            "200-http_pytest",
        ),
        (
            {"servername": "pytest", "ssl": {"attr": "is_irrelevant"}},
            "200-https_pytest",
        ),
        (
            {
                "servername": "pytest",
                "ssl": {"attr": "is_irrelevant"},
                "priority": 400,
            },
            "400-https_pytest",
        ),
    ],
)
def test_fpc_to_vhost_filename_happy_path(vhost, expected_fname):
    """Check happy path of to_vhost_filename()."""
    result = fpc.to_vhost_filename(vhost)
    assert result == expected_fname


@pytest.mark.parametrize(
    "vhost,expected_exc_msg",
    [
        (
            {},
            "to_vhost_filename - 'servername'. 'servername'",
        ),
        (
            {"priority": "abc", "servername": "test"},
            (
                "to_vhost_filename - invalid literal for int() with base 10: "
                "'abc'. invalid literal for int() with base 10: 'abc'"
            ),
        ),
        (
            {"priority": 200},
            "to_vhost_filename - 'servername'. 'servername'",
        ),
    ],
)
def test_fpc_to_vhost_filename_unhappy_path(vhost, expected_exc_msg):
    """Check unhappy path of to_vhost_filename()."""
    with pytest.raises(AnsibleFilterError) as exc:
        fpc.to_vhost_filename(vhost)

    assert str(exc.value) == expected_exc_msg

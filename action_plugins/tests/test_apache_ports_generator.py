#!/usr/bin/env python3
"""Unit tests for apache_ports_generator."""
from unittest.mock import Mock

import pytest
from ansible.errors import AnsibleError

from action_plugins.apache_ports_generator import ActionModule  # noqa


@pytest.mark.parametrize(
    "listen_ip,port,proto,expected",
    [
        ("1.2.3.4", 80, None, "1.2.3.4:80"),
        ("1.2.3.4", 80, "https", "1.2.3.4:80 https"),
        (None, 80, None, "80"),
        (None, 80, "https", "80 https"),
    ],
)
def test_apg_format_binding(listen_ip, port, proto, expected):
    """Check that ActionModule._format_binding() works as expected."""
    action = ActionModule(
        "task",
        "connection",
        "play_context",
        "loader",
        "templar",
        "shared_loader_obj",
    )
    result = action._format_binding(listen_ip, port, proto)
    assert result == expected


@pytest.mark.parametrize(
    "vhosts,expected",
    [
        # No vhosts defined.
        (
            [],
            {
                "data": {
                    ":443:": {
                        "formatted": "443",
                        "listen_ip": "",
                        "port": 443,
                        "proto": "",
                    },
                    ":80:": {
                        "formatted": "80",
                        "listen_ip": "",
                        "port": 80,
                        "proto": "",
                    },
                }
            },
        ),
        # Just HTTP/80
        (
            [
                {
                    "port": 80,
                }
            ],
            {
                "data": {
                    ":80:": {
                        "formatted": "80",
                        "listen_ip": "",
                        "port": 80,
                        "proto": "",
                    }
                }
            },
        ),
        # Just HTTPS/443
        (
            [
                {
                    "port": 443,
                }
            ],
            {
                "data": {
                    ":443:": {
                        "formatted": "443",
                        "listen_ip": "",
                        "port": 443,
                        "proto": "",
                    }
                }
            },
        ),
        # Mix
        (
            [
                {
                    "port": 80,
                },
                {
                    "port": 80,
                },
                {
                    "port": 443,
                },
                {
                    "port": 443,
                },
                {
                    "port": 8080,
                },
                {
                    "port": 8081,
                    "ssl": {"attr": "is_irrelevant"},
                },
                {
                    "listen_ip": "1.2.3.4",
                    "port": 8082,
                },
                {
                    "listen_ip": "1.2.3.4",
                    "port": 8083,
                    "ssl": {"attr": "is_irrelevant"},
                },
            ],
            {
                "data": {
                    ":80:": {
                        "formatted": "80",
                        "listen_ip": "",
                        "port": 80,
                        "proto": "",
                    },
                    ":443:": {
                        "formatted": "443",
                        "listen_ip": "",
                        "port": 443,
                        "proto": "",
                    },
                    ":8080:": {
                        "formatted": "8080",
                        "listen_ip": "",
                        "port": 8080,
                        "proto": "",
                    },
                    ":8081:https": {
                        "formatted": "8081 https",
                        "listen_ip": "",
                        "port": 8081,
                        "proto": "https",
                    },
                    "1.2.3.4:8082:": {
                        "formatted": "1.2.3.4:8082",
                        "listen_ip": "1.2.3.4",
                        "port": 8082,
                        "proto": "",
                    },
                    "1.2.3.4:8083:https": {
                        "formatted": "1.2.3.4:8083 https",
                        "listen_ip": "1.2.3.4",
                        "port": 8083,
                        "proto": "https",
                    },
                },
            },
        ),
    ],
)
def test_apg_run_happy_path(vhosts, expected):
    """Test happy path in ActionModule.run()."""
    # NOTE(zstyblik): mocked just enough to make it work.
    mock_task = Mock()
    mock_task.async_val = False
    mock_task.args = {"vhosts": vhosts}
    mock_conn = Mock()
    mock_conn._shell.tmpdir = "/path/does/not/exist"
    action = ActionModule(
        mock_task,
        mock_conn,
        "play_context",
        "loader",
        "templar",
        "shared_loader_obj",
    )
    result = action.run(None, None)
    assert result == expected


@pytest.mark.parametrize(
    "vhosts,expected_exc,expected_exc_msg",
    [
        # Port undefined
        (
            [
                {
                    "servername": "pytest",
                },
            ],
            AnsibleError,
            "vhost 'pytest' is missing port attribute: 'port'",
        ),
        # Port out-of-range
        (
            [
                {
                    "port": -1,
                },
            ],
            AnsibleError,
            "port number '-1' of vhost 'unknown' is out of 0-65535 range",
        ),
        (
            [
                {
                    "port": 72329,
                },
            ],
            AnsibleError,
            "port number '72329' of vhost 'unknown' is out of 0-65535 range",
        ),
        # Invalid port
        (
            [
                {
                    "port": "abcefg",
                },
            ],
            AnsibleError,
            (
                "failed to convert port 'abcefg' of vhost 'unknown' to int: "
                "invalid literal for int() with base 10: 'abcefg'"
            ),
        ),
        (
            [
                {
                    "port": None,
                },
            ],
            AnsibleError,
            (
                "failed to convert port 'None' of vhost 'unknown' to int: "
                "int() argument must be a string, a bytes-like object or "
                "a real number, not 'NoneType'"
            ),
        ),
        # IP/port/protocol collisions
        (
            [
                {
                    "port": 8080,
                },
                {
                    "port": 8080,
                    "ssl": {"attr": "is_irrelevant"},
                },
            ],
            AnsibleError,
            "HTTP/HTTPS collision for IP '' and port '8080' in vhost 'unknown'",
        ),
        (
            [
                {
                    "listen_ip": "1.2.3.4",
                    "port": 8080,
                },
                {
                    "listen_ip": "1.2.3.4",
                    "port": 8080,
                    "ssl": {"attr": "is_irrelevant"},
                },
            ],
            AnsibleError,
            (
                "HTTP/HTTPS collision for IP '1.2.3.4' and port '8080' "
                "in vhost 'unknown'"
            ),
        ),
        (
            [
                {
                    "port": 8080,
                },
                {
                    "listen_ip": "1.2.3.4",
                    "port": 8080,
                },
            ],
            AnsibleError,
            (
                "bind collision any Vs. IP for IP '1.2.3.4' and port '8080' "
                "in vhost 'unknown'"
            ),
        ),
    ],
)
def test_apg_run_unhappy_path(vhosts, expected_exc, expected_exc_msg):
    """Test unhappy path resp. exceptions in ActionModule.run()."""
    # NOTE(zstyblik): mocked just enough to make it work.
    mock_task = Mock()
    mock_task.async_val = False
    mock_task.args = {"vhosts": vhosts}
    mock_conn = Mock()
    mock_conn._shell.tmpdir = "/path/does/not/exist"
    action = ActionModule(
        mock_task,
        mock_conn,
        "play_context",
        "loader",
        "templar",
        "shared_loader_obj",
    )
    with pytest.raises(expected_exc) as exc:
        _ = action.run(None, None)

    assert str(exc.value) == expected_exc_msg

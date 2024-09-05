#!/usr/bin/env python3
"""Action plugin for ansible role apache - apache port config generator.

MIT License

Copyright (c) 2024 Zdenek Styblik

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionBase):
    """Generator of data for ports.conf configuration."""

    TRANSFERS_FILES = False
    _requires_connection = False

    def _format_binding(self, listen_ip, port, proto):
        """Return pre-formatted string for Listen directive."""
        lip_fmt = "{:s}:".format(listen_ip) if listen_ip else ""
        proto_fmt = " {:s}".format(proto) if proto else ""
        return "{:s}{:d}{:s}".format(lip_fmt, port, proto_fmt)

    def run(self, tmp=None, task_vars=None):
        """Transform virtual host definitions into data for ports.conf."""
        result = super().run(tmp, task_vars)
        del tmp

        vhosts = self._task.args.get("vhosts", [])
        if not vhosts:
            vhosts = [
                {"listen_ip": "", "port": 80, "ssl": {}},
                {"listen_ip": "", "port": 443, "ssl": {}},
            ]

        # Ref. https://httpd.apache.org/docs/2.4/bind.html
        # Structure:
        # port -> ip addr -> ssl yes/no
        #
        # Example:
        # 80 -> 1.2.3.4 -> False
        # 80 -> '*' -> ...
        # => EXCEPTION due to collision
        #
        # 80 -> '*' -> False
        # 80 -> '*' -> True
        # => EXCEPTION due to collision
        #
        # then transform it for jinja2
        bindings = {}
        for vhost in vhosts:
            try:
                port = int(vhost["port"])
            except KeyError as exception:
                msg = "vhost '{}' is missing port attribute".format(
                    vhost.get("servername", "unknown")
                )
                raise AnsibleError(msg) from exception
            except ValueError as exception:
                msg = "failed to convert port '{}' of vhost '{}' to int".format(
                    vhost.get("port", None),
                    vhost.get("servername", "unknown"),
                )
                raise AnsibleError(msg) from exception

            if port < 0 or port > 65535:
                raise AnsibleError(
                    "port number '{}' of vhost '{}' is out of 0-65535 "
                    "range".format(
                        port,
                        vhost.get("servername", "unknown"),
                    )
                )

            if port not in bindings:
                bindings[port] = {}

            ssl = vhost.get("ssl", {})
            # According to documentation, https is default proto for port 443.
            # Therefore there is no need to specify it.
            if ssl and port != 443:
                proto = "https"
            else:
                proto = ""

            listen_ip = vhost.get("listen_ip", "")
            if bindings[port]:
                # We need to check for possible numerous and various conflicts.
                if (
                    listen_ip in bindings[port]
                    and bindings[port][listen_ip] != proto
                ):
                    # Reasoning: 'IP:Port' is the same and protocol is
                    # different -> error
                    msg = (
                        "HTTP/HTTPS collision for IP '{}' "
                        "and port '{}' in vhost '{}'".format(
                            listen_ip,
                            port,
                            vhost.get("servername", "unknown"),
                        )
                    )
                    raise AnsibleError(msg)

                if (
                    listen_ip == "" and listen_ip not in bindings[port].keys()
                ) or (listen_ip != "" and "" in bindings[port].keys()):
                    # Reasoning: if listening on *:80, then we cannot listen
                    # on 1.2.3.4:80 as well and vice versa.
                    msg = (
                        "bind collision any Vs. IP for IP '{}' "
                        "and port '{}' in vhost '{}'".format(
                            listen_ip,
                            port,
                            vhost.get("servername", "unknown"),
                        )
                    )
                    raise AnsibleError(msg)

            bindings[port][listen_ip] = proto

        result["data"] = {
            "{}:{}:{}".format(listen_ip, port, binding[listen_ip]): {
                "listen_ip": listen_ip,
                "port": port,
                "proto": binding[listen_ip],
                "formatted": self._format_binding(
                    listen_ip, port, binding[listen_ip]
                ),
            }
            for port, binding in bindings.items()
            for listen_ip in binding
        }
        return result

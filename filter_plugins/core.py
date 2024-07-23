#!/usr/bin/env python3
"""Filter plugin for ansible role apache.

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
from ansible.errors import AnsibleFilterError
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.common.text.converters import to_text


def file_exists(stat_result):
    """Evaluate stat() results.

    Return True if file is either regular file or symlink, otherwise return
    False.
    """
    stat_data = stat_result.get("stat", None)
    if not stat_data:
        return False

    isreg = stat_data.get("isreg")
    islnk = stat_data.get("islnk")
    if isreg or islnk:
        return True

    return False


def parse_a2query(stdout):
    """Parse the first column from a2query STDOUT lines."""
    if not stdout:
        return stdout

    return [line.split(" ")[0] for line in stdout]


def to_vhost_filename(vhost):
    """Turn apache_vhost item(dict) into a filename."""
    try:
        priority = int(vhost.get("priority", 25))
        if "ssl" in vhost and vhost["ssl"]:
            proto = "https"
        else:
            proto = "http"

        servername = vhost["servername"]
        result = "{:d}-{:s}_{:s}".format(priority, proto, servername)
    except Exception as exception:
        raise AnsibleFilterError(
            "to_vhost_filename - {:s}".format(to_native(exception)),
            orig_exc=exception,
        )

    return to_text(result)


class FilterModule:
    """Filters used by apache httpd role."""

    def filters(self):
        """Return available filters."""
        return {
            "file_exists": file_exists,
            "parse_a2query": parse_a2query,
            "to_vhost_filename": to_vhost_filename,
        }

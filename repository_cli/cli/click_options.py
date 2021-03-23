# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Commonly used options for CLI commands."""

import click

# -i '{ "identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}'
option_identifier = click.option(
    "--identifier",
    "-i",
    required=True,
    help="metadata identifier as JSON",
)

# -p "fcze8-4vx33"
option_pid = click.option(
    "--pid",
    "-p",
    metavar="PID_VALUE",
    required=True,
    help="persistent identifier of the object to operate on",
)

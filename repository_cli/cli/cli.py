# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CLI commands for repository-cli."""

import click

from .records import rdmrecords
from .users import users


@click.group()
def utilities():
    """Utility commands for TU Graz Repository."""


utilities.add_command(users)
utilities.add_command(rdmrecords)

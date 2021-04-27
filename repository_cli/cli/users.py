# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Management commands for users."""

import click
from flask.cli import with_appcontext
from invenio_accounts.models import User


@click.group()
def users():
    """Management commands for users."""
    pass


@users.command("list")
@with_appcontext
def list_users():
    """List registered users.

    example call:
        invenio repository users list
    """
    users = User.query

    for user in users:
        line = "{} {}".format(user.id, user.email)

        fg = "green" if user.active else "red"
        click.secho(line, fg=fg)

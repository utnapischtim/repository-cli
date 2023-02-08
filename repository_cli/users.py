# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Management commands for users."""

import click
from flask.cli import with_appcontext
from invenio_accounts.models import User
from tabulate import tabulate


@click.group("users")
def group_users():
    """Management commands for users."""


@group_users.command("list")
@with_appcontext
def list_users():
    """List registered users.

    example call:
        invenio repository users list
    """
    users = []

    for user in User.query:
        active = "YES" if user.active else "NO"

        users.append([user.id, user.email, active, user.confirmed_at])

    print(tabulate(users, headers=["id", "email", "active", "confirmed"]))

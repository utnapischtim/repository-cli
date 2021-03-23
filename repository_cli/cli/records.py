# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Management commands for records."""

import json

import click
from flask.cli import with_appcontext
from flask_principal import Identity
from invenio_rdm_records.records.models import RDMRecordMetadata
from invenio_records import Record

from .click_options import option_identifier, option_pid
from .util import get_draft, get_identity, get_records_service, update_record


@click.group()
def records():
    """Management commands for records."""
    pass


@records.command("list")
@with_appcontext
def list_records():
    """List record's.

    example call:
        invenio repository records list
    """
    records = RDMRecordMetadata.query
    for index, metadata in enumerate(records):
        fg = "blue" if index % 2 == 0 else "cyan"
        click.secho(json.dumps(metadata.data, indent=2), fg=fg)


@records.command("delete")
@option_pid
@with_appcontext
def delete_record(pid):
    """Delete record.

    example call:
        invenio repository records delete -p "fcze8-4vx33"
    """
    identity = get_identity(
        permission_name="system_process", role_name="admin"
    )
    service = get_records_service()
    service.delete(id_=pid, identity=identity)
    click.secho(f"{pid}", fg="green")


@records.group()
def identifiers():
    """Management commands for record identifiers."""
    pass


@identifiers.command("list")
@option_pid
@with_appcontext
def list_identifiers(pid):
    """List record's identifiers.

    example call:
        invenio repository records identifiers list
    """
    identity = get_identity()
    service = get_records_service()
    record_data = service.read(id_=pid, identity=identity).data.copy()
    current_identifiers = record_data["metadata"].get("identifiers", [])

    if len(current_identifiers) == 0:
        fg = "yellow"
        click.secho("record does not have any identifiers", fg=fg)

    for index, identifier in enumerate(current_identifiers):
        # BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET
        fg = "blue" if index % 2 == 0 else "cyan"
        click.secho(json.dumps(identifier, indent=2), fg=fg)


@identifiers.command("add")
@option_identifier
@option_pid
@with_appcontext
def add_identifier(identifier, pid):
    """Update the specified record's identifiers.

    example call:
        invenio repository records identifiers add -p "fcze8-4vx33"
        -i '{ "identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}'
    """
    identifier = json.loads(identifier)
    if type(identifier) is not dict:
        click.secho(f"identifier should be of type dictionary", fg="red")
        return

    identity = get_identity("system_process")
    service = get_records_service()

    # get current draft or create new one
    draft = get_draft(pid, identity)
    should_publish = False
    if draft is None:
        should_publish = True
        draft = service.edit(id_=pid, identity=identity)

    record_data = draft.data.copy()
    current_identifiers = record_data["metadata"].get("identifiers", [])
    current_schemes = [_["scheme"] for _ in current_identifiers]
    scheme = identifier["scheme"]
    if scheme in current_schemes:
        if should_publish:
            service.delete_draft(id_=pid, identity=identity)
        click.secho(f"scheme '{scheme}' already in identifiers", fg="red")
        return

    current_identifiers.append(identifier)
    record_data["metadata"]["identifiers"] = current_identifiers

    try:
        update_record(
            pid=pid,
            identity=identity,
            should_publish=should_publish,
            new_data=record_data,
            old_data=draft.data,
        )
        click.secho(pid, fg="green")
    except Exception as e:
        click.secho(f"{pid}, {e}", fg="red")

    return


@identifiers.command("replace")
@option_identifier
@option_pid
@with_appcontext
def replace_identifier(identifier, pid):
    """Update the specified record's identifiers.

    example call:
        invenio repository records identifiers add -p "fcze8-4vx33"
        -i '{ "identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}'
    """
    identifier = json.loads(identifier)
    if type(identifier) is not dict:
        click.secho(f"identifier should be of type dictionary", fg="red")
        return

    identity = get_identity("system_process")
    service = get_records_service()

    # get current draft or create new one
    draft = get_draft(pid, identity)
    should_publish = False
    if draft is None:
        should_publish = True
        draft = service.edit(id_=pid, identity=identity)

    record_data = draft.data.copy()
    current_identifiers = record_data["metadata"].get("identifiers", [])
    scheme = identifier["scheme"]
    replaced = False
    for index, ci in enumerate(current_identifiers):
        if ci["scheme"] == scheme:
            current_identifiers[index] = identifier
            replaced = True
            break

    if not replaced:
        if should_publish:
            service.delete_draft(id_=pid, identity=identity)
        click.secho(f"scheme '{scheme}' not in identifiers", fg="red")
        return

    record_data["metadata"]["identifiers"] = current_identifiers

    try:
        update_record(
            pid=pid,
            identity=identity,
            should_publish=should_publish,
            new_data=record_data,
            old_data=draft.data,
        )
        click.secho(pid, fg="green")
    except Exception as e:
        click.secho(f"{pid}, {e}", fg="red")

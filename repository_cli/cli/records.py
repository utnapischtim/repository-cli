# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Management commands for records."""

import json
from typing import TextIO

import click
from flask.cli import with_appcontext
from flask_principal import Identity
from invenio_rdm_records.records.models import RDMRecordMetadata
from invenio_records import Record

from .click_options import (option_identifier, option_input_file,
                            option_output_file, option_pid)
from .util import (get_draft, get_identity, get_records_service, record_exists,
                   update_record)


@click.group()
def records():
    """Management commands for records."""
    pass


@records.command("list")
@option_output_file()
@with_appcontext
def list_records(output_file: TextIO):
    """List record's.

    example call:
        invenio repository records list [--of out.json]
    """
    records = RDMRecordMetadata.query.filter_by(is_deleted=False)
    if output_file:
        output_file.write("[")

    num_records = records.count()

    # rather iterate and write one record at time instead of converting to list
    # (might take up much memory)
    for index, metadata in enumerate(records):
        if output_file:
            json.dump(metadata.json, output_file, indent=2)
            if index < (num_records - 1):
                output_file.write(",\n")
        else:
            fg = "blue" if index % 2 == 0 else "cyan"
            click.secho(json.dumps(metadata.json, indent=2), fg=fg)

    if output_file:
        output_file.write("]")

        click.secho(
            f"wrote {num_records} records to {output_file.name}", fg="green"
        )
    else:
        click.secho(f"{num_records} records", fg="green")


@records.command("update")
@option_input_file(required=True)
@with_appcontext
def update_records(input_file: TextIO):
    """Update records specified in input file.

    example call:
        invenio repository records update --if in.json
    """
    records = json.load(input_file)
    identity = get_identity(
        permission_name="system_process", role_name="admin"
    )
    service = get_records_service()

    for record in records:
        pid = record["id"]
        click.secho(f"\n'{pid}', trying to update", fg="yellow")
        if not record_exists(pid):
            click.secho(f"'{pid}', does not exist or is deleted", fg="red")
            continue

        old_data = service.read(id_=pid, identity=identity).data.copy()
        try:
            update_record(
                pid=pid, identity=identity, new_data=record, old_data=old_data
            )
        except Exception as e:
            click.secho(f"'{pid}', problem during update, {e}", fg="red")
            continue

        click.secho(f"'{pid}', successfully updated", fg="green")


@records.command("delete")
@option_pid(required=True)
@with_appcontext
def delete_record(pid: str):
    """Delete record.

    example call:
        invenio repository records delete -p "fcze8-4vx33"
    """
    if not record_exists(pid):
        click.secho(f"'{pid}', does not exist or is deleted", fg="red")
        return

    identity = get_identity(
        permission_name="system_process", role_name="admin"
    )
    service = get_records_service()
    service.delete(id_=pid, identity=identity)
    click.secho(f"'{pid}', soft-deleted", fg="green")


@records.group()
def identifiers():
    """Management commands for record identifiers."""
    pass


@identifiers.command("list")
@option_pid(required=option_pid)
@with_appcontext
def list_identifiers(pid: str):
    """List record's identifiers.

    example call:
        invenio repository records identifiers list -p <pid>
    """
    if not record_exists(pid):
        click.secho(f"'{pid}', does not exist or is deleted", fg="red")
        return

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
@option_identifier(required=True)
@option_pid(required=True)
@with_appcontext
def add_identifier(identifier: map, pid: str):
    """Update the specified record's identifiers.

    example call:
        invenio repository records identifiers add -p "fcze8-4vx33"
        -i '{ "identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}'
    """
    identifier = json.loads(identifier)
    if type(identifier) is not dict:
        click.secho(f"identifier should be of type dictionary", fg="red")
        return

    if not record_exists(pid):
        click.secho(f"'{pid}', does not exist or is deleted", fg="red")
        return

    identity = get_identity("system_process", role_name="admin")
    service = get_records_service()
    record_data = service.read(id_=pid, identity=identity).data.copy()

    current_identifiers = record_data["metadata"].get("identifiers", [])
    current_schemes = [_["scheme"] for _ in current_identifiers]
    scheme = identifier["scheme"]
    if scheme in current_schemes:
        click.secho(f"scheme '{scheme}' already in identifiers", fg="red")
        return

    old_data = record_data.copy()
    current_identifiers.append(identifier)
    record_data["metadata"]["identifiers"] = current_identifiers

    try:
        update_record(
            pid=pid, identity=identity, new_data=record_data, old_data=old_data
        )
    except Exception as e:
        click.secho(f"'{pid}', Error during update, {e}", fg="red")
        return

    click.secho(f"Identifier for '{pid}'' added.", fg="green")
    return


@identifiers.command("replace")
@option_identifier(required=True)
@option_pid(required=True)
@with_appcontext
def replace_identifier(identifier: map, pid: str):
    """Update the specified record's identifiers.

    example call:
        invenio repository records identifiers replace -p "fcze8-4vx33"
        -i '{ "identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}'
    """
    identifier = json.loads(identifier)
    if type(identifier) is not dict:
        click.secho(f"identifier should be of type dictionary", fg="red")
        return

    if not record_exists(pid):
        click.secho(f"'{pid}', does not exist or is deleted", fg="red")
        return

    identity = get_identity("system_process", role_name="admin")
    service = get_records_service()
    record_data = service.read(id_=pid, identity=identity).data.copy()
    current_identifiers = record_data["metadata"].get("identifiers", [])
    scheme = identifier["scheme"]
    replaced = False
    for index, ci in enumerate(current_identifiers):
        if ci["scheme"] == scheme:
            current_identifiers[index] = identifier
            replaced = True
            break

    if not replaced:
        click.secho(f"scheme '{scheme}' not in identifiers", fg="red")
        return

    old_data = record_data.copy()
    record_data["metadata"]["identifiers"] = current_identifiers

    try:
        update_record(
            pid=pid, identity=identity, new_data=record_data, old_data=old_data
        )
    except Exception as e:
        click.secho(f"'{pid}', problem during update, {e}", fg="red")
        return

    click.secho(pid, fg="green")

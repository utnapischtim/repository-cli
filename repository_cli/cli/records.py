# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Management commands for records."""

import json
import os
from io import SEEK_END, SEEK_SET
from typing import TextIO

import click
from flask.cli import with_appcontext
from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_rdm_records.records.models import RDMRecordMetadata

from .click_options import (
    option_identifier,
    option_input_file,
    option_output_file,
    option_pid,
    option_pid_identifier,
)
from .util import (
    get_draft,
    get_identity,
    get_records_service,
    record_exists,
    update_record,
)


@click.group()
def rdmrecords():
    """Management commands for records."""


@rdmrecords.command("count")
@with_appcontext
def count_records():
    """Count number of record's.

    example call:
        invenio repository rdmrecords count
    """
    records = RDMRecordMetadata.query.filter_by(is_deleted=False)
    num_records = records.count()
    click.secho(f"{num_records} records", fg="green")


@rdmrecords.command("list")
@option_output_file()
@with_appcontext
def list_records(output_file: TextIO):
    """List record's.

    example call:
        invenio repository rdmrecords list [--of out.json]
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

        click.secho(f"wrote {num_records} records to {output_file.name}", fg="green")
    else:
        click.secho(f"{num_records} records", fg="green")


@rdmrecords.command("update")
@option_input_file(required=True)
@with_appcontext
def update_records(input_file: TextIO):
    """Update records specified in input file.

    example call:
        invenio repository rdmrecords update --if in.json
    """
    try:
        records = json.load(input_file)
    except Exception as e:
        click.secho(e.msg, fg="red")
        click.secho(f"The input file is not a valid JSON File", fg="red")
        return

    identity = get_identity(permission_name="system_process", role_name="admin")
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


@rdmrecords.command("delete")
@option_pid(required=True)
@with_appcontext
def delete_record(pid: str):
    """Delete record.

    example call:
        invenio repository rdmrecords delete -p "fcze8-4vx33"
    """
    if not record_exists(pid):
        click.secho(f"'{pid}', does not exist or is deleted", fg="red")
        return

    identity = get_identity(permission_name="system_process", role_name="admin")
    service = get_records_service()
    service.delete(id_=pid, identity=identity)
    click.secho(f"'{pid}', soft-deleted", fg="green")


@rdmrecords.command("delete-draft")
@option_pid(required=True)
@with_appcontext
def delete_draft(pid: str):
    """Delete draft.

    example call:
        invenio repository rdmrecords delete-draft -p "fcze8-4vx33"
    """
    if not record_exists(pid):
        click.secho(f"'{pid}', does not exist or is deleted", fg="red")
        return

    identity = get_identity(permission_name="system_process", role_name="admin")

    draft = get_draft(pid=pid, identity=identity)
    if draft is None:
        click.secho(f"'{pid}', does not have a draft", fg="yellow")
        return

    service = get_records_service()
    service.delete_draft(id_=pid, identity=identity)
    click.secho(f"'{pid}', deleted draft", fg="green")


@rdmrecords.group()
def pids():
    """Management commands for record pids."""


@pids.command("list")
@option_pid(required=True)
@with_appcontext
def list_pids(pid: str):
    """List record's pids.

    example call:
        invenio repository rdmrecords pids list -p <pid>
    """
    if not record_exists(pid):
        click.secho(f"'{pid}', does not exist or is deleted", fg="red")
        return

    identity = get_identity()
    service = get_records_service()
    record_data = service.read(id_=pid, identity=identity).data.copy()
    current_pids = record_data.get("pids", {}).items()

    if len(current_pids) == 0:
        fg = "yellow"
        click.secho("record does not have any pids", fg=fg)

    for index, pid in enumerate(current_pids):
        # BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET
        fg = "blue" if index % 2 == 0 else "cyan"
        click.secho(json.dumps(pid, indent=2), fg=fg)


@pids.command("replace")
@option_pid(required=True)
@option_pid_identifier(required=True)
@with_appcontext
def replace_pid(pid: str, pid_identifier: str):
    """Update pid doi to unmanaged.

    example call:
        invenio repository rdmrecords pids replace -p "fcze8-4vx33"
        --pid-identifier ' { "doi": {
        "identifier": "10.48436/fcze8-4vx33", "provider": "unmanaged" }}'
    """
    try:
        pid_identifier_json = json.loads(pid_identifier)
    except Exception as e:
        click.secho(e.msg, fg="red")
        click.secho(f"pid_identifier is not valid JSON", fg="red")
        return

    if not record_exists(pid):
        click.secho(f"'{pid}', does not exist or is deleted", fg="red")
        return

    identity = get_identity(permission_name="system_process", role_name="admin")
    service = get_records_service()

    old_data = service.read(id_=pid, identity=identity).data.copy()
    new_data = old_data.copy()
    pids = new_data.get("pids", {})
    pid_key = list(pid_identifier_json.keys())[0]

    if pids.get(pid_key, None) is None:
        click.secho(f"'{pid}' does not have pid identifier '{pid_key}'", fg="yellow")
        return

    pids[pid_key] = pid_identifier_json.get(pid_key)
    new_data["pids"] = pids

    try:
        update_record(pid=pid, identity=identity, new_data=new_data, old_data=old_data)
    except Exception as e:
        click.secho(f"'{pid}', problem during update, {e}", fg="red")
        return

    click.secho(f"'{pid}', successfully updated", fg="green")


@rdmrecords.group()
def identifiers():
    """Management commands for record identifiers."""


@identifiers.command("list")
@option_pid(required=option_pid)
@with_appcontext
def list_identifiers(pid: str):
    """List record's identifiers.

    example call:
        invenio repository rdmrecords identifiers list -p <pid>
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
def add_identifier(identifier: str, pid: str):
    """Update the specified record's identifiers.

    example call:
        invenio repository rdmrecords identifiers add -p "fcze8-4vx33"
        -i '{ "identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}'
    """
    try:
        identifier_json = json.loads(identifier)
    except Exception as e:
        click.secho(e.msg, fg="red")
        click.secho(f"identifier is not valid JSON", fg="red")
        return

    if not record_exists(pid):
        click.secho(f"'{pid}', does not exist or is deleted", fg="red")
        return

    identity = get_identity("system_process", role_name="admin")
    service = get_records_service()
    record_data = service.read(id_=pid, identity=identity).data.copy()

    current_identifiers = record_data["metadata"].get("identifiers", [])
    current_schemes = [_["scheme"] for _ in current_identifiers]
    scheme = identifier_json["scheme"]
    if scheme in current_schemes:
        click.secho(f"scheme '{scheme}' already in identifiers", fg="red")
        return

    old_data = record_data.copy()
    current_identifiers.append(identifier_json)
    record_data["metadata"]["identifiers"] = current_identifiers

    try:
        update_record(
            pid=pid, identity=identity, new_data=record_data, old_data=old_data
        )
    except Exception as e:
        click.secho(f"'{pid}', Error during update, {e}", fg="red")
        return

    click.secho(f"Identifier for '{pid}' added.", fg="green")
    return


@identifiers.command("replace")
@option_identifier(required=True)
@option_pid(required=True)
@with_appcontext
def replace_identifier(identifier: str, pid: str):
    """Update the specified record's identifiers.

    example call:
        invenio repository rdmrecords identifiers replace -p "fcze8-4vx33"
        -i '{ "identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}'
    """
    try:
        identifier_json = json.loads(identifier)
    except Exception as e:
        click.secho(e.msg, fg="red")
        click.secho(f"identifier is not valid JSON", fg="red")
        return

    if not record_exists(pid):
        click.secho(f"'{pid}', does not exist or is deleted", fg="red")
        return

    identity = get_identity("system_process", role_name="admin")
    service = get_records_service()
    record_data = service.read(id_=pid, identity=identity).data.copy()
    current_identifiers = record_data["metadata"].get("identifiers", [])
    scheme = identifier_json["scheme"]
    replaced = False
    for index, ci in enumerate(current_identifiers):
        if ci["scheme"] == scheme:
            current_identifiers[index] = identifier_json
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

    click.secho(f"Identifier for '{pid}' replaced.", fg="green")


@rdmrecords.command("add_file")
@click.argument("recid", type=str)
@click.argument("fp", type=click.File("rb"))
@click.option("--replace-existing", "-f", is_flag=True, default=False)
@click.option("--data-model", default="rdm")
@click.option("--enable-files", is_flag=True, default=False)
@with_appcontext
def add_file(recid, fp, replace_existing, data_model, enable_files):
    """Add a new file to a published record."""
    identity = get_identity("system_process", role_name="admin")
    service = get_records_service(data_model=data_model)

    try:
        record = service.read(identity=identity, id_=recid)._record
    except PIDDoesNotExistError as e:
        click.secho(
            "Record with type '{pid_type}' and id '{pid_value}' does not exist.".format(
                pid_type=e.pid_type, pid_value=e.pid_value
            ),
            fg="red",
        )
        return

    files = record.files
    bucket = files.bucket

    key = os.path.basename(fp.name)
    obj = None
    try:
        obj = files[key]
    except Exception as e:
        click.echo("File does not yet exist.")

    if obj is not None and not replace_existing:
        click.secho(
            'File with key "{key}" already exists.'
            " Use `--replace-existing/-f` to overwrite it.".format(
                key=key, recid=recid
            ),
            fg="red",
        )
        return

    if not files.enabled and not enable_files:
        click.secho(
            "Files are not enabled for this record (metadata-only)."
            "  Use `--enable-files` to add it anyway.",
            fg="red",
        )
        return

    fp.seek(SEEK_SET, SEEK_END)
    size = fp.tell()
    fp.seek(SEEK_SET)

    click.echo("Will add the following file:\n")
    click.secho(
        '  key: "{key}"\n'
        "  bucket: {bucket}\n"
        "  size: {size}\n"
        "".format(key=key, bucket=bucket.id, size=size),
        fg="green",
    )
    click.echo("to record:\n")
    click.secho(
        '  Title: "{title}"\n'
        "  ID   : {recid}\n"
        "  UUID : {uuid}\n"
        "".format(
            recid=record["id"],
            title=record.get("metadata", {}).get("title"),
            uuid=record.id,
            fg="green",
        )
    )
    if replace_existing and obj is not None:
        click.echo("and remove the file:\n")
        click.secho(
            '  key: "{key}"\n'
            "  bucket: {bucket}\n"
            "  size: {size}\n"
            "".format(key=obj.key, bucket=bucket, size=obj.file.size),
            fg="green",
        )

    if click.confirm("Continue?"):
        files.enabled = True  # this allows to also add files to metadata only records
        files.unlock()
        if obj is not None and replace_existing:
            files.delete(obj.key)
        files.create(key, stream=fp)
        files.lock()

        record.commit()
        db.session.commit()
        click.secho("File added successfully.", fg="green")
    else:
        click.secho("File addition aborted.", fg="green")

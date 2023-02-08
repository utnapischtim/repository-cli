# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Management commands for records."""

import json
import os
from copy import deepcopy
from io import SEEK_END, SEEK_SET
from typing import TextIO

import click
import jq
from click import secho
from flask.cli import with_appcontext
from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError

from .click_options import (
    option_data_model,
    option_identifier,
    option_input_file,
    option_jq_filter,
    option_output_file,
    option_pid,
    option_pid_identifier,
    option_quiet,
    option_record_type,
)
from .click_param_types import JSON
from .types import Color
from .utils import (
    add_metadata_to_marc21_record,
    exists_record,
    get_draft,
    get_identity,
    get_metadata_model,
    get_record_or_draft,
    get_records_service,
    update_record,
)


@click.group("records")
def group_records():
    """Management commands for records."""


@group_records.command("count")
@option_data_model
@option_record_type
@with_appcontext
def count_records(data_model, record_type):
    """Count number of record's.

    example call:
        invenio repository records count
    """
    model = get_metadata_model(data_model, record_type)
    records = model.query.filter_by(is_deleted=False)
    num_records = records.count()
    secho(f"{num_records} records", fg=Color.success)


@group_records.command("list")
@option_output_file(required=False)
@option_data_model
@option_quiet
@option_jq_filter
@option_record_type
@with_appcontext
def list_records(
    output_file: TextIO, data_model: str, quiet: bool, jq_filter: str, record_type: str
):
    """List record's.

    example call:
        invenio repository records list [--output-file out.json]
        invenio repository records list --record-type draft \
                                           --data-model marc21 \
                                           --output-file /dev/stdout \
                                           --quiet \
                                           --jq-filter '.pids.doi.identifier'
    """
    model = get_metadata_model(data_model, record_type)
    records = model.query.filter_by(is_deleted=False)

    if output_file:
        output_file.write("[")

    num_records = records.count()

    jq_compiled_filter = jq.compile(jq_filter)

    # rather iterate and write one record at time instead of converting to list
    # (might take up much memory)
    for index, metadata in enumerate(records):
        output = jq_compiled_filter.input(metadata.json).first()

        if not output:
            continue

        if output_file:
            json.dump(output, output_file, indent=2)
            if index < (num_records - 1):
                output_file.write(",\n")
        else:
            secho(json.dumps(output, indent=2), fg=Color.alternate[index % 2])

    if output_file:
        output_file.write("]\n")
        output_file.flush()

        output_msg = f"wrote {num_records} records to {output_file.name}"
    else:
        output_msg = f"{num_records} records"

    if not quiet:
        secho(output_msg, fg=Color.success)


@group_records.command("update")
@option_input_file(type_=JSON(), name="records")
@option_data_model
@with_appcontext
def update_records(records: list, data_model):
    """Update records specified in input file.

    example call:
        invenio repository records update --input-file in.json

    Description:
      the record could be replaced completelly by the given json
      object. The record has to have the same structure as the normal
      record within the repository.

      WARNING: this command is really dangerous. It could ruin the
      whole database.
    """
    identity = get_identity(permission_name="system_process", role_name="admin")
    service = get_records_service(data_model)

    for record in records:
        pid = record["id"]
        secho(f"\n'{pid}', trying to update", fg=Color.warning)

        if not exists_record(service, pid, identity):
            secho(f"'{pid}', does not exist or is deleted", fg=Color.error)
            continue

        old_data = service.read(id_=pid, identity=identity).data

        try:
            update_record(service, pid, identity, record, old_data)
        except Exception as error:
            secho(f"'{pid}', problem during update, {error}", fg=Color.error)
            continue

        secho(f"'{pid}', successfully updated", fg=Color.success)


@group_records.command("add-metadata")
@option_input_file(type_=JSON(), name="records")
@option_data_model
@with_appcontext
def add_metadata_to_records(records: list, data_model):
    """Add metadata to records.

    example call:
        invenio repository records update --input-file in.json [--data-model marc21]

    Description:
      file should look like:
      [{"id": "ID",
         "metadata": {
           "fields": {
             "995": [{"ind1": "", "ind2": "", "subfields": {"a": ["VALUE"]}}]
           }
         }
       }
      ]
    """
    identity = get_identity(permission_name="system_process", role_name="admin")
    service = get_records_service(data_model)

    for record in records:
        pid = record["id"]

        secho(f"\n'{pid}', trying to update", fg=Color.warning)

        try:
            old_data = get_record_or_draft(service, pid, identity)
        except RuntimeError as error:
            secho(str(error), fg=Color.error)
            continue

        if data_model == "marc21":
            new_data = add_metadata_to_marc21_record(deepcopy(old_data), record)
        else:
            raise RuntimeError(
                "Only marc21 is implemented for adding metadata to record."
            )

        try:
            update_record(service, pid, identity, new_data, old_data)
        except Exception as error:
            secho(
                f"'{pid}', an error occured on updating the record, {error}",
                fg=Color.error,
            )
            continue

        secho(f"'{pid}', successfully updated", fg=Color.success)


@group_records.command("delete")
@option_pid
@with_appcontext
def delete_record(pid: str):
    """Delete record.

    example call:
        invenio repository records delete -p "fcze8-4vx33"
    """
    service = get_records_service()
    identity = get_identity(permission_name="system_process", role_name="admin")

    if not exists_record(service, pid, identity):
        secho(f"'{pid}', does not exist or is deleted", fg=Color.error)
        return

    service.delete(id_=pid, identity=identity)
    secho(f"'{pid}', soft-deleted", fg=Color.success)


@group_records.command("delete-draft")
@option_pid
@with_appcontext
def delete_draft(pid: str):
    """Delete draft.

    example call:
        invenio repository records delete-draft -p "fcze8-4vx33"
    """
    service = get_records_service()
    identity = get_identity(permission_name="system_process", role_name="admin")

    if not exists_record(service, pid, identity):
        secho(f"'{pid}', does not exist or is deleted", fg=Color.error)
        return

    draft = get_draft(service=service, pid=pid, identity=identity)
    if draft is None:
        secho(f"'{pid}', does not have a draft", fg=Color.warning)
        return

    service.delete_draft(id_=pid, identity=identity)
    secho(f"'{pid}', deleted draft", fg=Color.success)


@group_records.group("pids")
def group_pids():
    """Management commands for record pids."""


@group_pids.command("list")
@option_pid
@with_appcontext
def list_pids(pid: str):
    """List record's pids.

    example call:
        invenio repository records pids list -p <pid>
    """
    service = get_records_service()
    identity = get_identity()

    if not exists_record(service, pid, identity):
        secho(f"'{pid}', does not exist or is deleted", fg=Color.error)
        return

    record_data = service.read(id_=pid, identity=identity).data.copy()
    current_pids = record_data.get("pids", {}).items()

    if len(current_pids) == 0:
        secho("record does not have any pids", fg=Color.warning)

    for index, current_pid in enumerate(current_pids):
        secho(json.dumps(current_pid, indent=2), fg=Color.alternate[index % 2])


@group_pids.command("replace")
@option_pid
@option_pid_identifier
@with_appcontext
def replace_pid(pid: str, pid_identifier: str):
    """Update pid doi to unmanaged.

    example call:
        invenio repository records pids replace -p "fcze8-4vx33"
        --pid-identifier ' { "doi": {
        "identifier": "10.48436/fcze8-4vx33", "provider": "unmanaged" }}'
    """
    try:
        pid_identifier_json = json.loads(pid_identifier)
    except Exception as error:
        secho(str(error), fg=Color.error)
        secho("pid_identifier is not valid JSON", fg=Color.error)
        return

    service = get_records_service()
    identity = get_identity(permission_name="system_process", role_name="admin")

    if not exists_record(service, pid, identity):
        secho(f"'{pid}', does not exist or is deleted", fg=Color.error)
        return

    old_data = service.read(id_=pid, identity=identity).data.copy()
    new_data = old_data.copy()
    pids = new_data.get("pids", {})
    pid_key = list(pid_identifier_json.keys())[0]

    if pids.get(pid_key, None) is None:
        secho(f"'{pid}' does not have pid identifier '{pid_key}'", fg=Color.warning)
        return

    pids[pid_key] = pid_identifier_json.get(pid_key)
    new_data["pids"] = pids

    try:
        update_record(service, pid, identity, new_data, old_data)
    except Exception as error:
        secho(f"'{pid}', problem during update, {error}", fg=Color.error)
        return

    secho(f"'{pid}', successfully updated", fg=Color.success)


@group_records.group("identifiers")
def group_identifiers():
    """Management commands for record identifiers."""


@group_identifiers.command("list")
@option_pid
@with_appcontext
def list_identifiers(pid: str):
    """List record's identifiers.

    example call:
        invenio repository records identifiers list -p <pid>
    """
    service = get_records_service()
    identity = get_identity()

    if not exists_record(service, pid, identity):
        secho(f"'{pid}', does not exist or is deleted", fg=Color.error)
        return

    record_data = service.read(id_=pid, identity=identity).data.copy()
    current_identifiers = record_data["metadata"].get("identifiers", [])

    if len(current_identifiers) == 0:
        secho("record does not have any identifiers", fg=Color.warning)

    for index, identifier in enumerate(current_identifiers):
        secho(json.dumps(identifier, indent=2), fg=Color.alternate[index % 2])


@group_identifiers.command("add")
@option_identifier
@option_pid
@with_appcontext
def add_identifier(identifier: str, pid: str):
    """Update the specified record's identifiers.

    example call:
        invenio repository records identifiers add -p "fcze8-4vx33"
        -i '{ "identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}'
    """
    try:
        identifier_json = json.loads(identifier)
    except Exception as error:
        secho(str(error), fg=Color.error)
        secho("identifier is not valid JSON", fg=Color.error)
        return

    service = get_records_service()
    identity = get_identity("system_process", role_name="admin")

    if not exists_record(service, pid, identity):
        secho(f"'{pid}', does not exist or is deleted", fg=Color.error)
        return

    record_data = service.read(id_=pid, identity=identity).data.copy()

    current_identifiers = record_data["metadata"].get("identifiers", [])
    current_schemes = [_["scheme"] for _ in current_identifiers]
    scheme = identifier_json["scheme"]
    if scheme in current_schemes:
        secho(f"scheme '{scheme}' already in identifiers", fg=Color.error)
        return

    old_data = record_data.copy()
    current_identifiers.append(identifier_json)
    record_data["metadata"]["identifiers"] = current_identifiers

    try:
        update_record(service, pid, identity, record_data, old_data)
    except Exception as error:
        secho(f"'{pid}', Error during update, {error}", fg=Color.error)
        return

    secho(f"Identifier for '{pid}' added.", fg=Color.success)
    return


@group_identifiers.command("replace")
@option_identifier
@option_pid
@with_appcontext
def replace_identifier(identifier: str, pid: str):
    """Update the specified record's identifiers.

    example call:
        invenio repository records identifiers replace -p "fcze8-4vx33"
        -i '{ "identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}'
    """
    try:
        identifier_json = json.loads(identifier)
    except Exception as error:
        secho(str(error), fg=Color.error)
        secho("identifier is not valid JSON", fg=Color.error)
        return

    service = get_records_service()
    identity = get_identity("system_process", role_name="admin")

    if not exists_record(service, pid, identity):
        secho(f"'{pid}', does not exist or is deleted", fg=Color.error)
        return

    record_data = service.read(id_=pid, identity=identity).data.copy()
    current_identifiers = record_data["metadata"].get("identifiers", [])
    scheme = identifier_json["scheme"]
    replaced = False
    for index, current_identifier in enumerate(current_identifiers):
        if current_identifier["scheme"] == scheme:
            current_identifiers[index] = identifier_json
            replaced = True
            break

    if not replaced:
        secho(f"scheme '{scheme}' not in identifiers", fg=Color.error)
        return

    old_data = record_data.copy()
    record_data["metadata"]["identifiers"] = current_identifiers

    try:
        update_record(service, pid, identity, record_data, old_data)
    except Exception as error:
        secho(f"'{pid}', problem during update, {error}", fg=Color.error)
        return

    secho(f"Identifier for '{pid}' replaced.", fg=Color.success)


@group_records.command("add_file")
@option_pid
@option_data_model
@option_input_file(type_=click.File("rb"))
@click.option("--replace-existing", "-f", is_flag=True, default=False)
@click.option("--enable-files", is_flag=True, default=False)
@with_appcontext
def add_file(pid, input_file, replace_existing, data_model, enable_files):
    """Add a new file to a published record."""
    identity = get_identity("system_process", role_name="admin")
    service = get_records_service(data_model=data_model)

    try:
        # pylint: disable=protected-access
        record = service.read(identity=identity, id_=pid)._record
    except PIDDoesNotExistError as error:
        secho(
            f"Record with type '{error.pid_type}' and id '{error.pid_value}' does not exist.",
            fg=Color.error,
        )
        return

    files = record.files
    bucket = files.bucket

    filename = os.path.basename(input_file.name)
    obj = None
    try:
        obj = files[filename]
    except KeyError:
        secho("File does not yet exist.", fg=Color.neutral)

    if obj is not None and not replace_existing:
        secho(
            f"Use --replace-existing to overwrite existing {filename} file",
            fg=Color.error,
        )
        return

    if not files.enabled and not enable_files:
        secho(
            "Use --enable-files to add files to (metadata-only) record",
            fg=Color.error,
        )
        return

    input_file.seek(SEEK_SET, SEEK_END)
    size = input_file.tell()
    input_file.seek(SEEK_SET)

    title = record.get("metadata", {}).get("title")
    messages = {
        "Will add the following file:": Color.neutral,
        f"  filename: {filename}\n  bucket: {bucket}\n  size: {size}": Color.success,
        "to record:": Color.neutral,
        f"  Title: {title}\n  ID: {record['id']}\n  UUID: {record.id}": Color.success,
    }

    for message, color in messages.items():
        secho(message, fg=color)

    if replace_existing and obj is not None:
        secho("and remove the file:\n", fg=Color.neutral)
        secho(
            f"  filename: {obj.key}\n  bucket: {bucket}\n  size: {obj.file.size}",
            fg=Color.success,
        )

    if click.confirm("Continue?"):
        files.enabled = True  # this allows to also add files to metadata only records
        files.unlock()
        if obj is not None and replace_existing:
            files.delete(obj.key)
        files.create(filename, stream=input_file)
        files.lock()

        record.commit()
        db.session.commit()  # pylint: disable=no-member
        secho("File added successfully.", fg=Color.success)
    else:
        secho("File addition aborted.", fg=Color.abort)

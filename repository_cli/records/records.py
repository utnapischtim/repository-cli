# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Records records."""


import json
from copy import deepcopy
from typing import TextIO

import jq
from click import STRING, Choice, option, secho
from flask.cli import with_appcontext
from invenio_pidstore.errors import PIDDoesNotExistError
from sqlalchemy.orm.exc import NoResultFound

from ..click_options import (
    option_data_model,
    option_input_file,
    option_jq_filter,
    option_output_file,
    option_pid,
    option_quiet,
    option_record_type,
)
from ..click_param_types import JSON
from ..types import Color
from ..utils import (
    add_metadata_to_marc21_record,
    exists_record,
    get_data,
    get_identity,
    get_metadata_model,
    get_records_service,
    update_record,
)


@option_data_model
@option_record_type
@with_appcontext
def count(data_model: str, record_type: str) -> None:
    """Count number of record's.

    example call:
        invenio repository records count
    """
    model = get_metadata_model(data_model, record_type)
    records = model.query.filter_by(is_deleted=False)
    num_records = records.count()
    secho(f"{num_records} records", fg=Color.success)


@option_output_file(required=False)
@option_data_model
@option_quiet
@option_jq_filter
@option_record_type
@with_appcontext
def list_records(
    output_file: TextIO,
    data_model: str,
    quiet: bool,  # noqa: FBT001
    jq_filter: str,
    record_type: str,
) -> None:
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


@option_input_file(type_=JSON(), name="records")
@option_data_model
@with_appcontext
def update(records: list, data_model: str) -> None:
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

        old_data = get_data(service, pid, identity)

        try:
            update_record(service, pid, identity, record, old_data)
        except Exception as error:
            secho(f"'{pid}', problem during update, {error}", fg=Color.error)
            continue

        secho(f"'{pid}', successfully updated", fg=Color.success)


@option_input_file(type_=JSON(), name="records")
@option_data_model
@with_appcontext
def add_category(records: list, data_model: str) -> None:
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
            old_data = get_data(service, pid, identity)
        except RuntimeError as error:
            secho(str(error), fg=Color.error)
            continue

        if data_model == "marc21":
            new_data = add_metadata_to_marc21_record(deepcopy(old_data), record)
        else:
            msg = "Only marc21 is implemented for adding metadata to record."
            raise RuntimeError(msg)

        try:
            update_record(service, pid, identity, new_data, old_data)
        except Exception as error:
            secho(
                f"'{pid}', an error occured on updating the record, {error}",
                fg=Color.error,
            )
            continue

        secho(f"'{pid}', successfully updated", fg=Color.success)


@option_pid
@option_record_type
@option_data_model
@with_appcontext
def delete(pid: str, data_model: str, record_type: str) -> None:
    """Delete record.

    example call:
        invenio repository records delete --data-model rdm \
                                          --record-type [draft|record] \
                                          --pid "fcze8-4vx33"
    """
    service = get_records_service(data_model)
    identity = get_identity(permission_name="system_process", role_name="admin")

    if not exists_record(service, pid, identity):
        secho(f"'{pid}', does not exist or is deleted", fg=Color.error)
        return

    try:
        if record_type == "draft":
            service.delete_draft(id_=pid, identity=identity)
        elif record_type == "record":
            service.delete(id_=pid, identity=identity)
        else:
            secho("wrong record_type", fg=Color.error)
    except NoResultFound:
        secho(f"'{pid}' does not have a draft", fg=Color.warning)
        return
    except PIDDoesNotExistError:
        secho(f"'{pid}' does not exists", fg=Color.warning)
        return

    secho(f"'{pid}', soft-deleted", fg=Color.success)


@option_data_model
@option_input_file(
    type_=JSON(),
    name="record_ids",
    help_="json array of ids",
    required=False,
)
@option("--record-id", type=STRING)
@option("--access-record", default=None, type=Choice(["public", "restricted"]))
@option("--access-file", default=None, type=Choice(["public", "restricted"]))
@with_appcontext
def modify_access(
    data_model: str,
    record_ids: list,
    record_id: str,
    access_record: str,
    access_file: str,
) -> None:
    """Modify the access object within the record."""
    identity = get_identity("system_process", role_name="admin")
    service = get_records_service(data_model=data_model)

    if not record_ids and record_id:
        record_ids = [record_id]

    for rec_id in record_ids:
        data = service.read(id_=rec_id, identity=identity).data

        if access_record:
            data["access"]["record"] = access_record
        if access_file:
            data["access"]["files"] = access_file

        service.edit(id_=rec_id, identity=identity)
        service.update_draft(id_=rec_id, identity=identity, data=data)
        service.publish(id_=rec_id, identity=identity)


@option_data_model
@option_input_file(
    type_=JSON(),
    name="record_ids",
    help_="json array of ids",
    required=False,
)
@option("--record-id", type=STRING)
@with_appcontext
def publish(data_model: str, record_ids: list, record_id: str) -> None:
    """Publish all records."""
    identity = get_identity("system_process", role_name="admin")
    service = get_records_service(data_model=data_model)

    if not record_ids and record_id:
        record_ids = [record_id]

    for rec_id in record_ids:
        record = service.publish(id_=rec_id, identity=identity)
        secho(f"record ({record.id}) published", fg=Color.success)

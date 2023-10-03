# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Management commands for records."""

from json import dumps

from click import secho
from flask.cli import with_appcontext

from ..click_options import option_identifier, option_pid
from ..types import Color
from ..utils import exists_record, get_identity, get_records_service, update_record


@option_pid
@with_appcontext
def list_identifiers(pid: str) -> None:
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
        secho(dumps(identifier, indent=2), fg=Color.alternate[index % 2])


@option_identifier
@option_pid
@with_appcontext
def add(identifier: str, pid: str) -> None:
    """Update the specified record's identifiers.

    example call:
        invenio repository records identifiers add -p "fcze8-4vx33"
        -i '{ "identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}'
    """
    service = get_records_service()
    identity = get_identity("system_process", role_name="admin")

    if not exists_record(service, pid, identity):
        secho(f"'{pid}', does not exist or is deleted", fg=Color.error)
        return

    record_data = service.read(id_=pid, identity=identity).data.copy()

    current_identifiers = record_data["metadata"].get("identifiers", [])
    current_schemes = [ci["scheme"] for ci in current_identifiers]
    scheme = identifier["scheme"]
    if scheme in current_schemes:
        secho(f"scheme '{scheme}' already in identifiers", fg=Color.error)
        return

    old_data = record_data.copy()
    current_identifiers.append(identifier)
    record_data["metadata"]["identifiers"] = current_identifiers

    try:
        update_record(service, pid, identity, record_data, old_data)
    except Exception as error:
        secho(f"'{pid}', Error during update, {error}", fg=Color.error)
        return

    secho(f"Identifier for '{pid}' added.", fg=Color.success)
    return


@option_identifier
@option_pid
@with_appcontext
def replace(identifier: str, pid: str) -> None:
    """Update the specified record's identifiers.

    example call:
        invenio repository records identifiers replace -p "fcze8-4vx33"
        -i '{ "identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}'
    """
    service = get_records_service()
    identity = get_identity("system_process", role_name="admin")

    if not exists_record(service, pid, identity):
        secho(f"'{pid}', does not exist or is deleted", fg=Color.error)
        return

    record_data = service.read(id_=pid, identity=identity).data.copy()
    current_identifiers = record_data["metadata"].get("identifiers", [])
    scheme = identifier["scheme"]
    replaced = False
    for index, current_identifier in enumerate(current_identifiers):
        if current_identifier["scheme"] == scheme:
            current_identifiers[index] = identifier
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

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

from ..click_options import option_data_model, option_pid, option_pid_identifier
from ..types import Color
from ..utils import exists_record, get_identity, get_records_service, update_record


@option_pid
@option_data_model
@with_appcontext
def list_pids(pid: str, data_model: str) -> None:
    """List record's pids.

    example call:
        invenio repository records pids list -p <pid>
    """
    service = get_records_service(data_model)
    identity = get_identity()

    if not exists_record(service, pid, identity):
        secho(f"'{pid}', does not exist or is deleted", fg=Color.error)
        return

    record_data = service.read(id_=pid, identity=identity).data.copy()
    current_pids = record_data.get("pids", {}).items()

    if len(current_pids) == 0:
        secho("record does not have any pids", fg=Color.warning)

    for index, current_pid in enumerate(current_pids):
        secho(dumps(current_pid, indent=2), fg=Color.alternate[index % 2])


@option_pid
@option_pid_identifier
@option_data_model
@with_appcontext
def replace_pid(pid: str, pid_identifier: str, data_model: str) -> None:
    """Update pid doi to unmanaged.

    example call:
        invenio repository records pids replace -p "fcze8-4vx33"
        --pid-identifier '{"doi": {
        "identifier": "10.48436/fcze8-4vx33", "provider": "unmanaged"}}'
    """
    service = get_records_service(data_model)
    identity = get_identity(permission_name="system_process", role_name="admin")

    if not exists_record(service, pid, identity):
        secho(f"'{pid}', does not exist or is deleted", fg=Color.error)
        return

    old_data = service.read(id_=pid, identity=identity).data.copy()
    new_data = old_data.copy()
    pids = new_data.get("pids", {})
    pid_key = list(pid_identifier.keys())[0]

    if pids.get(pid_key, None) is None:
        secho(f"'{pid}' does not have pid identifier '{pid_key}'", fg=Color.warning)
        return

    pids[pid_key] = pid_identifier.get(pid_key)
    new_data["pids"] = pids

    try:
        update_record(service, pid, identity, new_data, old_data)
    except Exception as error:
        secho(f"'{pid}', problem during update, {error}", fg=Color.error)
        return

    secho(f"'{pid}', successfully updated", fg=Color.success)

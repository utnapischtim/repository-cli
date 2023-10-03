# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Management commands for records files."""


from pathlib import Path

from click import STRING, File, option, secho
from flask.cli import with_appcontext
from invenio_db import db

from ..click_options import option_data_model, option_input_file, option_pid
from ..types import Color
from ..utils import get_identity, get_record_or_draft, get_records_service


@option_data_model
@option_pid
@option("--filename", type=STRING, required=True)
@with_appcontext
def delete(data_model: str, pid: str, filename: str) -> None:
    """Delete the file."""
    identity = get_identity("system_process", role_name="admin")
    service = get_records_service(data_model=data_model)

    try:
        record = get_record_or_draft(service, pid, identity)
    except RuntimeError as error:
        secho(error.msg, fg=Color.error)
        return

    files = record.files
    obj = None

    try:
        obj = files[filename]
    except KeyError:
        secho(
            f"File with filename: {filename} not found. Check filename or PID",
            fg=Color.error,
        )
        return

    files.unlock()
    files.delete(obj.key)
    files.lock()

    record.commit()
    db.session.commit()
    secho("File deleted successfully", fg=Color.success)


@option_data_model
@option_pid
@option_input_file(type_=File("rb"))
@option("--override-name-match-check", is_flag=True, default=False)
@with_appcontext
def replace(
    data_model: str,
    pid: str,
    input_file: File,
    override_name_match_check: bool,  # noqa: FBT001
) -> None:
    """Replace the file."""
    identity = get_identity("system_process", role_name="admin")
    service = get_records_service(data_model=data_model)

    try:
        record = get_record_or_draft(service, pid, identity)
    except RuntimeError as error:
        secho(error.msg, fg=Color.error)
        return

    files = record.files
    filename = Path(input_file.name).name  # Path().name gets the filename only
    obj = None

    try:
        obj = files[filename]
    except KeyError:
        if override_name_match_check and len(files) == 1:
            filename = list(files)[0]
            obj = files[filename]
        elif len(files) > 1:
            msg = "There is more than 1 file and no matching found, specify filename."
            secho(msg, fg=Color.error)
            return
        else:
            secho(
                "There is only one file but the filename does not match, "
                "maybe use parameter --override-name-match-check.",
                fg=Color.error,
            )
            return

    files.unlock()
    files.delete(obj.key)
    files.create(filename, stream=input_file)
    files.lock()

    record.commit()
    db.session.commit()
    secho("File replaced successfully.", fg=Color.success)


@option_pid
@option_data_model
@option_input_file(type_=File("rb"))
@option("--enable-files", is_flag=True, default=False)
@with_appcontext
def add(
    pid: str,
    input_file: File,
    data_model: str,
    enable_files: bool,  # noqa: FBT001
) -> None:
    """Add a new file to a published record."""
    identity = get_identity("system_process", role_name="admin")
    service = get_records_service(data_model=data_model)

    try:
        record = get_record_or_draft(service, pid, identity)
    except RuntimeError as error:
        secho(error.msg, fg=Color.error)
        return

    files = record.files
    filename = Path(input_file.name).name

    if files.enabled:
        obj = files.get(filename, None)
        if obj is not None:
            secho(
                "File already exists if you want to replace use argument replace-file",
                fg=Color.neutral,
            )
            return

    if not files.enabled and not enable_files:
        secho(
            "Use --enable-files to add files to (metadata-only) record",
            fg=Color.error,
        )
        return

    files.enabled = True  # this allows to also add files to metadata only records
    files.unlock()
    files.create(filename, stream=input_file)
    files.lock()

    record.commit()
    db.session.commit()
    secho("File added successfully.", fg=Color.success)

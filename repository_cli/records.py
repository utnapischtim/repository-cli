# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Management commands for records."""


from click import group

from .generate_commands import create_metadata_cli
from .records import (
    add_category,
    add_file,
    add_identifiers,
    count_records,
    delete_file,
    delete_records,
    list_identifiers,
    list_pids,
    list_records,
    modify_access,
    publish_records,
    replace_file,
    replace_identifiers,
    replace_pid,
    update_records,
)


@group("records")
def group_records() -> None:
    """Management commands for records."""


group_records.add_command(add_category)
group_records.add_command(count_records)
group_records.add_command(delete_records)
group_records.add_command(list_records)
group_records.add_command(modify_access)
group_records.add_command(publish_records)
group_records.add_command(update_records)


@group_records.group("files")
def group_files() -> None:
    """Management comands for record files."""


group_files.add_command(add_file)
group_files.add_command(delete_file)
group_files.add_command(replace_file)


@group_records.group("pids")
def group_pids() -> None:
    """Management commands for record pids."""


group_pids.add_command(list_pids)
group_pids.add_command(replace_pid)


@group_records.group("identifiers")
def group_identifiers() -> None:
    """Management commands for record identifiers."""


group_identifiers.add_command(add_identifiers)
group_identifiers.add_command(list_identifiers)
group_identifiers.add_command(replace_identifiers)

group_records.add_command(create_metadata_cli("lom"))

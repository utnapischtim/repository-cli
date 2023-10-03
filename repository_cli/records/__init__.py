# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Records cli."""


from .files import add as add_file
from .files import delete as delete_file
from .files import replace as replace_file
from .identifiers import add as add_identifiers
from .identifiers import list_identifiers
from .identifiers import replace as replace_identifiers
from .pids import list_pids, replace_pid
from .records import add_category
from .records import count as count_records
from .records import delete as delete_records
from .records import list_records as list_records
from .records import modify_access as modify_access
from .records import publish as publish_records
from .records import update as update_records

__all__ = (
    "add_category",
    "add_file",
    "add_identifiers",
    "count_records",
    "delete_file",
    "delete_records",
    "list_identifiers",
    "list_pids",
    "list_records",
    "modify_access",
    "publish_records",
    "replace_file",
    "replace_identifiers",
    "replace_pid",
    "update_records",
)

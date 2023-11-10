# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Build database update commands from `metadata_class`\\ es."""
from functools import wraps
from inspect import Parameter, signature
from typing import Callable, _UnionGenericAlias

from click import command, group, option, secho
from flask.cli import with_appcontext

from .click_options import option_pid
from .types import Color
from .utils import (
    exists_record,
    get_data,
    get_identity,
    get_metadata_class,
    get_records_service,
    update_record,
)

EMPTY = Parameter.empty  # special emptiness value distinguishable from `None`


def is_union_type(type_):
    """Check whether `type_` is a `typing.Union` of sorts."""
    return isinstance(type_, _UnionGenericAlias)


def build_method_options(method: Callable) -> list:
    """Inspect `method` to build options from its (non-`self`) parameters.

    :return: list of `click` options, one per non-`self` parameter of `method`
    """
    options = []  # to be result
    params_info = signature(method).parameters
    for param_name, param_info in params_info.items():
        option_kwargs = {}  # to be kwargs for the option-decorator to this parameter

        if param_info.default is not EMPTY:
            option_kwargs["default"] = param_info.default
            option_kwargs["show_default"] = True
        else:
            option_kwargs["required"] = True
        if param_info.annotation is not EMPTY and not is_union_type(
            param_info.annotation
        ):
            # click coerces to `type`, which is ambiguous for `typing.Union` types
            # (e.g. which of the classes `A`, `B` should `Union[A, B]` coerce to?)
            # hence such annotations can't be used...
            # type_ = param_info.annotation
            # option_kwargs["type"] = str if type_ == "str" else type_
            # TODO
            option_kwargs["type"] = str

        options.append(option(f"--{param_name.replace('_', '-')}", **option_kwargs))

    # option corresponding to `self`-param is guaranteed to be first, remove it
    # `inspect` handles this the same way (https://github.com/python/cpython/blob/3.11/Lib/inspect.py#L2053)
    options = options[1:]
    return options


def build_update_func(metadata_class, method_name: Callable):
    """Build a JSON-updating function using `metadata_class` internally.

    :param metadata_class: class for updating JSON,
                           will be initialized with to-be-updated JSON
    :param Callable method_name: name of method of `metadata_class` to use for updating
    """

    method = getattr(metadata_class, method_name)

    @wraps(method)
    def update_func(json, **method_kwargs):
        metadata = metadata_class(json, overwritable=True)
        method(metadata, **method_kwargs)
        return metadata.json

    return update_func


def build_command(data_model: str, update_func: Callable, update_options):
    """Build a `click` command that updates JSON in the database.

    :param str model_name: SQL-table to be updated, e.g. `"lom"`
    :param Callable update_func: function to be used to update JSON
    :param list update_options: additional options for the command
                                will be passed to update_func as kwargs
    """

    @option_pid()
    @with_appcontext
    @wraps(update_func)
    def command_func(pid, **update_kwargs):
        service = get_records_service(data_model)
        identity = get_identity(permission_name="system_process", role_name="admin")

        if not exists_record(service, pid, identity):
            secho(f"{pid!r} does not exist or was deleted", fg=Color.error)
            return

        old_json = get_data(service, pid, identity)
        new_json = update_func(old_json, **update_kwargs)
        update_record(service, pid, identity, new_json, old_json)

        secho(f'JSON for pid "{pid}" succesfully updated.', fg=Color.success)

    # `option`s are decorators, which are usually applied via `@my_option` syntax
    # but that's just syntactic sugar for calling `cmd=my_option(cmd)` after `def cmd(...):`
    for update_option in update_options:
        command_func = update_option(command_func)

    return command(command_func)


def create_metadata_cli(data_model):
    """Returns a `click` group with subcommands for `data_model`.

    One subcommand will be generated for every method of the corresponding
    *metadata_class*, if that method's name starts with *set_* or *append_*.

    sample of a metadata-class:

    .. code-block:: python

        class MyModelMetadata:
            def __init__(self, json, overwritable=False):
                # must not mutate passed-in json!
                ...

            def append_some_field(self, kwarg_1, kwarg_2):
                # will have a CLI-command generated from it since name starts with "append_"
                # created command will have required arguments `--kwarg-1` and `--kwarg-2`
                ...

            def set_some_other_field(self, kwarg_3=0):
                # will have a CLI-command generated from it since name starts with "set_"
                # created command will have optional argument --kwarg-3, which defaults to 0
                ...

            def utility_func(self, ...):
                # NO command generated since name neither starts with "append_" nor "set_"
                ...
    """

    @group(
        data_model,
        help=f"Commands computer-generated from {data_model}'s metadata class.",
    )
    def created_group():
        """Group for commands computer-generated for this data model."""

    metadata_class = get_metadata_class(data_model)
    method_names = [
        name
        for name in dir(metadata_class)
        if any(name.startswith(prefix) for prefix in ["append_", "set_"])
    ]
    for method_name in method_names:
        json_update_func = build_update_func(metadata_class, method_name)
        update_options = build_method_options(getattr(metadata_class, method_name))
        generated_command = build_command(data_model, json_update_func, update_options)

        created_group.add_command(generated_command, method_name.replace("_", "-"))

    return created_group

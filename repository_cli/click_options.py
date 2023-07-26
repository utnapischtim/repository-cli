# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Commonly used options for CLI commands."""


from collections.abc import Callable
from typing import Any, TypeVar

from click import BOOL, STRING, Choice, File, option

from .click_param_types import JSON

T = TypeVar("T")


def optional_brackets(func: Callable) -> Callable:
    """With this decorator it is possible to write decorators without ()."""

    def wrapper(*args: dict, **kwargs: dict) -> Any:  # noqa: ANN401
        if len(args) >= 1 and callable(args[0]):
            return func()(args[0])
        return func(*args, **kwargs)

    return wrapper


@optional_brackets
def option_quiet() -> Callable[[T], T]:
    """Get parameter option for quiet."""
    return option(
        "--quiet",
        is_flag=True,
        default=False,
        type=BOOL,
    )


@optional_brackets
def option_jq_filter() -> Callable[[T], T]:
    """Get parameter option for jq filter."""
    return option(
        "--jq-filter",
        default=".",
        type=STRING,
        required=False,
        help="filter for jq",
    )


@optional_brackets
def option_data_model() -> Callable[[T], T]:
    """Get parameter option for data model."""
    return option(
        "--data-model",
        type=Choice(["rdm", "marc21", "lom"]),
        default="rdm",
    )


@optional_brackets
def option_record_type() -> Callable[[T], T]:
    """Get parameter option for record type."""
    return option(
        "--record-type",
        type=Choice(["record", "draft"], case_sensitive=True),
        default="record",
    )


@optional_brackets
def option_identifier(
    required: bool = True,  # noqa: FBT001, FBT002
) -> Callable[[T], T]:
    """Get parameter options for metadata identifier.

    Sample use: --identifier '{ "identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}'
    """
    return option(
        "--identifier",
        "-i",
        required=required,
        type=JSON(validate=["identifier", "scheme"]),
        help="metadata identifier as JSON",
    )


# TODO. rename to option_pid
@optional_brackets
def option_pid_identifier(
    required: bool = True,  # noqa: FBT001, FBT002
) -> Callable[[T], T]:
    """Get parameter options for metadata identifier.

    Sample use: --pid-identifier '{"doi": {"identifier": "10.48436/fcze8-4vx33",
                                           "provider": "unmanaged"}}'
    """
    return option(
        "--pid-identifier",
        required=required,
        type=JSON(),
        help="pid identifier as JSON",
    )


# TODO: rename to option_id, refactore to true concept of the used id
@optional_brackets
def option_pid(
    required: bool = True,  # noqa: FBT001, FBT002
) -> Callable[[T], T]:
    """Get parameter options for record PID.

    Sample use: --pid "fcze8-4vx33"
    """
    return option(
        "--pid",
        "-p",
        metavar="PID_VALUE",
        required=required,
        help="persistent identifier of the object to operate on",
    )


@optional_brackets
def option_input_file(
    required: bool = True,  # noqa: FBT001, FBT002
    type_: File = None,
    name: str = "input_file",
    help_: str = "name of file to read from",
) -> Callable[[T], T]:
    """Get parameter options for input file.

    Sample use: --input-file "input.json"
    """
    if not type_:
        type_ = File("r")
    return option(
        "--input-file",
        name,
        metavar="string",
        required=required,
        help=help_,
        type=type_,
    )


@optional_brackets
def option_output_file(
    required: bool = True,  # noqa: FBT001, FBT002
) -> Callable[[T], T]:
    """Get parameter options for output file.

    Sample use: --output-file "output.json"
    """
    return option(
        "--output-file",
        metavar="string",
        required=required,
        help="name of file to write to",
        type=File("w"),
    )

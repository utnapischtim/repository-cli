# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Commonly used options for CLI commands."""

import click


def option_quiet():
    """Get parameter option for quiet."""
    return click.option(
        "--quiet",
        is_flag=True,
        default=False,
        type=click.BOOL,
    )


def option_jq_filter():
    """Get parameter option for jq filter."""
    return click.option(
        "--jq-filter",
        default=".",
        type=click.STRING,
        required=False,
        help="filter for jq",
    )


def option_data_model():
    """Get parameter option for data model."""
    return click.option(
        "--data-model",
        type=click.Choice(["rdm", "marc21"]),
        default="rdm",
    )


def option_record_type():
    """Get parameter option for record type."""
    return click.option(
        "--record-type",
        type=click.Choice(["record", "draft"], case_sensitive=True),
        default="record",
    )


# -i '{ "identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}'
def option_identifier(required: bool = False):
    """Get parameter options for metadata identifier."""
    return click.option(
        "--identifier",
        "-i",
        required=required,
        help="metadata identifier as JSON",
    )


# --pid-identifier ' { "doi":
#   { "identifier": "10.48436/fcze8-4vx33", "provider": "unmanaged" }
# }'
def option_pid_identifier(required: bool = False):
    """Get parameter options for metadata identifier."""
    return click.option(
        "--pid-identifier",
        "--pid-identifier",
        "pid_identifier",
        required=required,
        help="pid identifier as JSON",
    )


# -p "fcze8-4vx33"
def option_pid(required: bool = False):
    """Get parameter options for record PID."""
    return click.option(
        "--pid",
        "-p",
        metavar="PID_VALUE",
        required=required,
        help="persistent identifier of the object to operate on",
    )


# --if "input.json"
def option_input_file(required: bool = False):
    """Get parameter options for input file."""
    return click.option(
        "--input-file",
        "--if",
        "input_file",
        metavar="string",
        required=required,
        help="name of file to read from",
        type=click.File("r"),
    )


# --of "output.json"
def option_output_file(required: bool = False):
    """Get parameter options for output file."""
    return click.option(
        "--output-file",
        "--of",
        "output_file",
        metavar="string",
        required=required,
        help="name of file to write to",
        type=click.File("w"),
    )

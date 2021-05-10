# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Commonly used options for CLI commands."""

import click


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

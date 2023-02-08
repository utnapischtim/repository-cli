# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Commonly used param types for CLI commands."""


import sys
from json import JSONDecodeError, load
from os.path import isfile

from click import ParamType, secho

from .types import Color


class JSON(ParamType):
    """JSON provides the ability to load a json from a string or a file."""

    name = "JSON"

    def convert(self, value, param, ctx):
        """This method converts the json-file to the dictionary representation."""
        if not isfile(value):
            secho("ERROR - please look up if the file path is correct.", fg=Color.error)
            sys.exit()

        try:
            with open(value, "r", encoding="utf8") as file_pointer:
                obj = load(file_pointer)
            return obj
        except JSONDecodeError as error:
            secho("ERROR - Invalid JSON provided.", fg=Color.error)
            secho(f"  error: {error.args[0]}", fg=Color.error)
            sys.exit()

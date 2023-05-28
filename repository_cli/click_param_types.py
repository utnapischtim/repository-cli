# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Commonly used param types for CLI commands."""


import sys
from json import JSONDecodeError, load
from pathlib import Path
from typing import Any, Optional

from click import Context, Parameter, ParamType, secho

from .types import Color


class JSON(ParamType):
    """JSON provides the ability to load a json from a string or a file."""

    name = "JSON"

    def convert(
        self,
        value: Any,  # noqa: ANN401
        param: Optional["Parameter"],  # noqa: ARG002
        ctx: Optional["Context"],  # noqa: ARG002
    ) -> Any:  # noqa: ANN401
        """The method converts the json-file to the dictionary representation."""
        if not Path(value).is_file():
            secho("ERROR - please look up if the file path is correct.", fg=Color.error)
            sys.exit()

        try:
            with Path(value).open("r", encoding="utf8") as file_pointer:
                obj = load(file_pointer)
        except JSONDecodeError as error:
            secho("ERROR - Invalid JSON provided.", fg=Color.error)
            secho(f"  error: {error.args[0]}", fg=Color.error)
            sys.exit()
        else:
            return obj

# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Commonly used param types for CLI commands."""

from __future__ import annotations

import sys
from json import JSONDecodeError, load, loads
from pathlib import Path
from typing import Any

from click import Context, Parameter, ParamType, secho

from .types import Color


def _error_msg(art: str, key: str) -> str:
    """Construct error message."""
    error_msgs = {
        "validate": f"The given json does not validate, key: '{key}' does not exists",
    }
    return error_msgs[art]


class JSON(ParamType):
    """JSON provides the ability to load a json from a string or a file."""

    name = "JSON"

    def __init__(self, validate: list[str] | None = None) -> None:
        """Construct Json ParamType."""
        self.validate = validate

    def convert(
        self,
        value: Any,  # noqa: ANN401
        param: Parameter | None,  # noqa: ARG002
        ctx: Context | None,  # noqa: ARG002
    ) -> Any:  # noqa: ANN401
        """The method converts the json-file to the dictionary representation."""
        try:
            if Path(value).is_file():
                with Path(value).open("r", encoding="utf8") as file_pointer:
                    obj = load(file_pointer)
            else:
                obj = loads(value)
        except JSONDecodeError as error:
            msg = "ERROR - Invalid JSON provided. Check file path or json string."
            secho(msg, fg=Color.error)
            secho(f"  error: {error.args[0]}", fg=Color.error)
            sys.exit()

        if self.validate:
            for key in self.validate:
                if key not in obj:
                    secho(_error_msg("validate", key), fg=Color.error)
                    sys.exit()

        return obj

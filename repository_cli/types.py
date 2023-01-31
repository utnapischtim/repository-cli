# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Types."""


from dataclasses import dataclass


@dataclass(frozen=True)
class Color:
    """This class is for the output color management."""

    neutral = "black"
    error = "red"
    warning = "yellow"
    abort = "magenta"
    success = "green"
    alternate = ["blue", "cyan"]

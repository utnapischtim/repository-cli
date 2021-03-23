# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CLI utilities for invenioRDM."""

from .ext import RepositoryCli
from .version import __version__

__all__ = ("__version__", "RepositoryCli")

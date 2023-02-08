# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from flask import Flask

from repository_cli import RepositoryCli, __version__


def test_version():
    """Test version import."""
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = RepositoryCli(app)
    assert "repository-cli" in app.extensions

    app = Flask("testapp")
    ext = RepositoryCli()
    assert "repository-cli" not in app.extensions
    ext.init_app(app)
    assert "repository-cli" in app.extensions

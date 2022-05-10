# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

import json

import pytest
from flask import Flask
from flask_babelex import Babel

from repository_cli import RepositoryCli
from repository_cli.cli.records import (
    add_identifier,
    list_identifiers,
    replace_identifier,
)


def test_list_identifiers(app_initialized, create_record):
    runner = app_initialized.test_cli_runner()
    r_id = create_record.id
    response = runner.invoke(list_identifiers, ["--pid", r_id])
    assert response.exit_code == 0
    assert "scheme" in response.output
    assert "identifier" in response.output


def test_list_identifiers_record_not_found(app_initialized):
    runner = app_initialized.test_cli_runner()
    r_id = "this does not exist"
    response = runner.invoke(list_identifiers, ["--pid", r_id])
    assert response.exit_code == 0
    assert "does not exist or is deleted" in response.output


def test_add_identifier(app_initialized, identifier, create_record):
    runner = app_initialized.test_cli_runner()
    r_id = create_record.id
    response = runner.invoke(
        add_identifier, ["--pid", r_id, "--identifier", json.dumps(identifier)]
    )
    assert response.exit_code == 0
    assert f"Identifier for '{r_id}' added" in response.output


def test_add_identifier_scheme_exists(app_initialized, identifier, create_record):
    runner = app_initialized.test_cli_runner()
    r_id = create_record.id
    response = runner.invoke(
        add_identifier, ["--pid", r_id, "--identifier", json.dumps(identifier)]
    )
    assert response.exit_code == 0
    assert f"Identifier for '{r_id}' added" in response.output
    response = runner.invoke(
        add_identifier, ["--pid", r_id, "--identifier", json.dumps(identifier)]
    )
    assert response.exit_code == 0
    assert f"scheme '{identifier['scheme']}' already in identifiers" in response.output


def test_add_identifier_wrong_identifier_type(app_initialized, create_record):
    runner = app_initialized.test_cli_runner()
    r_id = create_record.id
    response = runner.invoke(
        add_identifier, ["--pid", r_id, "--identifier", "this is not a dict"]
    )
    assert response.exit_code == 0
    assert "identifier is not valid JSON" in response.output


def test_add_identifiers_record_not_found(app_initialized, identifier):
    runner = app_initialized.test_cli_runner()
    r_id = "this does not exist"
    response = runner.invoke(
        add_identifier, ["--pid", r_id, "--identifier", json.dumps(identifier)]
    )
    assert response.exit_code == 0
    assert "does not exist or is deleted" in response.output


def test_replace_identifier(app_initialized, create_record):
    runner = app_initialized.test_cli_runner()
    r_id = create_record.id
    new_identifier = create_record["metadata"]["identifiers"][0]
    response = runner.invoke(
        replace_identifier,
        ["--pid", r_id, "--identifier", json.dumps(new_identifier)],
    )
    assert response.exit_code == 0
    assert f"Identifier for '{r_id}' replaced" in response.output


def test_replace_identifier_scheme_does_not_exist(
    app_initialized, identifier, create_record
):
    runner = app_initialized.test_cli_runner()
    r_id = create_record.id
    response = runner.invoke(
        replace_identifier,
        ["--pid", r_id, "--identifier", json.dumps(identifier)],
    )
    assert response.exit_code == 0
    assert f"scheme '{identifier['scheme']}' not in identifiers" in response.output


def test_replace_identifier_wrong_identifier_type(app_initialized, create_record):
    runner = app_initialized.test_cli_runner()
    r_id = create_record.id
    response = runner.invoke(
        replace_identifier,
        ["--pid", r_id, "--identifier", "this is not a dict"],
    )
    assert response.exit_code == 0
    assert "identifier is not valid JSON" in response.output


def test_replace_identifiers_record_not_found(app_initialized, identifier):
    runner = app_initialized.test_cli_runner()
    r_id = "this does not exist"
    response = runner.invoke(
        replace_identifier,
        ["--pid", r_id, "--identifier", json.dumps(identifier)],
    )
    assert response.exit_code == 0
    assert "does not exist or is deleted" in response.output

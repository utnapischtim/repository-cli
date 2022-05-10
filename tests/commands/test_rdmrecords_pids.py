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
import os

import pytest
from flask import Flask
from flask_babelex import Babel

from repository_cli import RepositoryCli
from repository_cli.cli.records import list_pids, replace_pid


def test_list_pids_with_entries(app_initialized, create_record):
    runner = app_initialized.test_cli_runner()
    r_id = create_record.id
    response = runner.invoke(list_pids, ["--pid", r_id])
    assert response.exit_code == 0


def test_list_pids_record_not_found(app_initialized):
    runner = app_initialized.test_cli_runner()
    r_id = "this does not exist"
    response = runner.invoke(list_pids, ["--pid", r_id])
    assert response.exit_code == 0
    assert "does not exist or is deleted" in response.output


def test_replace_pid(app_initialized, pid_identifier, create_record):
    runner = app_initialized.test_cli_runner()
    r_id = create_record.id
    response = runner.invoke(
        replace_pid,
        ["--pid", r_id, "--pid-identifier", json.dumps(pid_identifier)],
    )
    assert response.exit_code == 0
    assert f"'{r_id}', successfully updated" in response.output


def test_replace_pid_pid_does_not_exist(app_initialized, pid_identifier, create_record):
    runner = app_initialized.test_cli_runner()
    r_id = create_record.id
    pid_identifier["unknown_identifier"] = pid_identifier.pop(
        list(pid_identifier.keys())[0]
    )
    response = runner.invoke(
        replace_pid,
        ["--pid", r_id, "--pid-identifier", json.dumps(pid_identifier)],
    )
    assert response.exit_code == 0
    assert "does not have pid identifier" in response.output


def test_replace_pid_wrong_identifier_type(app_initialized, create_record):
    runner = app_initialized.test_cli_runner()
    r_id = create_record.id
    response = runner.invoke(
        replace_pid, ["--pid", r_id, "--pid-identifier", "this is not a dict"]
    )
    assert response.exit_code == 0
    assert "pid_identifier is not valid JSON" in response.output


def test_replace_pid_record_not_found(app_initialized, pid_identifier):
    runner = app_initialized.test_cli_runner()
    r_id = "this does not exist"
    response = runner.invoke(
        replace_pid,
        ["--pid", r_id, "--pid-identifier", json.dumps(pid_identifier)],
    )
    assert response.exit_code == 0
    assert "does not exist or is deleted" in response.output

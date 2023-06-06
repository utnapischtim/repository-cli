# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

import json

from flask import Flask
from invenio_records_resources.services.records.results import RecordItem

from repository_cli.records import list_pids, replace_pid


def test_list_pids_with_entries(
    app_initialized: Flask,
    create_record: RecordItem,
) -> None:
    """Test list pids with entries."""
    runner = app_initialized.test_cli_runner()
    r_id = create_record.id
    response = runner.invoke(list_pids, ["--pid", r_id])
    assert response.exit_code == 0


def test_list_pids_record_not_found(app_initialized: Flask) -> None:
    """Test list pids record not found."""
    runner = app_initialized.test_cli_runner()
    r_id = "this does not exist"
    response = runner.invoke(list_pids, ["--pid", r_id])
    assert response.exit_code == 0
    assert "does not exist or is deleted" in response.output


def test_replace_pid_pid_does_not_exist(
    app_initialized: Flask,
    pid_identifier: dict,
    create_record: RecordItem,
) -> None:
    """Test replace pid pid does not exist."""
    runner = app_initialized.test_cli_runner()
    r_id = create_record.id
    pid_identifier["unknown_identifier"] = pid_identifier.pop(
        list(pid_identifier.keys())[0],
    )
    response = runner.invoke(
        replace_pid,
        ["--pid", r_id, "--pid-identifier", json.dumps(pid_identifier)],
    )
    assert response.exit_code == 0
    assert "does not have pid identifier" in response.output


def test_replace_pid_wrong_identifier_type(
    app_initialized: Flask,
    create_record: RecordItem,
) -> None:
    """Test replace pid wrong identifier type."""
    runner = app_initialized.test_cli_runner()
    r_id = create_record.id
    response = runner.invoke(
        replace_pid,
        ["--pid", r_id, "--pid-identifier", "this is not a dict"],
    )

    expected_error_msg = (
        "ERROR - Invalid JSON provided. Check file path or json string."
    )
    assert response.exit_code == 0
    assert expected_error_msg in response.output


def test_replace_pid_record_not_found(
    app_initialized: Flask,
    pid_identifier: dict,
) -> None:
    """Test replace pid record not found."""
    runner = app_initialized.test_cli_runner()
    r_id = "this does not exist"
    response = runner.invoke(
        replace_pid,
        ["--pid", r_id, "--pid-identifier", json.dumps(pid_identifier)],
    )
    assert response.exit_code == 0
    assert "does not exist or is deleted" in response.output

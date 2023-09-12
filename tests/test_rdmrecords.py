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

from pathlib import Path

from flask import Flask
from invenio_records_resources.services.records.results import RecordItem

from repository_cli.records import (
    count_records,
    delete_draft,
    delete_record,
    group_records,
    list_records,
    update_records,
)


def test_base_command(app: Flask) -> None:
    """Test base command."""
    runner = app.test_cli_runner()
    response = runner.invoke(group_records)
    assert response.exit_code == 0


def test_count_with_entries(
    app_initialized: Flask,
    create_record: RecordItem,  # noqa: ARG001
) -> None:
    """Test count with entries."""
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(count_records)
    assert response.exit_code == 0
    assert "0 records" not in response.output


def test_list_with_entries(app_initialized: Flask, create_record: RecordItem) -> None:
    """Test list with entries."""
    runner = app_initialized.test_cli_runner()
    record = create_record
    r_id = record.id
    title = record.data["metadata"]["title"]
    response = runner.invoke(list_records)
    assert response.exit_code == 0
    assert "0 records" not in response.output
    assert f"{ r_id }" in response.output
    assert f"{ title }" in response.output


def test_list_output_file(app_initialized: Flask) -> None:
    """Test list output file."""
    filename = "out.json"
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(list_records, ["--output-file", filename])
    Path(filename).unlink()
    assert response.exit_code == 0
    assert "0 records" not in response.output
    assert f"records to {filename}" in response.output


def test_update(app_initialized: Flask) -> None:
    """Test update."""
    filename = "out.json"
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(list_records, ["--output-file", filename])
    assert response.exit_code == 0
    assert f"records to {filename}" in response.output

    response = runner.invoke(update_records, ["--input-file", filename])
    Path(filename).unlink()
    assert response.exit_code == 0
    assert "successfully updated" in response.output


def test_update_ill_formatted_file(app_initialized: Flask) -> None:
    """Test update ill formatted file."""
    filename = "out.json"
    with Path(filename).open(mode="w", encoding="utf8") as file_pointer:
        file_pointer.write("not a valid JSON representation")

    runner = app_initialized.test_cli_runner()
    response = runner.invoke(update_records, ["--input-file", filename])

    Path(filename).unlink()

    assert response.exit_code == 0
    assert "ERROR - Invalid JSON provided." in response.output


def test_delete(app_initialized: Flask, create_record: RecordItem) -> None:
    """Test delete."""
    r_id = create_record.id
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(delete_record, ["--pid", r_id])
    assert response.exit_code == 0
    assert f"'{r_id}', soft-deleted" in response.output


def test_delete_draft_success(app_initialized: Flask, create_draft: RecordItem) -> None:
    """Test delete draft success."""
    r_id = create_draft.id
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(delete_draft, ["--pid", r_id])
    assert response.exit_code == 0
    assert f"'{r_id}', deleted draft" in response.output


def test_delete_draft_no_draft(
    app_initialized: Flask,
    create_record: RecordItem,
) -> None:
    """Test delete draft no draft."""
    r_id = create_record.id
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(delete_draft, ["--pid", r_id])
    assert response.exit_code == 0
    assert f"'{r_id}' does not have a draft" in response.output


def test_delete_draft_pid_does_not_exist(app_initialized: Flask) -> None:
    """Test delete draft pid does not exist."""
    r_id = "himbeere"
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(delete_draft, ["--pid", r_id])
    assert response.exit_code == 0
    assert f"'{r_id}' does not exist" in response.output

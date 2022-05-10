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
from repository_cli.cli.records import (
    count_records,
    delete_draft,
    delete_record,
    list_records,
    rdmrecords,
    update_records,
)


def test_base_command(app):
    runner = app.test_cli_runner()
    response = runner.invoke(rdmrecords)
    assert response.exit_code == 0


def test_count_with_entries(app_initialized, create_record):
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(count_records)
    assert response.exit_code == 0
    assert "0 records" not in response.output


def test_list_with_entries(app_initialized, create_record):
    runner = app_initialized.test_cli_runner()
    record = create_record
    r_id = record.id
    title = record.data["metadata"]["title"]
    response = runner.invoke(list_records)
    assert response.exit_code == 0
    assert "0 records" not in response.output
    assert f"{ r_id }" in response.output
    assert f"{ title }" in response.output


def test_list_output_file(app_initialized, create_record):
    filename = "out.json"
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(list_records, ["--of", filename])
    os.remove(filename)
    assert response.exit_code == 0
    assert "0 records" not in response.output
    assert f"records to {filename}" in response.output


def test_update(app_initialized, create_record):
    filename = "out.json"
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(list_records, ["--of", filename])
    assert response.exit_code == 0
    assert f"records to {filename}" in response.output

    response = runner.invoke(update_records, ["--if", filename])
    os.remove(filename)
    assert response.exit_code == 0
    assert "successfully updated" in response.output


def test_update_ill_formatted_file(app_initialized):
    filename = "out.json"
    f = open(filename, mode="w")
    f.write("not a valid JSON representation")
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(update_records, ["--if", filename])
    os.remove(filename)
    assert response.exit_code == 0
    assert "The input file is not a valid JSON File" in response.output


def test_delete(app_initialized, create_record):
    r_id = create_record.id
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(delete_record, ["--pid", r_id])
    assert response.exit_code == 0
    assert f"'{r_id}', soft-deleted" in response.output


def test_delete_draft_success(app_initialized, create_draft):
    r_id = create_draft.id
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(delete_draft, ["--pid", r_id])
    assert response.exit_code == 0
    assert f"'{r_id}', deleted draft" in response.output


def test_delete_draft_no_draft(app_initialized, create_record):
    r_id = create_record.id
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(delete_draft, ["--pid", r_id])
    assert response.exit_code == 0
    assert f"'{r_id}', does not have a draft" in response.output


def test_delete_draft_pid_does_not_exist(app_initialized):
    r_id = "himbeere"
    runner = app_initialized.test_cli_runner()
    response = runner.invoke(delete_draft, ["--pid", r_id])
    assert response.exit_code == 0
    assert f"'{r_id}', does not exist" in response.output

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
from repository_cli.cli.records import (count_records, delete_record,
                                        list_records, rdmrecords,
                                        update_records)


def test_base_command(app):
    runner = app.test_cli_runner()
    response = runner.invoke(rdmrecords)
    assert response.exit_code == 0


def test_count_no_entries(app):
    runner = app.test_cli_runner()
    response = runner.invoke(count_records)
    assert response.exit_code == 0
    assert "0 records" in response.output


def test_count_with_entries(app_initialized):
    runner = app_initialized["app"].test_cli_runner()
    response = runner.invoke(count_records)
    assert response.exit_code == 0
    assert "5 records" in response.output


def test_list_no_entries(app):
    runner = app.test_cli_runner()
    response = runner.invoke(list_records)
    assert response.exit_code == 0
    assert "0 records" in response.output


def test_list_with_entries(app_initialized):
    runner = app_initialized["app"].test_cli_runner()
    records = app_initialized["data"]["rdmrecords"]
    r_id = records[0].id
    title = records[0].data["metadata"]["title"]
    response = runner.invoke(list_records)
    assert response.exit_code == 0
    assert f"{len(records)} records" in response.output
    assert f"{ r_id }" in response.output
    assert f"{ title }" in response.output


def test_list_output_file(app_initialized):
    filename = "out.json"
    records = app_initialized["data"]["rdmrecords"]
    runner = app_initialized["app"].test_cli_runner()
    response = runner.invoke(list_records, ["--of", filename])
    os.remove(filename)
    assert response.exit_code == 0
    assert f"wrote {len(records)} records to {filename}" in response.output


def test_update(app_initialized):
    filename = "out.json"
    records = app_initialized["data"]["rdmrecords"]
    runner = app_initialized["app"].test_cli_runner()
    response = runner.invoke(list_records, ["--of", filename])
    assert response.exit_code == 0
    assert f"wrote {len(records)} records to {filename}" in response.output

    response = runner.invoke(update_records, ["--if", filename])
    os.remove(filename)
    assert response.exit_code == 0
    assert "successfully updated" in response.output


def test_update_ill_formatted_file(app_initialized):
    filename = "out.json"
    f = open(filename, mode="w")
    f.write("not a valid JSON representation")
    records = app_initialized["data"]["rdmrecords"]
    runner = app_initialized["app"].test_cli_runner()
    response = runner.invoke(update_records, ["--if", filename])
    os.remove(filename)
    assert response.exit_code == 0
    assert "The input file is not a valid JSON File" in response.output


def test_delete(app_initialized):
    records = app_initialized["data"]["rdmrecords"]
    r_id = records[0].id
    runner = app_initialized["app"].test_cli_runner()
    response = runner.invoke(delete_record, ["--pid", r_id])
    assert response.exit_code == 0
    assert f"'{r_id}', soft-deleted" in response.output

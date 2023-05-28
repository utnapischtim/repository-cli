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

import os
import shutil
from pathlib import Path

import pytest
from faker import Faker
from flask import Flask
from flask_principal import Identity
from invenio_access.cli import allow_action
from invenio_access.permissions import system_identity, system_process
from invenio_accounts.cli import roles_create
from invenio_app.factory import create_api as _create_api
from invenio_db import db
from invenio_files_rest.models import Location
from invenio_rdm_records.fixtures.demo import create_fake_record
from invenio_rdm_records.proxies import current_rdm_records
from invenio_records_resources.services.records.results import RecordItem
from invenio_vocabularies.proxies import current_service as vocabulary_service
from invenio_vocabularies.records.api import Vocabulary
from invenio_vocabularies.records.models import VocabularyType


@pytest.fixture(scope="module", name="app_config")
def fixture_app_config(app_config: dict) -> dict:
    """Mimic an instance's configuration."""
    app_config["JSONSCHEMAS_HOST"] = "no-use"
    app_config["BABEL_DEFAULT_LOCALE"] = "en"
    app_config["I18N_LANGUAGES"] = [("en", "English"), ("de", "German")]
    app_config[
        "RECORDS_REFRESOLVER_CLS"
    ] = "invenio_records.resolver.InvenioRefResolver"
    app_config[
        "RECORDS_REFRESOLVER_STORE"
    ] = "invenio_jsonschemas.proxies.current_refresolver_store"

    app_config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "sqlite://",
    )
    app_config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app_config["DATADIR"] = "data"

    return app_config


@pytest.fixture(scope="module")
def create_app() -> Flask:
    """Application factory fixture."""
    return _create_api


@pytest.fixture(scope="module", name="app_initialized")
def fixture_app_initialized(
    app: Flask,
    resource_type_item: str,  # noqa: ARG001
) -> Flask:
    """Flask application with data added."""
    datadir = app.config["DATADIR"]
    if Path(datadir).exists():
        shutil.rmtree(datadir)
        Path(datadir).makedir()

    loc = Location(name="local", uri=datadir, default=True)
    db.session.add(loc)
    db.session.commit()

    runner = app.test_cli_runner()
    runner.invoke(roles_create, ["admin"])
    runner.invoke(allow_action, ["superuser-access", "role", "admin"])

    return app


@pytest.fixture(name="create_record")
def fixture_create_record(app_initialized: Flask) -> RecordItem:  # noqa: ARG001
    """Create and publish new record."""
    record_service = current_rdm_records.records_service
    identity = Identity(1)
    identity.provides.add(system_process)

    record_json = minimal_record()
    record_json["metadata"]["identifiers"] = [
        {"identifier": "ark:/123/456", "scheme": "ark"},
    ]

    rec = record_service.create(data=record_json, identity=identity)
    record_service.publish(id_=rec.id, identity=identity)

    return rec


@pytest.fixture()
def create_draft(
    app_initialized: Flask,  # noqa: ARG001
    create_record: RecordItem,
) -> RecordItem:
    """Create draft for record."""
    record_service = current_rdm_records.records_service
    identity = Identity(1)
    identity.provides.add(system_process)

    return record_service.edit(id_=create_record.id, identity=identity)


def minimal_record() -> dict:
    """Minimal record data as dict coming from the external world.

    https://github.com/inveniosoftware/invenio-rdm-records/blob/aa575a4f8b1beb4d24a448067b649d6f0b8c085e/tests/conftest.py#L279
    """
    return {
        "pids": {},
        "access": {
            "record": "public",
            "files": "public",
        },
        "files": {
            "enabled": False,  # Most tests don't care about files
        },
        "metadata": {
            "publication_date": "2020-06-01",
            "resource_type": {"id": "image-photo"},
            "creators": [
                {
                    "person_or_org": {
                        "family_name": "Brown",
                        "given_name": "Troy",
                        "type": "personal",
                    },
                },
                {
                    "person_or_org": {
                        "name": "Troy Inc.",
                        "type": "organizational",
                    },
                },
            ],
            "title": "A Romans story",
        },
    }


def fake_record() -> dict:
    """Create fake record and replace date.

    As date ranges (e.g. 1968-08-20/2020-11) don't work yet.
    """
    record_json = create_fake_record()
    fake = Faker()
    date_pattern = ["%Y", "%m", "%d"]
    new_date = fake.date("-".join(date_pattern))
    record_json["metadata"]["publication_date"] = new_date

    return record_json


@pytest.fixture()
def identifier() -> dict:
    """Create identifier for test cases."""
    return {"identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}


@pytest.fixture()
def pid_identifier() -> dict:
    """Create pid identifier for test cases."""
    return {"doi": {"identifier": "10.48436/fcze8-4vx33", "provider": "unmanaged"}}


@pytest.fixture(scope="module", name="resource_type_type")
def fixture_resource_type_type(app: Flask) -> VocabularyType:  # noqa: ARG001
    """Resource type vocabulary type.

    https://github.com/inveniosoftware/invenio-rdm-records/blob/aa575a4f8b1beb4d24a448067b649d6f0b8c085e/tests/conftest.py#L398
    """
    return vocabulary_service.create_type(system_identity, "resourcetypes", "rsrct")


@pytest.fixture(scope="module", name="resource_type_item")
def fixture_resource_type_item(
    app: Flask,  # noqa: ARG001
    resource_type_type: str,  # noqa: ARG001
) -> VocabularyType:
    """Resource type vocabulary record.

    https://github.com/inveniosoftware/invenio-rdm-records/blob/aa575a4f8b1beb4d24a448067b649d6f0b8c085e/tests/conftest.py#L405
    """
    vocab = vocabulary_service.create(
        system_identity,
        {
            "id": "image-photo",
            "icon": "chart bar outline",
            "props": {
                "csl": "graphic",
                "datacite_general": "Image",
                "datacite_type": "Photo",
                "eurepo": "info:eu-repo/semantic/image-photo",
                "openaire_resourceType": "25",
                "openaire_type": "dataset",
                "schema.org": "https://schema.org/Photograph",
                "subtype": "image-photo",
                "type": "image",
            },
            "title": {"en": "Photo"},
            "tags": ["depositable", "linkable"],
            "type": "resourcetypes",
        },
    )

    Vocabulary.index.refresh()

    return vocab

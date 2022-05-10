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

import os
import shutil
import tempfile

import pytest
from faker import Faker
from flask import Flask
from flask_babelex import Babel
from flask_principal import Identity
from invenio_access.cli import allow_action
from invenio_access.permissions import any_user, system_identity, system_process
from invenio_accounts.cli import roles_create
from invenio_app.factory import create_app as create_rdm_app
from invenio_db import db
from invenio_files_rest.models import Location
from invenio_rdm_records.cli import create_fake_record
from invenio_rdm_records.proxies import current_rdm_records
from invenio_vocabularies.proxies import current_service as vocabulary_service
from invenio_vocabularies.records.api import Vocabulary
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

from repository_cli import RepositoryCli


@pytest.fixture(scope="module")
def celery_config():
    """Override pytest-invenio fixture.

    TODO: Remove this fixture if you add Celery support.
    """
    return {}


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""

    def factory(**config):
        app = Flask("testapp", instance_path=instance_path)
        app.config.update(**config)
        Babel(app)
        RepositoryCli(app)
        app.register_blueprint(blueprint)
        return app

    return factory


@pytest.fixture(scope="module")
def app(request):
    """Basic Flask application."""
    instance_path = tempfile.mkdtemp()
    app = create_rdm_app()
    DB = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite://")
    app.config.update(
        I18N_LANGUAGES=[("en", "English"), ("de", "German")],
        SQLALCHEMY_DATABASE_URI=DB,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        DATADIR="data",
    )

    RepositoryCli(app)

    app.config[
        "RECORDS_REFRESOLVER_CLS"
    ] = "invenio_records.resolver.InvenioRefResolver"
    app.config[
        "RECORDS_REFRESOLVER_STORE"
    ] = "invenio_jsonschemas.proxies.current_refresolver_store"

    # Variable not used. We set it to silent warnings
    app.config["JSONSCHEMAS_HOST"] = "not-used"

    with app.app_context():
        db_url = str(db.engine.url)
        if db_url != "sqlite://" and not database_exists(db_url):
            create_database(db_url)
        db.create_all()

    def teardown():
        with app.app_context():
            db_url = str(db.engine.url)
            db.session.close()
            if db_url != "sqlite://":
                drop_database(db_url)
            shutil.rmtree(instance_path)

    request.addfinalizer(teardown)
    app.test_request_context().push()

    return app


@pytest.fixture(scope="module")
def app_initialized(app, resource_type_item):
    """Flask application with data added."""
    d = app.config["DATADIR"]  # folder `data`

    if os.path.exists(d):
        shutil.rmtree(d)
        os.makedirs(d)

    loc = Location(name="local", uri=d, default=True)
    db.session.add(loc)
    db.session.commit()

    runner = app.test_cli_runner()
    runner.invoke(roles_create, ["admin"])
    runner.invoke(allow_action, ["superuser-access", "role", "admin"])

    return app


@pytest.fixture()
def create_record(app_initialized):
    """Create and publish new record."""
    record_service = current_rdm_records.records_service
    identity = Identity(1)
    identity.provides.add(system_process)

    record_json = minimal_record()
    record_json["metadata"]["identifiers"] = [
        {"identifier": "ark:/123/456", "scheme": "ark"}
    ]

    rec = record_service.create(data=record_json, identity=identity)
    record_service.publish(id_=rec.id, identity=identity)

    return rec


@pytest.fixture()
def create_draft(app_initialized, create_record):
    """Create draft for record."""
    record_service = current_rdm_records.records_service
    identity = Identity(1)
    identity.provides.add(system_process)

    draft = record_service.edit(id_=create_record.id, identity=identity)
    return draft


def minimal_record():
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
                    }
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


def fake_record():
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
def identifier():
    """Create identifier for test cases."""
    identifier = {"identifier": "10.48436/fcze8-4vx33", "scheme": "doi"}

    return identifier


@pytest.fixture()
def pid_identifier():
    """Create pid identifier for test cases."""
    pid_identifier = {
        "doi": {"identifier": "10.48436/fcze8-4vx33", "provider": "unmanaged"}
    }
    return pid_identifier


@pytest.fixture(scope="module")
def resource_type_type(app):
    """Resource type vocabulary type.

    https://github.com/inveniosoftware/invenio-rdm-records/blob/aa575a4f8b1beb4d24a448067b649d6f0b8c085e/tests/conftest.py#L398
    """
    return vocabulary_service.create_type(system_identity, "resource_types", "rsrct")


@pytest.fixture(scope="module")
def resource_type_item(app, resource_type_type):
    """Resource type vocabulary record.

    https://github.com/inveniosoftware/invenio-rdm-records/blob/aa575a4f8b1beb4d24a448067b649d6f0b8c085e/tests/conftest.py#L405
    """
    vocab = vocabulary_service.create(
        system_identity,
        {
            "id": "image-photo",
            "props": {
                "csl": "graphic",
                "datacite_general": "Image",
                "datacite_type": "Photo",
                "openaire_resourceType": "25",
                "openaire_type": "dataset",
                "schema.org": "https://schema.org/Photograph",
                "subtype": "image-photo",
                "subtype_name": "Photo",
                "type": "image",
                "type_icon": "chart bar outline",
                "type_name": "Image",
            },
            "title": {"en": "Photo"},
            "type": "resource_types",
        },
    )

    Vocabulary.index.refresh()

    return vocab

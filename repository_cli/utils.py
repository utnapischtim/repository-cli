# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Commonly used utility functions."""
from typing import Optional

from flask_principal import Identity, RoleNeed
from invenio_access.permissions import any_user, system_process
from invenio_accounts import current_accounts
from invenio_db import db
from invenio_drafts_resources.records.api import Draft
from invenio_rdm_records.proxies import current_rdm_records
from invenio_rdm_records.records.models import RDMDraftMetadata, RDMRecordMetadata
from invenio_records_marc21 import current_records_marc21
from invenio_records_marc21.records import DraftMetadata as Marc21DraftMetadata
from invenio_records_marc21.records import RecordMetadata as Marc21RecordMetadata
from invenio_records_resources.services import RecordService


def get_identity(permission_name: str = "any_user", role_name: str = None) -> Identity:
    """Get an identity to perform tasks.

    Default permission is "any_user"
    """
    identity = Identity(0)
    permission = any_user
    if permission_name == "system_process":
        permission = system_process

    if role_name:
        role = current_accounts.datastore.find_role(role_name)
        if role:
            identity.provides.add(RoleNeed(role_name))
        else:
            raise Exception(f"Role {role_name} does not exist")

    identity.provides.add(permission)
    return identity


def get_draft(pid: str, identity: Identity) -> Optional[Draft]:
    """Get current draft of record.

    None will be returned if there is no draft.
    """
    service = get_records_service()

    # check if record exists
    service.read(id_=pid, identity=identity)

    draft = None
    try:
        draft = service.read_draft(id_=pid, identity=identity)
    except Exception:
        pass

    return draft


def get_records_service(data_model="rdm") -> RecordService:
    """Get records service."""
    available_services = {
        "rdm": current_rdm_records.records_service,
        "marc21": current_records_marc21.records_service,
    }

    return available_services.get(data_model, current_rdm_records.records_service)


def get_metadata_model(
    data_model: str = "rdm", record_type: str = "record"
) -> db.Model:
    """Get the record model."""
    available_models = {
        "record": {
            "rdm": RDMRecordMetadata,
            "marc21": Marc21RecordMetadata,
        },
        "draft": {
            "rdm": RDMDraftMetadata,
            "marc21": Marc21DraftMetadata,
        },
    }

    try:
        _type = available_models.get(record_type)
    except KeyError:
        raise RuntimeError("the used record_type should be of the list [record, draft]")

    try:
        return _type.get(data_model)
    except KeyError:
        raise RuntimeError("the used data_model should be of the list [rdm, marc21]")


def update_record(pid: str, identity: Identity, new_data, old_data) -> None:
    """Update record with new data.

    If there is an error during publishing, the record will be set back
    WARNING: If there is an unpublished draft, the data of it will be lost.
    """
    service = get_records_service()
    if not get_draft(pid, identity):
        service.edit(id_=pid, identity=identity)

    try:
        service.update_draft(id_=pid, identity=identity, data=new_data)
        service.publish(id_=pid, identity=identity)
    except Exception as e:
        service.update_draft(id_=pid, identity=identity, data=old_data)
        raise e


def record_exists(pid: str) -> bool:
    """Check if record exists and is not deleted."""
    service = get_records_service()
    identity = get_identity()
    try:
        service.read(id_=pid, identity=identity)
    except Exception:
        return False

    return True

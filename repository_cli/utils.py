# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2023 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Commonly used utility functions."""
from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from flask_principal import Identity, RoleNeed
from invenio_access.permissions import any_user, system_process
from invenio_accounts import current_accounts
from invenio_rdm_records.proxies import current_rdm_records
from invenio_rdm_records.records.models import RDMDraftMetadata, RDMRecordMetadata
from invenio_records_lom import current_records_lom
from invenio_records_lom.records.models import LOMDraftMetadata, LOMRecordMetadata
from invenio_records_lom.utils.metadata import LOMMetadata
from invenio_records_marc21 import Marc21Metadata, current_records_marc21
from invenio_records_marc21.records import DraftMetadata as Marc21DraftMetadata
from invenio_records_marc21.records import RecordMetadata as Marc21RecordMetadata
from sqlalchemy.orm.exc import NoResultFound

if TYPE_CHECKING:
    from invenio_db import db
    from invenio_drafts_resources.records.api import Draft, Record
    from invenio_records_resources.services import RecordService
    from invenio_records_resources.services.records.results import RecordItem

BELOW_CONTROLFIELD = 10


class IdentityNotFoundError(Exception):
    """Identity not found exception."""

    def __init__(self, role: str) -> None:
        """Construct IdentityNotFound."""
        msg = f"Role {role} does not exist"
        super().__init__(msg)


def get_identity(
    permission_name: str = "any_user",
    role_name: str | None = None,
) -> Identity:
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
            raise IdentityNotFoundError(role=role_name)

    identity.provides.add(permission)
    return identity


def get_record_item(service: RecordService, pid: str, identity: Identity) -> RecordItem:
    """Get record item."""
    try:
        record_item = service.read(id_=pid, identity=identity)
    except NoResultFound:
        try:
            record_item = service.read_draft(id_=pid, identity=identity)
        except NoResultFound as exc:
            msg = f"Record ({pid}) does not exists"
            raise RuntimeError(msg) from exc
    return record_item


def get_data(service: RecordService, pid: str, identity: Identity) -> dict:
    """Get data."""
    return get_record_item(service, pid, identity).data


def get_record_or_draft(
    service: RecordService,
    pid: str,
    identity: Identity,
) -> Draft | Record:
    """Get record or draft."""
    return get_record_item(service, pid, identity)._record


def get_records_service(data_model: str = "rdm") -> RecordService:
    """Get records service."""
    available_services = {
        "rdm": current_rdm_records.records_service,
        "marc21": current_records_marc21.records_service,
        "lom": current_records_lom.records_service,
    }

    return available_services.get(data_model, current_rdm_records.records_service)


def get_metadata_model(
    data_model: str = "rdm",
    record_type: str = "record",
) -> db.Model:
    """Get the record model."""
    available_models = {
        "record": {
            "rdm": RDMRecordMetadata,
            "marc21": Marc21RecordMetadata,
            "lom": LOMRecordMetadata,
        },
        "draft": {
            "rdm": RDMDraftMetadata,
            "marc21": Marc21DraftMetadata,
            "lom": LOMDraftMetadata,
        },
    }

    try:
        type_ = available_models[record_type]
    except KeyError as exc:
        msg = "the used record_type should be of the list [record, draft]"
        raise RuntimeError(msg) from exc

    try:
        return type_[data_model]
    except KeyError as exc:
        msg = "the used data_model should be of the list [rdm, marc21, lom]"
        raise RuntimeError(msg) from exc


def get_metadata_class(data_model: str):
    """Get the metadata class."""
    available_metadata_classes = {
        "lom": LOMMetadata,
    }
    try:
        return available_metadata_classes[data_model]
    except KeyError as exc:
        msg = f"the used data_model should be in [{', '.join(available_metadata_classes)}]"
        raise RuntimeError(msg) from exc


def update_record(
    service: RecordService,
    pid: str,
    identity: Identity,
    new_data: dict,
    old_data: dict,
) -> None:
    """Update record with new data.

    If there is an error during publishing, the record will be set back
    WARNING: If there is an unpublished draft, the data of it will be lost.
    """
    do_publish = False
    if not exists_draft(service, pid, identity):
        service.edit(id_=pid, identity=identity)
        do_publish = True

    try:
        service.update_draft(id_=pid, identity=identity, data=new_data)
        if do_publish:
            service.publish(id_=pid, identity=identity)
    except Exception as error:
        service.update_draft(id_=pid, identity=identity, data=old_data)
        raise error  # noqa: TRY201


def add_metadata_to_marc21_record(metadata: dict, addition: dict) -> dict:
    """Add fields to marc21 record."""
    marc21 = Marc21Metadata(json=metadata["metadata"])

    for field_number, fields in addition["metadata"]["fields"].items():
        if int(field_number) < BELOW_CONTROLFIELD:
            marc21.emplace_controlfield(field_number, fields)
        else:
            for field in fields:
                selector = f"{field_number}.{field['ind1']}.{field['ind2']}."
                marc21.emplace_datafield(selector, subfs=field["subfields"])

    metadata.update(marc21.json)
    return metadata


def exists_record(service: RecordService, pid: str, identity: Identity) -> bool:
    """Check if record exists and is not deleted."""
    try:
        service.read(id_=pid, identity=identity)
    except Exception:
        return False

    return True


def exists_draft(service: RecordService, pid: str, identity: Identity) -> bool:
    """Check if draft exists."""
    try:
        service.read_draft(id_=pid, identity=identity)
    except Exception:
        return False
    return True

# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Commonly used utility functions."""

from flask_principal import Identity, RoleNeed
from invenio_access.permissions import any_user, system_process
from invenio_accounts import current_accounts
from invenio_admin.permissions import action_admin_access
from invenio_rdm_records.proxies import current_rdm_records


def get_identity(permission_name="any_user", role_name=None):
    """Get an identity to perform tasks.

    Default is "any_user"
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


def get_draft(pid, identity):
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


def get_records_service():
    """Get records service."""
    return current_rdm_records.records_service


def update_record(pid, identity, should_publish, new_data, old_data):
    """Update record with new data.

    If it was published before, it should be published again.
    If it had a draft, it should not be published.
    If an error occurs, revert record to previous state.

    """
    service = get_records_service()
    try:
        service.update_draft(id_=pid, identity=identity, data=new_data)
        if should_publish:
            service.publish(id_=pid, identity=identity)
    except Exception as e:
        if should_publish:
            service.delete_draft(id_=pid, identity=identity)
        else:
            service.update_draft(id_=pid, identity=identity, data=old_data)
        raise e

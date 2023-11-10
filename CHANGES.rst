..
    Copyright (C) 2021 Graz University of Technology.

    repository-cli is free software; you can redistribute it and/or modify
    it under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version v0.11.1 (release 2023-11-10)

- cli: tmp fix, this should be revisited
- setup: increase rdm version


Version v0.11.0 (release 2023-11-03)

- add command for adding persistent identifiers


Version v0.10.0 (release 2023-09-12)

- add way to generate commands that update JSON
- refactor: delete-draft
- test: improve run-tests.sh
- setup: use pytest-black-ng instead of pytest-black
- fix: logic error
- fix: can't return draft without existing record
- fix: cli delete-draft


Version v0.9.0 (release 2023-07-31)

- records: add data_model parameter
- typing: use new optional syntax
- service: add lom service
- global: update ruff


Version v0.8.1 (release 2023-06-07)

- refactor: move json validation into JSON
- refactor: get_record_or_draft


Version v0.8.0 (release 2023-06-01)

- records: make arguments ready for drafts too
- records: add argument delete-file


Version v0.7.0 (release 2023-05-30)

- test: fix and pin due flask-babelex
- records: separate replace-file from add-file
- fix: black color on black background, bad
- types: otherwise it is not working with 3.9
- global: migrate to ruff


Version v0.6.0 (release 2023-05-01)

- cli: add command publish
- cli: add record_id parameter to modify-access


Version v0.5.0 (release 2023-03-08)

- setup: remove python 3.11
- records: add command modify-access
- records: change add-file command to common pattern


Version v0.4.0 (release 2023-02-09)

- setup: add pylint and bandit
- feature: add parameter add-metadata-to-records
- refactor: add decorator without brackets
- refactor: remove two character long forms
- change: empty output not shown for list
- change: command list output_file required=False
- refactor:
- refactor: make count datamodel independent
- refactor: removed directory cli


Version v0.3.1 (release 2023-02-01)

- setup: move jq and tabulate to install require


Version v0.3.0 (release 2023-01-31)

- improve: add explicit raised RuntimeError
- record: add parameters to list_records
- users: change to table output
- refactor: add Color class
- refactor
- fix: tests


Version v0.2.0 (release 2023-01-20)

- add files enabled check
- add data_model param and marc21 service
- add add_file command
- setup: update to newer infrastructure
- add .git-blame-ignore-revs
- migrate to use black as opinionated auto formater
- migrate setup.py to setup.cfg
- feature: add delete-draft command
- dep: bump invenio_app_rdm (#27)
- tests: add test cases for cli commands (#25)
- cli: adds command for pids
- Rename records command (#23)
- bugfix: build readthedocs doc: setup documentation for click commands closes #14
- global: cleanup
- global: refactor comments/strings.
- cli: show number of rdmrecords.


Version 0.1.0 (released TBD)

- Initial public release.

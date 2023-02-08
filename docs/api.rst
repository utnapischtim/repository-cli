..
   Copyright (C) 2021 Graz University of Technology.

   repository-cli is free software; you can redistribute it and/or modify
   it under the terms of the MIT License; see LICENSE file for more details.


API Docs
========

.. automodule:: repository_cli.ext
   :members:

CLI Commands
------------

.. click:: repository_cli.records:group_records
   :prog: invenio repository records
   :nested: full
   :commands: count, list, update, delete

.. click:: repository_cli.records:group_identifiers
   :prog: invenio repository records identifiers
   :nested: full

.. click:: repository_cli.records:group_pids
   :prog: invenio repository records pids
   :nested: full

Utility functions
------------------

.. automodule:: repository_cli.utils
   :members:

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

.. click:: repository_cli.cli.records:rdmrecords
   :prog: invenio repository rdmrecords
   :nested: full
   :commands: count, list, update, delete

.. click:: repository_cli.cli.records:identifiers
   :prog: invenio repository rdmrecords identifiers
   :nested: full

.. click:: repository_cli.cli.records:pids
   :prog: invenio repository rdmrecords pids
   :nested: full

Utility functions
------------------

.. automodule:: repository_cli.cli.util
   :members:

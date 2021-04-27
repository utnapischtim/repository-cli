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

.. click:: repository_cli.cli.records:records
   :prog: invenio repository records
   :nested: full
   :commands: count, list

.. click:: repository_cli.cli.records:identifiers
   :prog: invenio repository records identifiers
   :nested: full


Utility functions
------------------

.. automodule:: repository_cli.cli.util
   :members:

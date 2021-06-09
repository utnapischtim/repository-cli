# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Graz University of Technology.
#
# repository-cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CLI utilities for TU Graz Repository."""

import os

from setuptools import find_packages, setup

readme = open("README.rst").read()
history = open("CHANGES.rst").read()

tests_require = [
    "pytest-invenio>=1.4.0",
    "invenio_app_rdm==4.0.1",
]

# Should follow inveniosoftware/invenio versions
invenio_search_version = ">=1.4.1,<1.5.0"
invenio_db_version = ">=1.0.8,<1.1.0"

extras_require = {
    "elasticsearch7": [
        f"invenio-search[elasticsearch7]{invenio_search_version}"
    ],
    "mysql": [f"invenio-db[mysql,versioning]{invenio_db_version}"],
    "postgresql": [f"invenio-db[postgresql,versioning]{invenio_db_version}"],
    "sqlite": [f"invenio-db[versioning]{invenio_db_version}"],
    "docs": [
        "Sphinx>=3",
        "sphinx-click>=2.5.0"
    ],
    "tests": tests_require,
}

extras_require["all"] = []
for name, reqs in extras_require.items():
    if name[0] == ":" or name in (
        "elasticsearch7",
        "mysql",
        "postgresql",
        "sqlite",
    ):
        continue
    extras_require["all"].extend(reqs)


setup_requires = [
    "Babel>=2.8",
]

install_requires = [
    "click>=7.1.1,<8.0",
    "invenio-rdm-records>=0.30.4,<0.31.0",
    "flask>=1.1,<2.0",
    "invenio-records-resources<0.16.0,>=0.15.2"

    # TODO: https://github.com/tu-graz-library/repository-cli/issues/22 : Should be solved via this issue
    "elasticsearch>=7.0.0,<8.0.0",
    "elasticsearch_dsl>=7.2.1",
    "SQLAlchemy-Continuum>=1.3.11",
    "SQLAlchemy<1.4.0",
    "SQLAlchemy-Utils<0.36,>=0.33.1"
    "invenio_search>=1.4.0,<2.0.0",
    "psycopg2-binary>=2.8.6",
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join("repository_cli", "version.py"), "rt") as fp:
    exec(fp.read(), g)
    version = g["__version__"]

setup(
    name="repository-cli",
    version=version,
    description=__doc__,
    long_description=readme + "\n\n" + history,
    keywords="invenio repository cli",
    license="MIT",
    author="Graz University of Technology",
    author_email="info@tugraz.at",
    url="https://github.com/tu-graz-library/repository-cli",
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    entry_points={
        "flask.commands": ["repository = repository_cli.cli:utilities"],
        "invenio_base.apps": [
            "repository_cli = repository_cli:RepositoryCli",
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Development Status :: 1 - Planning",
    ],
)

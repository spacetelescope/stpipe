Writing news fragments for the change log
#########################################

This ``changes/`` directory contains "news fragments": small reStructuredText (`.rst`) files describing a change in a few sentences.
When making a release, run ``towncrier build --version <VERSION>`` to consume existing fragments in ``changes/`` and insert them as a full change log entry at the top of ``CHANGES.rst`` for the released version.

News fragment filenames consist of the pull request number and the change log category (see below). A single change can have more than one news fragment.

Change log categories
*********************

- ``<PR#>.feature.rst``: new feature
- ``<PR#>.bugfix.rst``: fixes an issue
- ``<PR#>.doc.rst``: documentation change
- ``<PR#>.removal.rst``: deprecation or removal of public API
- ``<PR#>.misc.rst``: infrastructure or miscellaneous change

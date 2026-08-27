# Writing News Fragments for the Changelog

This `changes/` directory contains "news fragments": small reStructuredText (`.rst`) files describing a change in a few sentences.
When making a release, run `towncrier build --version <VERSION>` to consume existing fragments in `changes/`
and insert them as a full changelog entry at the top of `CHANGES.rst` for the released version.

News fragment filenames consist of the pull request number and the changelog category (see below).
A single change can have more than one news fragment, if it spans multiple categories.

Refer to `towncrier.toml` for categories.

<!-- If this PR addresses a JIRA ticket: -->
<!-- Resolves [JP-nnnn](https://jira.stsci.edu/browse/JP-nnnn) -->
<!-- Resolves [RCAL-nnnn](https://jira.stsci.edu/browse/RCAL-nnnn) -->

<!-- If this PR will close an existing GitHub issue (that is not already attached to a JIRA ticket): -->
<!-- Closes # -->

<!-- Describe your changes here: -->

## Description

This change ...

<!-- If you can't perform these tasks due to permissions, reach out to a maintainer. -->

## Tasks

- [ ] update or add relevant tests
- [ ] update relevant docstrings and / or `docs/` page
- [ ] If this change affects user-facing code or public API, add news fragment file(s) to `changes/` (see [the changelog instructions](https://github.com/spacetelescope/stpipe/blob/main/changes/README.md)).
      Otherwise, add the `no-changelog-entry-needed` label.
  - [ ] run regression tests with this branch installed (`stpipe@git+https://github.com/<fork>/stpipe.git@<branch>`)
    - [ ] [`jwst` regression test](https://github.com/spacetelescope/RegressionTests/actions/workflows/jwst.yml)
    - [ ] [`romancal` regression test](https://github.com/spacetelescope/RegressionTests/actions/workflows/romancal.yml)

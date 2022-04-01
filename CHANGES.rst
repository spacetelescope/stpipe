0.3.2 (unreleased)
==================

- Pass header-only model to steps for CRDS fetching to reduce memory usage [#38]

- Ensure product header is passed for CRDS fetching instead of empty
  ModelContainer header [#50]

0.3.1 (2021-11-12)
==================

- Fig a bug that prevented support for list arguments. [#33]

- Add keyword 'logcfg' to Step.call() to set logging configuration. [#32]

- Add Step.log_records to make log output available to subclasses. [#35]

0.3.0 (2021-10-11)
==================

- Change ConfigObj.update() to merge() when combining user-provided
  config_file and step-specific flags during a step.call() to properly
  merge dicts of step flags [#22]

- Drop the ``stspec`` command-line tool, which is no longer relevant
  now that config files are stored in ASDF format.  See ``strun --save-parameters``
  or the ``Step.export_config`` method for options for generating
  ASDF config files. [#25]

- Prevent ConfigObj from treating DataModel as a config section. [#26]

- Added Step class attribute ``name_format`` to provide Steps control over
  output filename formatting by using an input format string rather than
  the default formatting. [#29]

- Fix wiping out substep parameters settings when using Step.call [#28]

0.2.1 (2021-08-26)
==================

- Workaround for setuptools_scm issues with recent versions of pip. [#27]

0.2.0 (2021-04-22)
==================

- Remove the default value of ``output_ext`` so subclsses can define it. [#17]

- Remove specific dependency on stdatamodels DataModel class. [#20]

0.1.0 (2021-02-08)
==================

- Create package and import code from jwst.stpipe. [#2, #11, #12]

- Create new CLI infrastructure and implement 'stpipe list'. [#14]

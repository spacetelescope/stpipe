0.4.2 (unreleased)
==================

- Refactored ``Step.crds_get_config_from_reference`` and
  ``Pipeline.get_config_from_reference`` to reduce memory when the input to
  a pipeline is an association file, i.e. a ``ModelContainer``. In this case
  the crds parameters are retrieved from the first model which is already opened. [#63]

0.4.1 (2022-07-14)
==================

- Add special behavior for ModelContainers during setting of skipped steps'
  meta keyword [#62]

0.4.0 (2022-07-05)
==================

- Update astropy min version to 5.0.4. [#52]

- Update datamodel with 'SKIPPED' status when step.skip set to True [#53]

- Update CI workflows to cache test environments and depend upon style and security checks [#55, #58]

- Correctly handle config merges of default spec, any possible step-pars files (from
  CRDS or the user), and either command line (for strun) or step parameter dictionary (for interactive
  session Pipeline.call()) parameter specifications [#57]

- Remove log dump of any CRDS-retrieved PARS-reference files [#60]

0.3.3 (2022-04-07)
==================

- Ensure product header is passed for CRDS fetching instead of empty
  ModelContainer header [#50]

0.3.2 (2022-03-29)
==================

- Pass header-only model to steps for CRDS fetching to reduce memory usage [#38]

- For classmethods, use the delegator logger. [#37]

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

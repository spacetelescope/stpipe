0.3.0 (unreleased)
==================

- Change ConfigObj.update() to merge() when combining user-provided
  config_file and step-specific flags during a step.call() to properly
  merge dicts of step flags [#22]

- Drop the ``stspec`` command-line tool, which is no longer relevant
  now that config files are stored in ASDF format.  See ``strun --save-parameters``
  or the ``Step.export_config`` method for options for generating
  ASDF config files. [#25]

- Prevent ConfigObj from treating DataModel as a config section. [#26]

0.2.0 (2021-04-22)
==================

- Remove the default value of ``output_ext`` so subclsses can define it. [#17]

- Remove specific dependency on stdatamodels DataModel class. [#20]

0.1.0 (2021-02-08)
==================

- Create package and import code from jwst.stpipe. [#2, #11, #12]

- Create new CLI infrastructure and implement 'stpipe list'. [#14]

0.10.0 (2025-07-10)
===================

Bug Fixes
---------

- Fix logging for python 3.13.4 and 3.13.5 by removing delegation. (`#240
  <https://github.com/spacetelescope/stpipe/issues/240>`_)


0.9.0 (2025-06-18)
==================

Bug Fixes
---------

- Record the full path to custom reference files (`#234
  <https://github.com/spacetelescope/stpipe/issues/234>`_)
- Fixed non-deterministic ordering of unused keys passed into
  ``FormatTemplate`` that manifested when user-provided output template was
  incomplete. (`#235 <https://github.com/spacetelescope/stpipe/issues/235>`_)


New Features
------------

- Add ``Step._get_crds_parameters`` to allow subclasses to override parameter
  determination. (`#229
  <https://github.com/spacetelescope/stpipe/issues/229>`_)
- Force skip=False when step is run standalone (`#230
  <https://github.com/spacetelescope/stpipe/issues/230>`_)


Deprecations and Removals
-------------------------

- Remove the deprecated ``Step.__call__`` method. (`#239
  <https://github.com/spacetelescope/stpipe/issues/239>`_)


0.8.1 (2025-03-19)
==================

Bug Fixes
---------

- Fix pre-hooks by wrapping hook results in a tuple. (`#214
  <https://github.com/spacetelescope/stpipe/issues/214>`_)
- Allow hooks to save to non-fits files. (`#217
  <https://github.com/spacetelescope/stpipe/issues/217>`_)


Misc
----

- test with latest supported Python version (`#222
  <https://github.com/spacetelescope/stpipe/issues/222>`_)


0.8.0 (2024-12-20)
==================

Bug Fixes
---------

- Fix cal_step setting when a step is skipped for roman datamodels. (`#195
  <https://github.com/spacetelescope/stpipe/issues/195>`_)
- Add hook to allow ModelLibrary subclasses to override exptype. (`#201
  <https://github.com/spacetelescope/stpipe/issues/201>`_)


Documentation
-------------

- use ``towncrier`` to handle change log entries (`#187
  <https://github.com/spacetelescope/stpipe/issues/187>`_)


New Features
------------

- test with Python 3.13 (`#193
  <https://github.com/spacetelescope/stpipe/issues/193>`_)
- Allow class aliases (used during strun) to contain the package name (for
  example "jwst::resample"). (`#202
  <https://github.com/spacetelescope/stpipe/issues/202>`_)


Deprecations and Removals
-------------------------

- Deprecate Step.__call__. For users that do not want to use CRDS parameters
  please use Step.run. (`#204
  <https://github.com/spacetelescope/stpipe/issues/204>`_)


0.7.0 (2024-08-13)
==================

- remove Windows tests and add info box indicating lack of Windows support to README [#163]
- add ``ModelLibrary`` container class [#156]
- add ``ModelLibrary`` docs [#168]
- improve memory usage of ``ModelLibrary.map_function`` [#181]
- log only strings in ``Step.log_records`` when a formatter is provided [#171]

0.6.0 (2024-01-24)
==================

- Remove unused ``Step.closeout`` [#152]
- Remove unused ``Pipeline.set_input_filename``, ``Step.name_format``,
  ``Step.resolve_file_name``, ``format`` argument to ``Step.save_model``,
  ``name_format``, ``component_format`` and ``separator`` arguments to
  ``Step._make_output_path`` and ``Step.reference_uri_to_cache_path``. [#154]

0.5.2 (2024-03-21)
==================

- Update style and linting checking [#103]
- Fix regex issue in internal configobj [#108]
- Remove bundled ``configobj`` package in favor of the ``configobj`` package
  bundled into ``astropy``. [#122]
- Fix ``datetime.utcnow()`` DeprecationWarning [#134]
- Provide ``asn_n_members=1`` when opening the ``Step`` dataset for
  ``get_crds_parameters`` [#142]
- Fix bug in handling of ``pathlib.Path`` objects as ``Step`` inputs [#143]
- Log readable Step parameters [#140]
- Fix handling of functions and subprocesses as Step pre- and post-hooks.  Add
  ability to pass imported python functions and ``Step`` subclasses directly as
  hooks. And allow ``Step`` subclass instances with set parameters as hooks. [#133]

0.5.1 (2023-10-02)
==================

- Print out ``jwst`` or ``romancal`` versions from ``strun --version``. [#98]
- Print default parameter values for ``strun <step_alias> --help`` [#101]
- Move ``strun`` to entrypoints [#101]
- Deprecate ``preserve_comments`` fix spec parsing for inline comments with
  a closing parenthesis [#107]

0.5.0 (2023-04-19)
==================

- Remove use of deprecated ``pytest-openfiles`` ``pytest`` plugin. This has been replaced by
  catching ``ResourceWarning`` s. [#90]
- Start using ``pre-commit`` to handle style checks. [#79]
- Apply the ``isort`` and ``black`` code formatters and reduce the line length
  maximum to 88 characters. [#80]
- Add spell checking through the ``codespell`` tool. [#81]
- Drop support for Python 3.8 [#93]
- Remove ``stdatamodels`` dependency, as it is no longer used. [#91]
- Add ``flynt`` string update checking tool. [#92]

0.4.6 (2023-03-27)
==================

- add ``importlib.metadata`` as a dependency and update loading of entry_points to drop
  usage of pkg_resources [#84]
- update minimum python to 3.8 and ASDF version to 2.8 [#87]
- replace legacy AsdfExtension with resource_mapping [#82]
- update minimum version of ``asdf`` to ``2.13`` and add minimum dependency testing to CI [#75]

0.4.5 (2022-12-23)
==================

- convert ``FromCommandLine`` instances to str before using as keyword arguments to ``Step`` [#78]

0.4.4 (2022-12-16)
==================

- include ``scripts`` in package [#76]

0.4.3 (2022-12-15)
==================

- Load and merge configuration files for each step they are provided when
  running pipeline in interactive mode using ``Step.call()``. [#74]

- Restored support for step list arguments by removing code that was
  overwriting processed and validated command line arguments with their
  raw values. [#73]


0.4.2 (2022-07-29)
==================

- Refactored ``Step.crds_get_config_from_reference`` and
  ``Pipeline.get_config_from_reference`` to reduce memory when the input to
  a pipeline is an association file, i.e. a ``ModelContainer``. In this case
  the crds parameters are retrieved from the first model which is already opened. [#63]

- Added a small edit to ``Step.get_config_from_reference`` to run datamodel
  methods on the first contained model in a ModelContainer, rather than the
  ModelContainer itself [#67]

- Moved build configuration from ``setup.cfg`` to ``pyproject.toml`` to support PEP621 [#56]

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

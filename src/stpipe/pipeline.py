"""
Pipeline
"""

import logging
from os.path import dirname, join
from typing import ClassVar

from astropy.extern.configobj.configobj import ConfigObj, Section

from . import config_parser, crds_client, log
from .step import Step, get_disable_crds_steppars
from .utilities import _not_set

# For classmethods, use the STPIPE_ROOT_LOGGER
logger = logging.getLogger(log.STPIPE_ROOT_LOGGER)


class Pipeline(Step):
    """
    A Pipeline is a way of combining a number of steps together.
    """

    # Configuration
    spec = """
    """
    # A set of steps used in the Pipeline.  Should be overridden by
    # the subclass.
    step_defs: ClassVar = {}

    def __init__(self, *args, **kwargs):
        """
        See `~stpipe.step.Step` for the parameters.
        """
        Step.__init__(self, *args, **kwargs)

        # Configure all of the steps
        for key, val in self.step_defs.items():
            cfg = self.steps.get(key)
            if cfg is not None:
                new_step = val.from_config_section(
                    cfg,
                    parent=self,
                    name=key,
                    config_file=self.config_file,
                )
            else:
                new_step = val(
                    key,
                    parent=self,
                    config_file=self.config_file,
                    **kwargs.get(key, {}),
                )

            setattr(self, key, new_step)

    @property
    def reference_file_types(self):
        """Collect the list of all reftypes for child Steps that are not skipped.
        Overridden reftypes are included but handled normally later by the
        Pipeline version of the get_ref_override() method defined below.
        """
        return [
            reftype
            for step in self._unskipped_steps
            for reftype in step.reference_file_types
        ]

    @property
    def _unskipped_steps(self):
        """Return a list of the unskipped Step objects launched by `self`.

        Steps are also excluded if `Step.prefetch_references` is False.
        """
        return [
            getattr(self, name)
            for name in self.step_defs
            if (
                not getattr(self, name).skip and getattr(self, name).prefetch_references
            )
        ]

    def get_ref_override(self, reference_file_type):
        """Return any override for ``reference_file_type`` for any of the steps in
        Pipeline ``self``.  OVERRIDES Step.

        Returns
        -------
        override_filepath or None.

        """
        for step in self._unskipped_steps:
            override = step.get_ref_override(reference_file_type)
            if override is not None:
                return override
        return None

    @classmethod
    def merge_config(cls, config, config_file):
        steps = config.get("steps", {})

        # Configure all of the steps
        for key in cls.step_defs:
            cfg = steps.get(key)
            if cfg is not None:
                # If a config_file is specified, load those values and
                # then override them with our values.
                if cfg.get("config_file"):
                    cfg2 = config_parser.load_config_file(
                        join(dirname(config_file or ""), cfg.get("config_file"))
                    )
                    del cfg["config_file"]
                    config_parser.merge_config(cfg2, cfg)
                    steps[key] = cfg2
        return config

    @classmethod
    def load_spec_file(cls, preserve_comments=_not_set):
        spec = config_parser.get_merged_spec_file(
            cls, preserve_comments=preserve_comments
        )

        spec["steps"] = Section(spec, spec.depth + 1, spec.main, name="steps")
        steps = spec["steps"]
        for key, val in cls.step_defs.items():
            if not issubclass(val, Step):
                raise TypeError(f"Entry {key!r} in step_defs is not a Step subclass")
            stepspec = val.load_spec_file(preserve_comments=preserve_comments)
            steps[key] = Section(steps, steps.depth + 1, steps.main, name=key)

            config_parser.merge_config(steps[key], stepspec)

            # Also add a key that can be used to specify an external
            # config_file
            step = spec["steps"][key]
            step["config_file"] = "string(default=None)"
            step["name"] = "string(default='')"
            step["class"] = "string(default='')"

        return spec

    @classmethod
    def get_config_from_reference(cls, dataset, disable=None, crds_observatory=None):
        """Retrieve step parameters from reference database

        Parameters
        ----------
        cls : `stpipe.step.Step`
            Either a class or instance of a class derived
            from `Step`.

        dataset : `stpipe.datamodel.AbstractDataModel` or dict
            A model of the input file.  Metadata on this input file will
            be used by the CRDS "bestref" algorithm to obtain a reference
            file. If dict, crds_observatory must be a non-None value.

        disable: bool or None
            Do not retrieve parameters from CRDS. If None, check global settings.

        crds_observatory : str
            Observatory name ('jwst' or 'roman').

        Returns
        -------
        step_parameters : configobj
            The parameters as retrieved from CRDS. If there is an issue, log as such
            and return an empty config obj.
        """
        reftype = cls.get_config_reftype()
        refcfg = ConfigObj()
        refcfg["steps"] = Section(refcfg, refcfg.depth + 1, refcfg.main, name="steps")

        # Check if retrieval should be attempted.
        if disable is None:
            disable = get_disable_crds_steppars()
        if disable:
            logger.debug(
                "%s: CRDS parameter reference retrieval disabled.", reftype.upper()
            )
            return refcfg

        logger.debug("Retrieving all substep parameters from CRDS")
        #
        # Iterate over the steps in the pipeline
        if isinstance(dataset, dict):
            # crds_parameters was passed as input from pipeline.py
            crds_parameters = dataset
            if crds_observatory is None:
                raise ValueError("Need a valid name for crds_observatory.")
        else:
            crds_parameters, crds_observatory = cls._get_crds_parameters(dataset)

        for cal_step in cls.step_defs.keys():
            cal_step_class = cls.step_defs[cal_step]
            refcfg["steps"][cal_step] = cal_step_class.get_config_from_reference(
                crds_parameters,
                crds_observatory=crds_observatory,
            )
        #
        # Now merge any config parameters from the step cfg file
        logger.debug("Retrieving pipeline %s parameters from CRDS", reftype.upper())
        try:
            ref_file = crds_client.get_reference_file(
                crds_parameters,
                reftype,
                crds_observatory,
            )
        except (AttributeError, crds_client.CrdsError):
            logger.debug("%s: No parameters found", reftype.upper())
        else:
            if ref_file != "N/A":
                logger.info("%s parameters found: %s", reftype.upper(), ref_file)
                refcfg = cls.merge_pipeline_config(refcfg, ref_file)
            else:
                logger.debug("No %s reference files found.", reftype.upper())

        return refcfg

    @classmethod
    def merge_pipeline_config(cls, refcfg, ref_file):
        """
        Merge the config parameters from a pipeline config reference file into the
        config obtained from each step

        Parameters
        ----------
        cls : jwst.stpipe.pipeline.Pipeline class
            The pipeline class

        refcfg : ConfigObj object
            The ConfigObj created from crds cfg files from each of the steps
            in the pipeline

        ref_file : string
            The name of the pipeline crds step config file

        Returns
        -------
        ConfigObj of the merged parameters, with those from the pipeline cfg having
        precedence over those from the individual steps
        """

        pipeline_cfg = config_parser.load_config_file(ref_file)
        config_parser.merge_config(refcfg, pipeline_cfg)
        return refcfg

    def _precache_references(self, input_file):
        """
        Precache all of the expected reference files before the Step's
        process method is called.

        Handles opening `input_file` as a model if it is a filename.

        input_file:  filename, model container, or model

        Returns
        -------
        None
        """
        try:
            crds_parameters, observatory = self._get_crds_parameters(input_file)
        except (ValueError, TypeError, OSError):
            self.log.info("First argument %s does not appear to be a model", input_file)
            return

        ovr_refs = {
            reftype: self.get_ref_override(reftype)
            for reftype in self.reference_file_types
            if self.get_ref_override(reftype) is not None
        }

        fetch_types = sorted(set(self.reference_file_types) - set(ovr_refs.keys()))

        self.log.info(
            "Prefetching reference files for dataset: %r reftypes = %r",
            self._get_filename(input_file),
            fetch_types,
        )
        crds_refs = crds_client.get_multiple_reference_paths(
            crds_parameters, fetch_types, observatory
        )

        ref_path_map = dict(list(crds_refs.items()) + list(ovr_refs.items()))

        for reftype, refpath in sorted(ref_path_map.items()):
            how = "Override" if reftype in ovr_refs else "Prefetch"
            self.log.info(
                "%s for %s reference file is '%s'.", how, reftype.upper(), refpath
            )
            crds_client.check_reference_open(refpath)

    def get_pars(self, full_spec=True):
        """Retrieve the configuration parameters of a pipeline

        Parameters are retrieved for the pipeline and all of its
        component steps.

        Parameters
        ----------
        full_spec : bool
            Return all parameters, including parent-specified parameters.
            If `False`, return only parameters specific to the pipeline
            and steps.

        Returns
        -------
        pars : dict
            Keys are the parameters and values are the values.
        """
        pars = super().get_pars(full_spec=full_spec)
        pars["steps"] = {}
        for step_name in self.step_defs.keys():
            pars["steps"][step_name] = getattr(self, step_name).get_pars(
                full_spec=full_spec
            )
        return pars

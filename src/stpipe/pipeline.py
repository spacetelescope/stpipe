"""
Pipeline
"""
from collections.abc import Sequence
from os.path import dirname, join
from argparse import Namespace
from .extern.configobj.configobj import Section, ConfigObj

from . import config_parser
from . import crds_client
from . import log
from .step import get_disable_crds_steppars, Step


# For classmethods, the logger to use is the
# delegator, since the pipeline has not yet been instantiated.
logger = log.delegator.log

class Pipeline(Step):
    """
    A Pipeline is a way of combining a number of steps together.
    """

    # Configuration
    spec = """
    """
    # A set of steps used in the Pipeline.  Should be overridden by
    # the subclass.
    step_defs = {}

    def __init__(self, *args, **kwargs):
        """
        See `Step.__init__` for the parameters.
        """
        Step.__init__(self, *args, **kwargs)

        # Configure all of the steps
        for key, val in self.step_defs.items():
            cfg = self.steps.get(key)
            if self.param_args is not None:
                if isinstance(self.param_args, Namespace):
                    self._override_stepconfig_from_param_args(key, cfg, self.param_args)
                elif isinstance(self.param_args, dict):
                    allsteps_dict = self.param_args.get('steps', {})
                    step_dict = allsteps_dict.get(key, {})
                    for item in step_dict:
                        cfg[item] = step_dict[item]
                else:
                    # Can this ever be reached?
                    raise ValueError(f"Cannot parse arguments to Pipeline: {self.param_args}")
            if cfg is not None:
                new_step = val.from_config_section(
                    cfg, parent=self, name=key,
                    config_file=self.config_file)
            else:
                new_step = val(
                    key, parent=self, config_file=self.config_file,
                    **kwargs.get(key, {}))

            setattr(self, key, new_step)

    @property
    def reference_file_types(self):
        """Collect the list of all reftypes for child Steps that are not skipped.
        Overridden reftypes are included but handled normally later by the
        Pipeline version of the get_ref_override() method defined below.
        """
        return [reftype for step in self._unskipped_steps
                for reftype in step.reference_file_types]

    @property
    def _unskipped_steps(self):
        """Return a list of the unskipped Step objects launched by `self`.

        Steps are also excluded if `Step.prefetch_references` is False.
        """
        return [getattr(self, name) for name in self.step_defs
                if (not getattr(self, name).skip and getattr(self, name).prefetch_references)]

    def get_ref_override(self, reference_file_type):
        """Return any override for `reference_file_type` for any of the steps in
        Pipeline `self`.  OVERRIDES Step.

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
        steps = config.get('steps', {})

        # Configure all of the steps
        for key in cls.step_defs:
            cfg = steps.get(key)
            if cfg is not None:
                # If a config_file is specified, load those values and
                # then override them with our values.
                cfg3 = cfg.copy()
                if cfg.get('config_file'):
                    cfg2 = config_parser.load_config_file(
                        join(dirname(config_file or ''), cfg.get('config_file')))
                    del cfg['config_file']
                    del cfg3['config_file']
                    config_parser.merge_config(cfg, cfg2)
                    config_parser.merge_config(cfg, cfg3)
                    steps[key] = cfg

        return config

    @classmethod
    def load_spec_file(cls, preserve_comments=False):
        spec = config_parser.get_merged_spec_file(
            cls, preserve_comments=preserve_comments)

        spec['steps'] = Section(spec, spec.depth + 1, spec.main, name="steps")
        steps = spec['steps']
        for key, val in cls.step_defs.items():
            if not issubclass(val, Step):
                raise TypeError(
                    "Entry {0!r} in step_defs is not a Step subclass"
                    .format(key))
            stepspec = val.load_spec_file(preserve_comments=preserve_comments)
            steps[key] = Section(steps, steps.depth + 1, steps.main, name=key)

            config_parser.merge_config(steps[key], stepspec)

            # Also add a key that can be used to specify an external
            # config_file
            step = spec['steps'][key]
            step['config_file'] = 'string(default=None)'
            step['name'] = "string(default='')"
            step['class'] = "string(default='')"

        return spec

    @classmethod
    def get_config_from_reference(cls, dataset, disable=None):
        """Retrieve step parameters from reference database

        Parameters
        ----------
        cls : `jwst.stpipe.step.Step`
            Either a class or instance of a class derived
            from `Step`.

        dataset : `jwst.datamodels.ModelBase`
            A model of the input file.  Metadata on this input file will
            be used by the CRDS "bestref" algorithm to obtain a reference
            file.

        disable: bool or None
            Do not retrieve parameters from CRDS. If None, check global settings.

        Returns
        -------
        step_parameters : configobj
            The parameters as retrieved from CRDS. If there is an issue, log as such
            and return an empty config obj.
        """
        reftype = cls.get_config_reftype()
        refcfg = ConfigObj()
        refcfg['steps'] = Section(refcfg, refcfg.depth + 1, refcfg.main, name="steps")

        # Check if retrieval should be attempted.
        if disable is None:
            disable = get_disable_crds_steppars()
        if disable:
            logger.debug(f'{reftype.upper()}: CRDS parameter reference retrieval disabled.')
            return refcfg


        logger.debug('Retrieving all substep parameters from CRDS')
        #
        # Iterate over the steps in the pipeline
        with cls._datamodels_open(dataset, asn_n_members=1) as model:
            if isinstance(model, Sequence):
                for contained_model in model:
                    input_class = contained_model.__class__()
                    metadata = input_class
                    metadata.update(contained_model, only='PRIMARY')
            else:
                input_class = model.__class__()
                metadata = input_class
                metadata.update(model, only='PRIMARY')

        for cal_step in cls.step_defs.keys():
            cal_step_class = cls.step_defs[cal_step]
            refcfg['steps'][cal_step] = cal_step_class.get_config_from_reference(metadata)
        #
        # Now merge any config parameters from the step cfg file
        logger.debug(f'Retrieving pipeline {reftype.upper()} parameters from CRDS')
        try:
            ref_file = crds_client.get_reference_file(metadata.get_crds_parameters(),
                                                    reftype,
                                                    metadata.crds_observatory)
        except (AttributeError, crds_client.CrdsError):
            logger.debug(f'{reftype.upper()}: No parameters found')
        else:
            if ref_file != 'N/A':
                logger.info(f'{reftype.upper()} parameters found: {ref_file}')
                refcfg = cls.merge_pipeline_config(refcfg, ref_file)
            else:
                logger.debug(f'No {reftype.upper()} reference files found.')

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

    @classmethod
    def from_config_section(cls, config, parent=None, name=None,
                            config_file=None, param_args=None):
        """
        Create a step from a configuration file fragment.

        Parameters
        ----------
        config : configobj.Section instance
            The config file fragment containing parameters for this
            step only.
        parent : Step instance, optional
            The parent step of this step.  Used to determine a
            fully-qualified name for this step, and to determine
            the mode in which to run this step.
        name : str, optional
            If provided, use that name for the returned instance.
            If not provided, try the following (in order):
            - The ``name`` parameter in the config file fragment
            - The name of returned class
        config_file : str, optional
            The path to the config file that created this step, if
            any.  This is used to resolve relative file name
            parameters in the config file.

        Returns
        -------
        step : instance of cls
            Any parameters found in the config file fragment will be
            set as member variables on the returned `Step` instance.
        """

        #spec = cls.load_spec_file()
        #config_parser.validate(
        #    config, spec, root_dir=dirname(config_file or ''))


        config = cls.finalize_config(config, name, config_file)

        step = cls(
            name=name,
            parent=parent,
            config_file=config_file,
            _validate_kwds=False,
            param_args=param_args,
            **config)

        return step

    def set_input_filename(self, path):
        self._input_filename = path
        for key in self.step_defs:
            getattr(self, key).set_input_filename(path)

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
            with self.open_model(input_file, asn_n_members=1,
                                asn_exptypes=["science"]) as model:
                self._precache_references_opened(model)
        except (ValueError, TypeError, IOError):
            self.log.info(
                'First argument {0} does not appear to be a '
                'model'.format(input_file))

    def _precache_references_opened(self, model_or_container):
        """Pre-fetches references for `model_or_container`.

        Handles recursive pre-fetches for any models inside a container,
        or just a single model.

        Assumes model_or_container is an open model or container object,
        not a filename.

        No garbage collection.
        """
        if isinstance(model_or_container, Sequence):
            # recurse on each contained model
            for contained_model in model_or_container:
                self._precache_references_opened(contained_model)
        else:
            # precache a single model object
            self._precache_references_impl(model_or_container)

    def _precache_references_impl(self, model):
        """Given open data `model`,  determine and cache reference files for
        any reference types which are not overridden on the command line.

        Verify that all CRDS and overridden reference files are readable.

        Parameters
        ----------
        model :  `DataModel`
            Only a `DataModel` instance is allowed.
            Cannot be a filename, Sequence, etc.
        """
        ovr_refs = {
            reftype: self.get_ref_override(reftype)
            for reftype in self.reference_file_types
            if self.get_ref_override(reftype) is not None
            }

        fetch_types = sorted(set(self.reference_file_types) - set(ovr_refs.keys()))

        self.log.info("Prefetching reference files for dataset: " + repr(model.meta.filename) +
                      " reftypes = " + repr(fetch_types))
        crds_refs = crds_client.get_multiple_reference_paths(model.get_crds_parameters(), fetch_types, model.crds_observatory)

        ref_path_map = dict(list(crds_refs.items()) + list(ovr_refs.items()))

        for (reftype, refpath) in sorted(ref_path_map.items()):
            how = "Override" if reftype in ovr_refs else "Prefetch"
            self.log.info(f"{how} for {reftype.upper()} reference file is '{refpath}'.")
            crds_client.check_reference_open(refpath)

    def _override_stepconfig_from_param_args(self, stepname, stepcfg, param_args):
        """After step config is built from any CRDS or user provided pars files,
        overwrite cfg with command line specified parameter values

        Parameters
        ----------
        stepname : str
            Step name provided in step_defs, used to pull relevant pars
            from param_args Namespace

        stepcfg : ConfigObj
            The configobj built from step_pars files but not yet including
            possible command line values

        param_args : argparse.Namespace
            The parsed set of command line arguments
        """
        for arg in vars(param_args):
            if f'steps.{stepname}' in arg:
                if vars(param_args)[arg] is not None:
                    stepcfg.merge({arg.split('.')[-1]: vars(param_args)[arg]})

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
        pars['steps'] = {}
        for step_name, step_class in self.step_defs.items():
            pars['steps'][step_name] = getattr(self, step_name).get_pars(full_spec=full_spec)
        return pars

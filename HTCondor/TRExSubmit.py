#!/usr/bin/env python3

"""
================================================================================
=== Python Script to run Condor batch jobs for different steps in TRExFitter ===
================================================================================

Description:

 - v1.0 New features:
    - Split by systematic as well as region
    - Ignore commented out regions/systematics
    - Ignore if syst/reg name is enclosed by double quote
    - parse through syst names with ; separating them

 - v2.0 New features:
    - Parsing of arguments - no need to hardcode in the python code anymore (only in the config structure)
    - Submission of all jobs in a single cluster instead of many clusters with one job each
    - Possibility to execute a dry-run - Generates ready-to-execute scripts for submission, but does not submit

 - v2.1 New features:
    - Possibility to store configs and replacement files consistently within the work directory for re-use between
      actions
    - Change of default behaviour for results: Instead of getting stored in the work directory, config paths are
      respected
    - Detection of configs without systematics to fix a no-submission bug in these cases
    - Possibility to bundle multiple systematics per batch-job to reduce I/O load on ntuple files
    - Option to select configs to run in jobs (mostly for multi-fit support)
    - Possibility to run ranking jobs per systematic


 TODO: Nice to haves:
    - Add deployment possibilities via tarballs for batch systems where submit and worker nodes do not share a
      filesystem
    - Convert submission scripts to DAG for automatic hupdate jobs with split systematics
    - Use htcondor API library for job submission directly instead of using subprocess
    - Add ability to submit Bootstrap jobs
    - Add ability to submit group impacts (via SubCategory option in syst blocks)
"""

import tempfile
import sys
import os
import subprocess
import stat
import shutil
import re
from difflib import get_close_matches

# Used for type deduction in the docs
from typing import List, Dict, Optional


class TRExSubmit:
    """Class to steer HTCondor script creation and submission of the resulting jobs."""

    def __init__(
        self,
        config_list: list,
        trex_folder: str,
        work_dir: str,
        actions: str,
        integrate_everything: bool = False,
        split_regions: bool = True,
        split_systs: bool = True,
        split_scan: bool = True,
        num_syst_per_job: int = 20,
        extra_opts: list = None,
        run_time: int = None,
    ) -> None:
        """Init the class and setup all variables.

        Parameters
        ----------
        config_list : list
            List of config files to use for TRExFitter.
        trex_folder : str
            Path to root folder of TRExFitter repo used to run jobs on the batch system.
        work_dir : str
            Root directory to store scripts, logs, and more in.
        actions : str
            Actions to be executed by TRExFitter.
        integrate_everything : bool, optional
            Whether to also store configs and the TRExFitter workspace inside `work_dir`
            (`True`) or not (`False`). This also adjusts paths inside the configs to
            work seamlessly. By default, configs are not stored inside `work_dir` and
            the manually defined paths of the configs are used for replacement files,
            inputs, and outputs, by default False.
        split_regions : bool, optional
            Whether to split supported actions by region (`True`) or not (`False`).
            By default, such actions are split, by default True
        split_systs : bool, optional
            Whether to split supported actions by systematic in each region (`True`)
            or not (`False`). By default, such actions are split, by default True.
        split_scan : bool, optional
            Whether to split the likelihood scan into steps (`True`) or not (`False`).
        num_syst_per_job : int, optional
            How many systematics to bundle per batch job during the `n` action, if
            neither `split_regions` nor `split_systs` is engaged, by default 20
        extra_opts : list, optional
            Extra options to be supplied to the TRExFitter executable. By default,
            no such options are supplied, by default None
        run_time : int, optional
            Non-standard run-time to be requested for the jobs, by default None
        """
        self.config_list = config_list
        self.trex_folder = trex_folder
        self.work_dir = work_dir
        self.run_time = run_time

        # Already define the subdirectories
        self.script_dir = os.path.join(self.work_dir, self.SUB_DIRS["scripts"])
        self.log_dir = os.path.join(self.work_dir, self.SUB_DIRS["logs"])

        # Only required if we want to keep configs and TRExFitter workspace in the work directory
        self.config_dir = os.path.join(self.work_dir, self.SUB_DIRS["configs"])
        self.workspace_dir = os.path.join(self.work_dir, self.SUB_DIRS["results"])

        # Build the regex expressions needed later on
        # Rep-file: Take everything up to comments and trim whitespace in the path, disregard quotes
        self._file_regex = re.compile(
            "^\s*(?P<key>[\w-]+)\s*:\s*(?P<value>[^#%]*[^\s#%])[\s#%]*"  # noqa W605
        )
        # Other keys: Allow quote-escaping of value and add key and quote groups with logic for retrieval
        self._key_regex = re.compile(
            '^\s*(?P<key>[\w-]+)\s*:\s*(?P<quote>")?'                        # noqa W605
            '(?P<value>(?(quote)[^"]+|[^"#%]*[^"\s#%]))(?(quote)"|)[\s#%]*'  # noqa W605
        )

        # Make the work directory (pass if it's already present but fail if the parent directory is not there)
        try:
            os.mkdir(self.work_dir)
        except FileExistsError:
            pass

        # Read actions and make sure the `n` or 'b' step is executed alone only to not have thousands of job failures from this
        self.actions = actions
        if (
            self.actions is not None
            and ("n" in self.actions or "b" in self.actions)
            and self.actions not in ["n", "b"]
        ):
            print(
                f"\033[31mERROR: N-tuple translation action `n` should only be used alone, you used `{self.actions}`!"
                f"\033[0m",
                file=sys.stderr,
            )
            sys.exit(1)

        # Logic-OR whether to integrate configs and results
        self.integrate_everything = self._check_update_integrate_cachefile(
            integrate_everything
        )
        self.config_region_syst_dict = None

        # Check if we got any configs if we don't integrate
        if not self.integrate_everything and not self.config_list:
            print(
                "\033[31mERROR: You cannot work in non-integrated mode without configs!\033[0m",
                file=sys.stderr,
            )
            sys.exit(1)

        # We need to transfer configs and query everything if we want to integrate everything into the work directory
        if self.integrate_everything:
            os.makedirs(self.config_dir, exist_ok=True)
            if self.config_list is not None:
                self._check_integrate_configs(self.config_list)
            self.config_list = [
                os.path.join(self.config_dir, f) for f in self._query_cached_configs()
            ]

        # It only makes sense to run regions separated if we have the `n` or 'b' action included
        self.split_regions = split_regions if self.actions in ["n", "b"] else False
        # We automatically run systematics together if we run regions together (unless in 'r' mode)
        self.split_systs = split_systs if "r" in self.actions else False
        self.split_systs = (
            (split_systs and self.split_regions)
            if ("n" in self.actions or "b" in self.actions)
            else self.split_systs
        )
        self.split_scan = split_scan if "x" in self.actions else False
        self.num_syst_per_job = num_syst_per_job if self.split_systs else None
        self.extra_opts = [extra_opts] if isinstance(extra_opts, str) else extra_opts

        # Build the correct key for the granularity-dict
        self.granularity = "global"
        if self.split_regions and not self.split_systs:
            self.granularity = "region"
        elif self.split_regions and self.split_systs:
            self.granularity = "syst"
        elif not self.split_regions and self.split_systs:
            self.granularity = "ranking"
        elif self.split_scan:
            self.granularity = "lhscan"

    def build_and_submit(
        self,
        config_list: list,
        dry_run: bool = False,
        stage_out_results=False,
    ) -> None:
        """Execute the job submission.

        Uses the values supplied during initialisation to generate HTCondor submit
        scripts and the actual bash-scripts to run on the worker nodes. Afterwards,
        submits the jobs if we are not in a dry-run.

        Parameters
        ----------
        config_list : list
            List of cached (and newly supplied) configs to use for TRExFitter jobs.
            By default, all found cached configs are used by the jobs.
        dry_run : bool, optional
            Whether to actually submit the prepared jobs (`False`) or not (`True`).
            By default, the jobs are submitted to HTCondor, by default False
        stage_out_results : bool, optional
            Whether results of the fits need to be staged out of the worker nodes
            (`True`, in case access point and worker node don't share a filesystem)
            or not (`False`). By default, no need to stage out results is assumed,
            by default False
        """

        if not self.integrate_everything and config_list is not None:
            print(
                "\033[33mWARNING: Explicit config list to run supplied even though "
                "we are not running in integrated "
                "mode! This will have no effect!\033[0m",
                file=sys.stderr,
            )

        elif config_list is not None:
            self._match_update_config_list(config_list)

        # Associate regions and systematics with config files (and check that we only have each region once)
        self.config_region_syst_dict = self._get_config_region_syst_dict(
            self.config_list,
        )
        # Now check that we have at least one systematic - or disable the split by systematics
        self._check_update_systematic_split(self.config_region_syst_dict)

        os.makedirs(self.script_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        if self.integrate_everything:
            os.makedirs(self.workspace_dir, exist_ok=True)

        condor_result_dir = self.workspace_dir if stage_out_results else None

        job_file = os.path.join(self.script_dir, f"job_arguments_{self.actions}.txt")
        script_file = os.path.join(self.script_dir, f"script_{self.actions}.sh")
        submit_file = os.path.join(self.script_dir, f"submit_{self.actions}.sub")

        self._build_job_file(
            config_region_syst_dict=self.config_region_syst_dict,
            job_filename=job_file,
        )
        self._write_batch_bash(
            script_path=script_file,
            actions=self.actions,
            extra_opts=self.extra_opts,
        )
        self._write_htc_submit(
            submit_file_path=submit_file,
            script_path=script_file,
            job_file=job_file,
            log_dir=self.log_dir,
            result_dir=condor_result_dir,
            granularity=self.granularity,
            run_time=self.run_time,
        )

        if dry_run:
            print(f"INFO: In dry-run, submit files can be found in {self.work_dir}")
        else:
            print(f"INFO: Submitting jobs...")
            proc = subprocess.run(
                ["condor_submit", submit_file], stdout=sys.stdout, stderr=sys.stderr
            )
            sys.exit(proc.returncode)

    def _check_update_integrate_cachefile(self, cli_flag: bool) -> bool:
        """Checks whether integration of configs and results should be performed

        This is set to `True` either if directly submitted via CLI options or already
        present in the work-directory as a cachefile `_integrate.cache`.

        Parameters
        ----------
        cli_flag : bool
            Whether the integrate option was specifically requested via CLI (`True`)
            or not (`False`). This is necessary to update the integrate cache if
            previous steps did not explicitly request integration.

        Returns
        -------
        bool
            Integration-flag built from a logical-OR of `integration_flag` and
            (if present) the work directory cache.
        """
        integration_cachefile = os.path.join(self.work_dir, ".integrate.cache")
        cache_flag = False

        # Read in cache flag and update combined flag is existing
        if os.path.isfile(integration_cachefile):
            with open(integration_cachefile) as f:
                cache_flag = (
                    f.read().replace("\n", "") == "True"
                )  # Remove unwanted linebreaks
            integration_flag = cli_flag | cache_flag
        else:
            integration_flag = cli_flag

        # Update cache-file
        with open(integration_cachefile, "w") as f:
            cache_flag_string = "True" if integration_flag else "False"
            f.write(cache_flag_string)

        # Generate some logging output
        if cache_flag:
            print(
                "INFO: Integrating configs and TRExFitter workspace into "
                f"'{self.work_dir}' as saved in cache."
            )
        elif cli_flag:
            print(
                "INFO: Integrating configs and TRExFitter workspace into "
                f"'{self.work_dir}' as requested on CLI."
            )
        else:
            print(
                f"INFO: Not integrating configs and TRExFitter workspace "
                f"into '{self.work_dir}'.\n"
                "      Ensuring consistent paths in the configs is your "
                "responsibility!"
            )

        return integration_flag

    def _get_config_region_syst_dict(
        self,
        config_list: list,
    ) -> Dict[str, Dict[str, List[str]]]:
        """Retrieves regions and systematics from multiple TRExFitter configs
        and checks region uniqueness.

        The dictionary returned by this function has the following form:
        ```
            <config1>: {regions: [<region1>, <region2>, ..., <regionN>],
                        systs: [<syst1.1>, <syst1.2>, ...]},
            <config2>: {regions: [<regionN+1>, ...], systs: [<syst2.1,>, ...]},
            ...
        ```

        The function raises an error if some region is present in multiple
        configs, as this will mess up ntuple-histogram conversion.

        Parameters
        ----------
        config_list : list
            List of TRExFitter config paths.

        Returns
        -------
        Dict[str, Dict[str, List[str]]]
            Dictionary associating regions and systematics to the configs in
            the schema described above.

        Raises
        ------
        RuntimeError
            If some region is present in multiple configs.
        """
        region_check_set = set()
        config_region_syst_dict = {}

        for config in config_list:
            config_regions = self._get_region_list(config)
            config_systs = self._get_syst_list(config)

            # Use sets for checking intersections for complexity - empty set evaluates as `False`
            region_intersection = region_check_set & set(config_regions)
            if region_intersection:
                raise RuntimeError(
                    f"Regions {list(region_intersection)} in '{config}' were already present!"
                )

            # Add the new regions to our check_set
            region_check_set |= set(config_regions)

            # Now add all to the overall dict
            config_region_syst_dict[config] = {
                "regions": config_regions,
                "systs": config_systs,
            }

        return config_region_syst_dict

    def _get_region_list(
        self,
        config: str,
        as_subconfig: bool = False,
    ) -> List[str]:
        """Retrieves regions from TRExFitter config

        Parameters
        ----------
        config : str
            Path to TRExFitter config.
        as_subconfig : bool, optional
            Whether this function is called for a nested config from another config
            (`True`) or not (`False`), by default False

        Returns
        -------
        List[str]
            List of regions in config and included configs.
        """
        tmp_region_list = []
        sub_config_list = []

        with open(config) as conf:
            for line in conf:
                file_match = self._file_regex.search(line)
                key_match = self._key_regex.search(line)

                if key_match is not None and key_match['key'] == "Region":
                    tmp_region_list.append(key_match['value'])
                elif file_match is not None and file_match['key'] == "INCLUDE":
                    sub_config_list.append(
                        os.path.abspath(os.path.join(os.path.dirname(config), file_match['value']))
                    )
                elif (
                    'm' in self.actions
                    and key_match is not None
                    and key_match['key'] == "ConfigFile"
                ):
                    # Add in subconfigs into this config
                    sub_config_list.append(
                        os.path.abspath(os.path.join(os.path.dirname(config), key_match['value']))
                    )
                elif key_match is not None and key_match["key"] == "INCLUDE":
                    # now also check for any additonal included configs
                    include_file = os.path.join(self.config_dir, key_match["value"])
                    include_regions = self._get_region_list(
                        include_file, as_subconfig=True
                    )
                    tmp_region_list.extend(include_regions)

        # Use sets here as regions in nested configs may have common regions
        region_set = set(tmp_region_list)

        for sub_config in sub_config_list:
            sub_regions = self._get_region_list(sub_config, as_subconfig=True)
            region_set.update(sub_regions)

        region_list = sorted(list(region_set))

        if not as_subconfig:
            print(f"INFO: Regions found in '{config}' (and its nested configs):")
            for region in region_list:
                print(f"       - {region}")

        return region_list

    def _get_syst_list(
        self,
        config: str,
        as_subconfig: bool = False,
    ) -> List[str]:
        """_summary_

        Parameters
        ----------
        config : str
            Path to TRExFitter config.
        as_subconfig : bool, optional
            Whether this function is called for a nested config from another config
            (`True`) or not (`False`), by default False

        Returns
        -------
        List[str]
            List of systematics in config.
        """
        tmp_syst_list = []
        sub_config_list = []
        syst_list_template = "      - {}. {}"

        with open(config) as f:
            # Use caching variable for number of systematics to remove in case of NuisanceParameter entries
            last_syst_cache_size = 0

            for line in f:
                file_match = self._file_regex.search(line)
                key_match = self._key_regex.search(line)

                if file_match is not None and file_match['key'] == "INCLUDE":
                    sub_config_list.append(
                        os.path.abspath(os.path.join(os.path.dirname(config), key_match['value']))
                    )
                    continue
                elif (
                    'm' in self.actions
                    and key_match is not None
                    and key_match['key'] == "ConfigFile"
                ):
                    # Add in subconfigs into this config
                    sub_config_list.append(
                        os.path.abspath(os.path.join(os.path.dirname(config), key_match['value']))
                    )
                    continue

                line = line.split("%")[0].strip()

                if line.startswith("#"):
                    continue

                # Gathering systematics (and background norm factors & deviating NP names for rankings)
                is_syst = "Systematic:" in line or "UnfoldingSystematic:" in line
                is_np = "r" in self.actions and "NuisanceParameter:" in line
                is_nf = "r" in self.actions and "NormFactor:" in line

                if not is_syst and not is_np and not is_nf:
                    continue

                syst_line = line.split(":")[1].strip()
                single_syst_list = []
                # let's get all the names for multi-systematic defined blocks
                for syst in syst_line.split(";"):
                    syst = syst.strip()
                    # remove any quotes
                    if syst.startswith('"') and syst.endswith('"'):
                        syst = syst[1:-1]
                    single_syst_list.append(syst)

                if is_syst:
                    # Update the systematics list we use to remove entries
                    # in case we have a NuisanceParameter entry for this systematic
                    last_syst_cache_size = len(single_syst_list)
                elif is_np:
                    # Remove last systematic's entries from the combined list
                    # (under the assumption that a NuisanceParameter will never stand outside a
                    # Systematic or UnfoldingSystematic block!!!)
                    if args.used_configs:
                        assert len(single_syst_list) == last_syst_cache_size
                    tmp_syst_list = tmp_syst_list[:-last_syst_cache_size]
                elif is_nf:
                    # Filter out POIs for NormFactors (those should start with 'mu_')
                    single_syst_list = list(
                        filter(lambda s: not s.startswith("mu_"), single_syst_list)
                    )

                tmp_syst_list += single_syst_list

        # Use sets here as to not double-count systematics in nested configs
        syst_set = set(tmp_syst_list)

        for sub_config in sub_config_list:
            sub_systs = self._get_syst_list(sub_config, as_subconfig=True)
            syst_set.update(sub_systs)

        syst_list = sorted(list(syst_set))

        # Only print systematics if we found any
        if not as_subconfig and not syst_list:
            print(f"INFO: No systematics found in '{config}'")
        elif not as_subconfig:
            print(f"INFO: Systematics found in '{config}' (and its nested configs):")
            # First figure out the maximum width of the systematic index (so that we align the systematics names)
            syst_index_width = len(f"{len(syst_list):d}")
            syst_list_format = f"      - {{index:>{syst_index_width:d}d}}. {{syst}}"

            for index, syst in enumerate(syst_list, start=1):
                print(syst_list_template.format(index, syst))

        return syst_list

    def _check_update_systematic_split(
        self,
        config_region_syst_dict: dict,
    ) -> None:
        """Check number of systematics per config and region for job splits

        Parameters
        ----------
        config_region_syst_dict : dict
            Dictionary with config file names and associated regions and
            systematics in the schema returned by `_get_config_region_syst_dict`.
        """
        # No need to do anything if we already do not split by systematics
        if not self.split_systs:
            return

        for config, region_syst_dict in config_region_syst_dict.items():
            if not region_syst_dict["systs"]:
                print(
                    f"INFO: No systematics present for config '{config}'.\n"
                    f"      Disabling systematics split in condor jobs..."
                )
                self.split_systs = False
                break

    def _check_integrate_configs(self, config_list: list) -> None:
        """Add additional configs to the config subdirectory.

        Before new configs (and replacement files) are added, files are checked
        for namespace collisions as well. Additionally, the input, output, include,
        and replacement file paths in the configs are updated in such a way that
        they can be used without further modifications.

        Parameters
        ----------
        config_list : list
            List of config files to be added to the config subdirectory.
        """
        cached_configs = self._query_cached_configs()

        # Extract the config names from the paths
        config_names = {}
        replacement_paths = {}
        include_file_paths = {}
        for config_path in config_list:
            config_name = os.path.basename(config_path)
            config_name = (
                config_name[:-5] if config_name.endswith(".yaml") else config_name
            )
            config_names[config_path] = config_name

            # Check that we actually can access the file
            if not os.path.isfile(config_path):
                print(
                    f"\033[31mERROR: Cannot find '{config_path}'!\033[0m",
                    file=sys.stderr,
                )
                sys.exit(1)

            # Deal with the replacement file
            rep_file_paths = self._get_path_from_config(config_path, 'ReplacementFile')

            if len(rep_file_paths) > 1:
                print(
                    f"\033[31mERROR: Found {len(rep_file_paths)} "
                    f"replacement files in '{config_path}'!\033[0m",
                    file=sys.stderr
                )
                sys.exit(1)

            rep_file = None if not rep_file_paths else rep_file_paths[0]

            # Deal with relative replacement files
            if rep_file is not None and not os.path.isabs(rep_file):
                rep_file = os.path.abspath(
                    os.path.join(os.path.dirname(config_path), rep_file)
                )

            if rep_file is not None and not os.path.isfile(rep_file):
                print(
                    "\033[31mERROR: Cannot find replacement file "
                    f"'{rep_file}' for '{config_path}'!\033[0m",
                    file=sys.stderr,
                )
                sys.exit(1)

            replacement_paths[config_name] = rep_file

            # Now deal with included files - they cannot recurse in TRExFitter
            # at the moment (December 2023), so we'll not do that either
            config_include_file_paths = self._get_path_from_config(config_path, 'INCLUDE')
            config_include_file_path_dict = {}
            for path in config_include_file_paths:
                abs_path = path
                if not os.path.isabs(path):
                    abs_path = os.path.abspath(
                        os.path.join(os.path.dirname(config_path), path)
                    )

                if not os.path.isfile(abs_path):
                    print(
                        f"\033[31mERROR: Cannot find include file '{abs_path}' for "
                        f"'{config_path}'!\033[0m",
                        file=sys.stderr
                    )
                    sys.exit(1)

                # Now add the path
                config_include_file_path_dict[path] = abs_path

            if config_include_file_path_dict:
                tmp_include_string = '    - ' + '\n    - '.join(
                    config_include_file_path_dict.values()
                )
                print(
                    f"INFO: Including the following files for '{config_name}':"
                    f"\n{tmp_include_string}"
                )

            include_file_paths[config_name] = config_include_file_path_dict

        # Check config_names for duplicates - both amongst the new ones and
        # with the cached ones
        cached_config_check = {
            os.path.splitext(os.path.basename(c))[0] for c in cached_configs
        }
        new_config_check = set(config_names.values())
        if not len(new_config_check) == len(config_names.values()):
            print(
                "\033[31mERROR: Multiple configs you submitted have the same filename "
                "and cannot be cached!\033[m",
                file=sys.stderr,
            )
            sys.exit(1)

        config_intersection = new_config_check & cached_config_check
        if config_intersection:
            print(
                "\033[31mERROR: Newly added config names clash with the cached "
                f"configs {config_intersection}!\033[0m",
                file=sys.stderr,
            )
            sys.exit(1)

        # Add configs and replacement files, change paths
        for config_path, config_name in config_names.items():
            replacement_path = replacement_paths[config_name]
            config_include_file_paths = include_file_paths[config_name]

            new_config_path = os.path.join(self.config_dir, f"{config_name}.yaml")
            new_replacement_file = (
                f"REPLACEMENTFILE_{config_name}.yaml"
                if replacement_path is not None
                else None
            )
            old_new_include_file_path_pairs = {
                ref: (old_path, f"INCLUDEFILE_{i}_{config_name}.yaml")
                for i, (ref, old_path) in enumerate(config_include_file_paths.items())
            }
            old_new_include_file_value_dict = {
                old_value: new_value
                for old_value, (_, new_value) in old_new_include_file_path_pairs.items()
            }

            shutil.copy2(config_path, new_config_path)
            if replacement_path is not None:
                shutil.copy2(replacement_path, os.path.join(self.config_dir, new_replacement_file))
            for old_path, new_file_name in old_new_include_file_path_pairs.values():
                shutil.copy2(old_path, os.path.join(self.config_dir, new_file_name))
            self._update_paths_in_config(new_config_path, old_new_include_file_value_dict, new_replacement_file)

    def _query_cached_configs(self) -> List[str]:
        """Retrieves config files from config folder

        For this, the function also discards files ending with
        `_REPLACEMENTFILE` - i.e. the replacement files.

        Returns
        -------
        List[str]
            List of cached config files.
        """
        file_list = [
            f
            for f in os.listdir(self.config_dir)
            if os.path.isfile(os.path.join(self.config_dir, f))
        ]

        # Now remove all replacement files and return the remainder
        return [
            f for f in file_list
            if (
                not f.startswith('REPLACEMENTFILE_')
                and not f.startswith('INCLUDEFILE_')
            )
        ]

    def _get_path_from_config(self, config_path: str, key: str) -> List[str]:
        """Crawls config to find possible paths at a specific key

        Parameters
        ----------
        config_path : str
            Path to the config to be crawled.
        key : str
            Key to search for in the config.

        Returns
        -------
        List[str]
            A list with all paths found under the key `key`.
        """

        matches = []
        with open(config_path) as f:
            for line in f:
                tmp_match = self._file_regex.search(line)
                if tmp_match is not None and tmp_match['key'] == key:  # Add the path if it matches the key
                    matches.append(tmp_match['value'])

        return matches

    def _update_paths_in_config(
        self,
        config_path: str,
        old_new_include_files: Dict[str, str],
        new_replacement_file: str = None,
    ) -> None:
        """Updates file paths and output directory for newly cached config.

        Parameters
        ----------
        config_path : str
            Config file to modify.
        old_new_include_files : Dict[str, str]
            Dictionary with the old include files as keys, and their old paths and
            new names as tuple-items.
        new_replacement_file : str, optional
            Name of relocated replacement file of the config. By default, it is
            assumed that the config file does not need a replacement file.

        Raises
        ------
        KeyError
            - If no replacement file name was submitted, but needed by the config file.
            - If an include file in the config does not have a valid replacement.
        """
        # Use relative paths and ensure that folder paths end in `/`
        rel_workspace_dir_slash = os.path.join("..", self.SUB_DIRS["results"], "")

        # Use temporary file for safety
        temp_file_handle, temp_file_path = tempfile.mkstemp()

        with open(temp_file_handle, "w") as temp_file, open(config_path) as orig_file:
            for line in orig_file:
                # This is where the matching magic happens
                new_line = line
                file_match = self._file_regex.search(line)
                key_match = self._key_regex.search(line)

                # No need to check for quotes with ReplacementFiles and INCLUDEs (as of December 2023)
                if file_match is not None and file_match['key'] == 'ReplacementFile':
                    if new_replacement_file is None:
                        raise KeyError(
                            f"No replacement file submitted for '{config_path}' but required!"
                        )
                    new_line = line.replace(file_match['value'], new_replacement_file)
                elif file_match is not None and file_match['key'] == 'INCLUDE':
                    if file_match['value'] not in old_new_include_files:
                        raise KeyError(
                                f"Include file '{file_match['value']}' to be "
                                f"changed has no alternative to change to!"
                        )
                    new_line = line.replace(
                        file_match['value'],
                        old_new_include_files[file_match['value']]
                    )
                elif key_match is not None:
                    # First make sure that we only change paths for the correct keys
                    if key_match["key"] not in self.CONFIG_KEYS_TO_PATH_CONVERT:
                        pass
                    else:
                        if (
                            key_match["quote"] == '"'
                        ):  # Check if we need to add in quotes after the fact
                            new_line = line.replace(
                                key_match["value"], rel_workspace_dir_slash
                            )
                        else:
                            new_line = line.replace(
                                key_match["value"], f'"{rel_workspace_dir_slash}"'
                            )

                temp_file.write(new_line)

        # Copy the file permissions from the old file to the new file
        shutil.copymode(config_path, temp_file_path)
        # Move files
        temp_storage = f"{config_path}.swp"
        shutil.move(config_path, temp_storage)
        shutil.move(temp_file_path, config_path)
        # Finally, remove original config file
        os.remove(temp_storage)

    def _make_syst_bundle(self, systematics_list: list) -> Dict[str, str]:
        """Bundles systematics into groups to reduce file I/O load

        The systematics will be bundled with `num_syst_per_job` systematics
        per bundle. Systematics are separated by `,` as per TRExFitter
        conventions. Per bundle, a name for the bundle-suffix is also generated.

        Parameters
        ----------
        systematics_list : list
            List of systematics to be bundled.

        Returns
        -------
        Dict[str, str]
            List of bundles systematics separated by `,`.

        Raises
        ------
        RuntimeError
            If somehow to many systematics bundles are present.
        """
        syst_bundles = {}
        tmp_syst_list = []
        bundle_counter = 0  # Needed for easily parseable bundles in case of multiple systematics per job

        assert (
            self.num_syst_per_job is not None
        ), "Something with the systematics processing has gone very wrong!"

        for syst in systematics_list:
            if (
                self.num_syst_per_job == 1
            ):  # The easy case: Only one systematic per job...
                syst_bundles[syst] = syst
                bundle_counter += 1
                continue

            if len(tmp_syst_list) == self.num_syst_per_job:
                syst_bundles[f"Syst_group_{bundle_counter:04d}"] = ",".join(
                    tmp_syst_list
                )
                bundle_counter += 1
                tmp_syst_list.clear()
            elif len(tmp_syst_list) > self.num_syst_per_job:
                raise RuntimeError(
                    "Somehow, we ended up with too many systematics in the bundle here!"
                )

            tmp_syst_list.append(syst)  # Do not forget the current systematic!

        # Final fill with possible left-over systematics
        if tmp_syst_list:
            syst_bundles[f"Syst_group_{bundle_counter:04d}"] = ",".join(tmp_syst_list)
            bundle_counter += 1

        assert len(syst_bundles) == bundle_counter

        return syst_bundles

    def _match_update_config_list(self, new_list: list) -> None:
        """Matches the current config list with the input list for
        selecting configs

        Parameters
        ----------
        new_list : list
            List of configs to match with the current config region-systematics dictionary.
        """
        tmp_config_list = []
        cached_config_list = [os.path.basename(c) for c in self.config_list]

        for config in new_list:
            if (
                config not in cached_config_list
            ):  # Go through suggestions interactively to find possible matches
                tmp_config = None
                cached_string = "\n        - ".join(cached_config_list)
                possible_matches = get_close_matches(config, cached_config_list)
                for match in possible_matches:
                    answer = input(
                        f"INFO: Could not find '{config}' directly! Did you mean '{match}'? [yN] "
                    ).lower()
                    if answer == "y":
                        tmp_config = match
                        break

                # Error case when no suggestion fits
                if tmp_config is None:
                    print(
                        f"\033[31mERROR: Could not find '{config}' directly! The following configs are cached:\n"
                        f"        - {cached_string}\033[0m"
                    )
                    sys.exit(1)
            else:
                tmp_config = config

            tmp_config_path = os.path.join(self.config_dir, tmp_config)
            if tmp_config_path in tmp_config_list:
                print(
                    f"\033[33mWARNING: Config '{tmp_config}' already matched! Please check your setup!\033[0m",
                    file=sys.stderr,
                )
            else:
                tmp_config_list.append(tmp_config_path)

        # Finally, update the class member with the selected configs
        self.config_list = tmp_config_list

    def _get_lhscan_steps(self, config: str) -> int:
        """Extracts LHscanSteps from TRExFitter config.

        Parameters
        ----------
        config : str
            Path to TRExFitter config.

        Returns
        -------
        int
            Number of steps for the likelihood scan.
        """

        lhscan_steps = 30  # Default value if LHscanSteps key is not found in config
        in_fit_section = False

        with open(config) as f:
            for line in f:
                # Check if we are in the fit block of the config...
                if line.strip().startswith("Fit:"):
                    in_fit_section = True
                elif in_fit_section and line.strip().startswith("LHscanSteps:"):
                    lhscan_steps = int(line.split(":")[1].strip())
                    print(
                        f"INFO: Found {lhscan_steps} steps for the likelihood scan in '{config}'"
                    )
                    break  # We found the key, so we can stop looking
                elif in_fit_section and line.strip() and not line.startswith("  "):
                    in_fit_section = False
                    print(
                        f"INFO: You did not specify 'LHscanSteps' in the fit block of '{config}'. Using default value of 30"
                    )

        return lhscan_steps

    def _build_job_file(
        self,
        config_region_syst_dict: dict,
        job_filename: str,
    ) -> None:
        """Generates a file containing the job information needed by condor_submit

        Parameters
        ----------
        config_region_syst_dict : dict
            Dictionary with config file names and associated regions and systematics
            in the schema returned by `_get_config_region_syst_dict`.
        job_filename : str
            Path to the script folder of the output directory.
        """
        outlines = []

        for config, region_syst_dict in config_region_syst_dict.items():
            short_config = os.path.splitext(os.path.basename(config))[0].replace(
                ".", "_"
            )

            if self.split_regions:
                for region in region_syst_dict["regions"]:
                    if self.split_systs:
                        # Build lists of systematics to be put into each file
                        for bundle_name, syst_bundle in sorted(
                            self._make_syst_bundle(region_syst_dict["systs"]).items()
                        ):
                            outlines.append(
                                f"{config} {short_config} {region} {bundle_name} {syst_bundle}"
                            )
                    else:
                        outlines.append(f"{config} {short_config} {region}")
            elif self.split_systs:
                for bundle_name, syst_bundle in sorted(
                    self._make_syst_bundle(region_syst_dict["systs"]).items()
                ):
                    outlines.append(
                        f"{config} {short_config} {bundle_name} {syst_bundle}"
                    )

            elif self.split_scan:
                lhscan_steps = self._get_lhscan_steps(config)
                for step in range(1, lhscan_steps + 1):
                    outlines.append(f"{config} {short_config} {step}")
            else:
                outlines.append(f"{config} {short_config}")

        with open(job_filename, "w") as f:
            f.write("\n".join(outlines))

    def _write_batch_bash(
        self,
        script_path: str,
        actions: str,
        extra_opts: list = None,
    ) -> None:
        """Writes bash-script executed on HTCondor

        Parameters
        ----------
        script_path : str
            Filepath of the bash-script to be generated.
        actions : str
            TRExFitter actions to be executed.
        extra_opts : list, optional
            Additional options to be supplied to TRExFitter in the format
            `<Option>=<Value>[,<Value2> ...]`. By default, no additional
            options are supplied, by default None
        """
        # Make sure we don't split up strings later
        extra_opts = [extra_opts] if isinstance(extra_opts, str) else extra_opts

        # Add all options in sequence
        opts = ["Regions=${region}"] if self.split_regions else []
        opts += (
            ["Systematics=${systs}", "SaveSuffix=_${suffix}"]
            if self.split_systs and self.split_regions
            else []
        )
        opts += (
            ["Ranking=${systs}"] if self.split_systs and not self.split_regions else []
        )
        opts += ["LHscanStep=${steps}"] if self.split_scan else []
        opts += [] if extra_opts is None else list(extra_opts)
        option_string = ":".join(opts)

        trex_setup_path = os.path.join(self.trex_folder, "setup.sh")

        with open(script_path, "w") as f:
            f.write("#!/bin/bash\n\n")
            # Get config (and region and systematic, if applicable), complain if we cannot
            f.write(
                "config=${1:?Config should be supplied as the first parameter but was not!}\n"
            )
            if self.split_regions:
                f.write(
                    "region=${2:?Region should be supplied as the second parameter but was not!}\n"
                )
            if self.split_systs and self.split_regions:
                f.write(
                    "suffix=${3:?Suffix should be supplied as the third parameter but was not!}\n"
                )
                f.write(
                    "systs=${4:?Systematics should be supplied as the fourth parameter but were not!}\n"
                )
            if self.split_systs and not self.split_regions:
                f.write(
                    "systs=${2:?Systematics should be supplied as the second parameter but were not!}\n"
                )
            if self.split_scan:
                f.write(
                    "steps=${2:?Step should be supplied as the second parameter but was not!}\n"
                )
            f.write("\n")
            f.write(
                f"cd {self.config_dir}\n"
            )  # Make the relative config paths work for us
            f.write(f"source {trex_setup_path}\n")
            # We should now have `trex-fitter` in our PATH, so can simply call it directly
            f.write(f'trex-fitter {actions} ${{config}} "{option_string}"\n')
            f.write("pwd\n")
            f.write("ls -l\n")

        # Lastly, we also have to make the script executable
        os.chmod(
            script_path,
            stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH,
        )

    def _write_htc_submit(
        self,
        submit_file_path: str,
        script_path: str,
        job_file: str,
        log_dir: str,
        result_dir: str = None,
        granularity: str = "global",
        arguments: list = None,
        run_time: int = None,
        num_cpu: int = None,
        universe: str = "vanilla",
    ) -> None:
        """Generates an HTCondor submission file

        Parameters
        ----------
        submit_file_path : str
            Filepath of the HTCondor submit file to be generated.
        script_path : str
            Filepath of the bash-script to be executed on the worker node(s).
        job_file : str
            Filepath of the file containing argument information for the
            individual jobs.
        log_dir : str
            Path to the folder in which logs should be saved.
        result_dir : str, optional
            Path to the folder into which results should be transferred if no
            shared filesystem between access point and worker nodes is available.
            By default, no file output transfer is performed, by default None
        granularity : str, optional
            Granularity, with which jobs should be launched. Here, `global` refers
            to a single job per config, `region` to one job per region, and `syst`
            to one job per systematic in each region. This has to be tuned to the
            information content of the `job_file`. By default, `global` granularity
            is used, by default "global"
        arguments : list | str, optional
            Extra arguments to be supplied to the bash-script. By default, no extra
            arguments are supplied beyond the job arguments from `job_file`,
            by default None
        run_time : int, optional
            Non-standard run-time to be requested for the jobs, by default None
        num_cpu : int, optional
            Non-standard amount of CPU cores to be requested for the jobs,
            by default None
        universe : str, optional
            Universe to run the HTCondor jobs in. By default, `vanilla` universe is
            used, by default "vanilla"

        Raises
        ------
        KeyError
            If `granularity` is not a key of `GRANULARITY_ARGS`.
        """
        # Check if the granularity makes sense
        if granularity not in self.GRANULARITY_ARGS:
            raise KeyError(
                f"\033[31mERROR: Unknown granularity '{granularity}'"
                f"(Options are : {self.GRANULARITY_ARGS.keys()})!\033[0m"
            )

        # Build arguments (first cluster and job ID, then possible arguments from the job_file, then anything else)
        arguments = [arguments] if isinstance(arguments, str) else arguments

        # Need all arguments coming from the file containing them
        job_file_args = self.GRANULARITY_ARGS[granularity]["job_file"]

        # We don't need the ShortConfig for the bash-scripts
        job_option_args = self.GRANULARITY_ARGS[granularity]["script_args"]
        job_option_args = [f"$({value})" for value in job_option_args]

        submit_args = job_option_args
        submit_args += [] if arguments is None else arguments
        submit_arg_string = " ".join(submit_args)

        # We don't want the full Config path for the logs
        log_job_args = self.GRANULARITY_ARGS[granularity]["log_args"]
        log_job_args = [f"$({value})" for value in log_job_args]
        log_job_options = ".".join(log_job_args)

        log_path = os.path.join(log_dir, f"TRExFitter.{self.actions}.$(ClusterId).log")
        out_path = os.path.join(
            log_dir,
            f"TRExFitter.{self.actions}.$(ClusterId).$(ProcId).{log_job_options}.out",
        )
        err_path = os.path.join(
            log_dir,
            f"TRExFitter.{self.actions}.$(ClusterId).$(ProcId).{log_job_options}.err",
        )

        with open(submit_file_path, "w") as f:
            f.write(f"universe = {universe}\n")
            f.write(f"executable = {script_path}\n")
            f.write(f"arguments = {submit_arg_string}\n\n")

            f.write("\n")
            f.write(f"log = {log_path}\n")
            f.write(f"output = {out_path}\n")
            f.write(f"error = {err_path}\n\n")

            # Only transfer files if needed
            if result_dir is not None:
                f.write("\n")
                f.write(f"initialdir = {result_dir}\n")
                f.write("should_transfer_files = YES\n")
                f.write("when_to_transfer_output = ON_EXIT\n\n")

            # Add explicitly supplied requirements
            if run_time is not None:
                # Not sure if this is a standard requirement as mandated by HTCondor...
                f.write(f"+RequestRuntime = {run_time:d}\n")
            if num_cpu is not None:
                f.write(f"RequestCpus = {num_cpu:d}\n")
            f.write('requirements = (OpSysAndVer =?= "CentOS7")\n\n')

            # Finally, add job queue statement (with arguments read in from `job_file`)
            f.write(f"queue {', '.join(job_file_args)} from {job_file}\n")

    # Arguments supplied to batch-system scripts for different granularities (have to be listed in a job-file then)
    GRANULARITY_ARGS = {
        "global": {
            "job_file": ["Config", "ShortConfig"],
            "script_args": ["Config"],
            "log_args": ["ShortConfig"],
        },
        "region": {
            "job_file": ["Config", "ShortConfig", "Region"],
            "script_args": ["Config", "Region"],
            "log_args": ["ShortConfig", "Region"],
        },
        "syst": {
            "job_file": ["Config", "ShortConfig", "Region", "Suffix", "Systematics"],
            "script_args": ["Config", "Region", "Suffix", "Systematics"],
            "log_args": ["ShortConfig", "Region", "Suffix"],
        },
        "ranking": {
            "job_file": ["Config", "ShortConfig", "Suffix", "Systematics"],
            "script_args": ["Config", "Systematics"],
            "log_args": ["ShortConfig", "Suffix"],
        },
        "lhscan": {
            "job_file": ["Config", "ShortConfig", "Step"],
            "script_args": ["Config", "Step"],
            "log_args": ["ShortConfig", "Step"],
        },
    }

    SUB_DIRS = {
        "scripts": "scripts",
        "logs": "logs",
        "configs": "configs",
        "results": "results",
    }

    CONFIG_KEYS_TO_PATH_CONVERT = [
        "OutputDir",
        "InputFolder",
    ]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Submits TRexFitter actions to an HTCondor batch system."
    )

    parser.add_argument(
        "work_dir",
        metavar="work-dir",
        type=os.path.abspath,
        help="Directory to store scripts, logs (and configs and outputs for "
        "`integrate-everything`) in.",
    )
    parser.add_argument(
        "trex_path",
        metavar="trex-path",
        type=os.path.abspath,
        help="Path to the root folder of the TRExFitter repo to use.",
    )
    parser.add_argument(
        "-a",
        "--actions",
        default=None,
        help="Actions to be carried out by TRexFitter. Common options are `n` "
        "(only to be submitted on its own!), `f`, `fp`, `wfp`, `dwfp` and their "
        "multi-fit equivalents prefixed with `m`, but check the relevant TRExFitter "
        "docs under https://trexfitter-docs.web.cern.ch for a full description.\n"
        "If no actions are submitted, only an update of the configs is performed.",
    )
    parser.add_argument(
        "-c",
        "--config",
        metavar="PATH",
        action="append",
        dest="trex_configs",
        type=os.path.abspath,
        help="TRExFitter config files to load. Can be supplied multiple times. "
        "If `integrate-everything` is not active or nothing was initialised yet, "
        "at least one config has to be supplied.",
    )
    parser.add_argument(
        "-u",
        "--use-config",
        metavar="CONFIG",
        action="append",
        dest="used_configs",
        help="TRExFitter config files to use in the current action. This option only "
        "has an effect if the tool is run in integrated mode to select specific "
        "configs to run with. The configs should already be present in cache or "
        "loaded in simultaneously using the `--config` option. No path, only "
        "the config name is required! If no configs are supplied via this option "
        "in integrated mode, all cached configs are used.",
    )
    parser.add_argument(
        "-o",
        "--option",
        metavar="OPT=VALUE",
        action="append",
        default=None,
        dest="trex_options",
        help="Extra options to supply to the TRExFitter executable. Must be supplied "
        "as`<Option>=<Value>[,<Value2> ...]`.",
    )
    parser.add_argument(
        "--integrate-everything",
        action="store_true",
        dest="integrate_everything",
        help="Instructs jobs to integrate configs and TRExFitter workspace. This "
        "then allows subsequent actions to make use of them instead of fine-tuning "
        "paths in the configs. Only has to be specified once (afterwards, subsequent "
        "jobs will automatically make use of stored configs and the output).",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Enables dry-run option, where all scripts are generated but not launched.",
    )
    parser.add_argument(
        "-t",
        "--transfer-output",
        action="store_true",
        dest="transfer_output",
        help="Enables transfer of outputs from the HTCondor worker nodes. Needed in "
        "case access point and worker nodes "
        "do not share a common filesystem.",
    )
    parser.add_argument(
        "-r",
        "--run-time",
        type=int,
        dest="run_time",
        default=None,
        help="Runtime for the jobs in seconds.",
    )
    parser.add_argument(
        "--split-scan",
        action="store_true",
        dest="split_scan",
        help="Instructs TRExFitter to carry out the 'x' action in multiple jobs for each step of the likelihood scan, specified in the config file.",
    )

    job_split_procedure = parser.add_mutually_exclusive_group()
    job_split_procedure.add_argument(
        "--single-reg",
        action="store_false",
        dest="split_regions",
        help="Instructs TRExFitter to carry out the `n`-action in a single job for "
        "all regions and systematics. "
        "(Implies option `--single-syst-n`)",
    )
    job_split_procedure.add_argument(
        "--single-np",
        action="store_false",
        dest="split_nps",
        help="Instructs TRExFitter to carry out the `n`- and `r`-actions in a single "
        "job for all nuisance parameters "
        "(pre region in case of the `n`-action).",
    )
    job_split_procedure.add_argument(
        "--nps-per-job",
        metavar="NUM_NPS",
        type=int,
        default=20,
        dest="num_nps_per_job",
        help="How many nuisance parameters to run per `n`-/`r`-job to avoid DDoSing "
        "input files. Has no impact on "
        "other actions.",
    )

    args = parser.parse_args()

    if (
        not args.used_configs
    ):  # Make it explicit that all configs will be used if none are given as parameters
        args.used_configs = None

    submit_jobs = TRExSubmit(
        config_list=args.trex_configs,
        trex_folder=args.trex_path,
        work_dir=args.work_dir,
        actions=args.actions,
        integrate_everything=args.integrate_everything,
        split_regions=args.split_regions,
        split_systs=args.split_nps,
        split_scan=args.split_scan,
        num_syst_per_job=args.num_nps_per_job,
        extra_opts=args.trex_options,
        run_time=args.run_time,
    )

    if args.actions is None:
        print(
            "INFO: No action applied, will only update configs! If you are "
            "not running in integrated mode, this will "
            "not have any effect!"
        )
    else:
        submit_jobs.build_and_submit(
            config_list=args.used_configs,
            dry_run=args.dry_run,
            stage_out_results=args.transfer_output,
        )

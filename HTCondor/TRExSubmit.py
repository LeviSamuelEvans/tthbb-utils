#!/usr/bin/env python3

"""
=================================================================================================
=== Python Script to run Condor batch jobs for different steps in TRExFitter 29.03.23 LE v1.0 ===
=================================================================================================

 - v0.1 named TRExSubmit_old.py now 06.01.23 Kept for posterity

 - v1.0 New features:
    - Split by systematic as well as region | results in ~ 1000 batch jobs
    - Ignore commented out regions/systematics
    - Ignore if syst/reg name is enclosed by double quote
    - parse through syst names with ; separating them

 - v2.0 New features:
    - Parsing of arguments - no need to hardcode in the python code anymore (only in the config structure)
    - Submission of all jobs in a single cluster instead of many clusters with one job each
    - Possibility to execute a dry-run - Generates ready-to-execute scripts for submission, but does not submit

 - v2.1 New features:
    - Detection of configs without systematics to fix a no-submission bug in these cases
    - Possibility to bundle multiple systematics per batch-job to reduce I/O load on ntuple files

Develop in this branch then merge in once ready.

 TODO: Nice to haves:
    - Copy configs and replacement file(s) into the work directory for easy access.
       - Would reduce the amount of hard-coding required in the configs wrt replacement files
       - Could also allow for automatic config gathering with workspace fetching in later steps
    - Add deployment possibilities via tarballs for batch systems where submit and worker nodes do not share a
      filesystem
    - Convert submission scripts to DAG for automatic hupdate jobs with split systematics
    - Use htcondor API library for job submission directly instead of using subprocess
"""

import sys
import os
import subprocess
import stat
# Used for type deduction in the docs
from typing import List, Dict, Optional


class TRExSubmit:
    """Class to steer HTCondor script creation and submission of the resulting jobs.

    :param List[str] config_list:
        List of config files to use for TRExFitter.
    :param str trex_folder:
        Path to root folder of TRExFitter repo used to run jobs on the batch system.
    :param str work_dir:
        Root directory to store scripts, logs, and more in.
    :param str actions:
        Actions to be executed by TRExFitter.
    :param bool or None split_regions:
        Whether to split supported actions by region (`True`) or not (`False`). By default, such actions are split.
    :param bool or None split_systs:
        Whether to split supported actions by systematic in each region (`True`) or not (`False`). By default, such
        actions are split.
    :param int or None num_syst_per_job:
        How many systematics to bundle per batch job during the `n` action, if neither `split_regions` nor `split_systs`
        is engaged.
    :param List[str] or None extra_opts:
        Extra options to be supplied to the TRExFitter executable. By default, no such options are supplied.

    :func build_and_submit:
        Overall function to create necessary scripts for batch-system submission and execute the resulting jobs.
    """
    def __init__(self,
                 config_list,
                 trex_folder,
                 work_dir,
                 actions,
                 split_regions=True,
                 split_systs=True,
                 num_syst_per_job=20,
                 extra_opts=None):
        self.config_list = config_list
        self.trex_folder = trex_folder
        self.work_dir = work_dir

        # Already define the subdirectories
        self.script_dir = os.path.join(self.work_dir, self.SUB_DIRS["scripts"])
        self.log_dir = os.path.join(self.work_dir, self.SUB_DIRS["logs"])
        # Only required if we want to keep configs and TRExFitter workspace in the work directory
        self.config_dir = os.path.join(self.work_dir, self.SUB_DIRS["configs"])
        self.workspace_dir = os.path.join(self.work_dir, self.SUB_DIRS["results"])

        # Make the work directory (pass if it's already present but fail if the parent directory is not there)
        try:
            os.mkdir(self.work_dir)
        except FileExistsError:
            pass

        # Read actions and make sure the `n` step is executed alone only to not have thousands of job failures from this
        self.actions = actions
        if 'n' in self.actions and not self.actions == 'n':
            print(
                f"\033[31mERROR: N-tuple translation action `n` should only be used alone, you used `{self.actions}`!"
                f"\033[0m",
                file=sys.stderr
            )
            sys.exit(1)

        # Check if we got any configs if we don't integrate
        if not self.config_list:
            print("\033[31mERROR: You cannot run without configs!\033[0m", file=sys.stderr)
            sys.exit(1)

        # It only makes sense to run regions separated if we have the `n` action included
        self.split_regions = split_regions if self.actions == 'n' else False
        # We automatically run systematics together if we run regions together
        self.split_systs = split_systs and self.split_regions
        self.num_syst_per_job = num_syst_per_job if self.split_systs else None
        self.extra_opts = [extra_opts] if isinstance(extra_opts, str) else extra_opts

        # Associate regions and systematics with config files (and check that we only have each region once)
        self.config_region_syst_dict = self._get_config_region_syst_dict(self.config_list)
        # Now check that we have at least one systematic - or disable the split by systematics
        self._check_update_systematic_split(self.config_region_syst_dict)

        # Build the correct key for the granularity-dict
        self.granularity = 'global'
        if self.split_regions:
            self.granularity = 'region'
        if self.split_systs:
            self.granularity = 'syst'

    def build_and_submit(self, dry_run=False, stage_out_results=False):
        """Execute the job submission

        Uses the values supplied during initialisation to generate HTCondor submit scripts and the actual bash-scripts
        to run on the worker nodes. Afterwards, submits the jobs if we are not in a dry-run.

        :param bool or None dry_run:
            Whether to actually submit the prepared jobs (`False`) or not (`True`). By default, the jobs are submitted
            to HTCondor.
        :param bool or None stage_out_results:
            Whether results of the fits need to be staged out of the worker nodes (`True`, in case access point and
            worker node don't share a filesystem) or not (`False`). By default, no need to stage out results is assumed.
        """
        os.makedirs(self.script_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.workspace_dir, exist_ok=True)

        condor_result_dir = self.workspace_dir if stage_out_results else None

        # Define custom output folder in TRExFitter CL-options if we have a shared filesystem
        if not stage_out_results and self.extra_opts is None:
            self.extra_opts = f"OutputDir={self.workspace_dir}"
        elif not stage_out_results:
            self.extra_opts += [f"OutputDir={self.workspace_dir}"]

        job_file = os.path.join(self.script_dir, f"job_arguments_{self.actions}.txt")
        script_file = os.path.join(self.script_dir, f"script_{self.actions}.sh")
        submit_file = os.path.join(self.script_dir, f"submit_{self.actions}.sub")

        self._build_job_file(self.config_region_syst_dict, job_file)
        self._write_batch_bash(script_file, self.actions, self.extra_opts)
        self._write_htc_submit(
                submit_file,
                script_file,
                job_file,
                self.log_dir,
                result_dir=condor_result_dir,
                granularity=self.granularity
        )

        if dry_run:
            print(f"INFO: In dry-run, submit files can be found in {self.work_dir}")
        else:
            print(f"INFO: Submitting jobs...")
            proc = subprocess.run(["condor_submit", submit_file], stdout=sys.stdout, stderr=sys.stderr)
            sys.exit(proc.returncode)

    def _get_config_region_syst_dict(self, config_list) -> Dict[str, Dict[str, List[str]]]:
        """Retrieves regions and systematics from multiple TRExFitter configs and checks region uniqueness

        The dictionary returned by this function has the following form:
        ```
            <config1>: {regions: [<region1>, <region2>, ..., <regionN>], systs: [<syst1.1>, <syst1.2>, ...]},
            <config2>: {regions: [<regionN+1>, ...], systs: [<syst2.1,>, ...]},
            ...
        ```

        The function raises an error if some region is present in multiple configs, as this will mess up
        ntuple-histogram conversion.

        :param List[str] config_list:
            List of TRExFitter config paths.

        :returns:
            Dictionary associating regions and systematics to the configs in the schema described above.
        :rtype: Dict[str, Dict[str, List[str]]]

        :raises RuntimeError:
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
                raise RuntimeError(f"Regions {list(region_intersection)} in '{config}' were already present!")

            # Add the new regions to our check_set
            region_check_set |= set(config_regions)

            # Now add all to the overall dict
            config_region_syst_dict[config] = {
                'regions': config_regions,
                'systs': config_systs,
            }

        return config_region_syst_dict

    @staticmethod
    def _get_region_list(config) -> List[str]:
        """Retrieves regions from TRExFitter config

        :param str config:
            Path to TRExFitter config.

        :returns:
            List of regions in config.
        :rtype: List[str]
        """
        region_list = []

        with open(config) as conf:
            for line in conf:
                line = line.split('%')[0].strip()

                if 'Region:' not in line or 'FitRegion' in line:
                    continue

                region = line.split(":")[1].strip()

                # Check if the region name is enclosed by double quotes, remove them if so
                if region.startswith('"') and region.endswith('"'):
                    region = region[1:-1]

                region_list.append(region)

        print(f"INFO: Regions found in '{config}':")
        for region in region_list:
            print(f"       - {region}")

        return region_list

    @staticmethod
    def _get_syst_list(config) -> List[str]:
        """Retrieves systematics from TRExFitter config

        :param str config:
            Path to TRExFitter config.

        :returns:
            List of systematics in config.
        :rtype: List[str]
        """
        syst_list = []

        with open(config) as f:
            for line in f:
                line = line.split('%')[0].strip()

                if line.startswith('#'):
                    continue
                if 'Systematic:' not in line:
                    continue

                syst_line = line.split(":")[1].strip()

                # Split the systematic names by semicolon and add them to the syst_list
                for syst in syst_line.split(';'):
                    syst = syst.strip()  # Remove any spaces before and after the systematic name

                    # Check if the systematic names are enclosed by double quotes
                    if syst.startswith('"') and syst.endswith('"'):
                        syst = syst[1:-1]  # Remove the double quotes

                    syst_list.append(syst)

        # Only print systematics if we found any
        if not syst_list:
            print(f"INFO: No systematics found in '{config}'")
        else:
            print(f"INFO: Systematics found in '{config}':")
            for syst in syst_list:
                print(f"      - {syst}")

        return syst_list

    def _check_update_systematic_split(self, config_region_syst_dict):
        """Check number of systematics per config and region for job splits

        :param Dict[str, Dict[str, List[str]]] config_region_syst_dict:
            Dictionary with config file names and associated regions and systematics in the schema returned by
            `_get_config_region_syst_dict`.
        """
        # No need to do anything if we already do not split by systematics
        if not self.split_systs:
            return

        for config, region_syst_dict in config_region_syst_dict.items():
            if not region_syst_dict['systs']:
                print(
                    f"INFO: No systematics present for config '{config}'.\n"
                    f"      Disabling systematics split in condor jobs..."
                )
                self.split_systs = False
                break

    def _make_syst_bundle(self, systematics_list) -> List[str]:
        """Bundles systematics into groups to reduce file I/O load

        The systematics will be bundled with `num_syst_per_job` systematics per bundle. Systematics are separated by `,`
        as per TRExFitter conventions.

        :param List[str] systematics_list:
            List of systematics to be bundled.

        :returns
            List of bundles systematics separated by `,`.
        :rtype: list of str
        """
        syst_bundles = []
        tmp_syst_list = []

        for syst in systematics_list:
            if len(tmp_syst_list) < self.num_syst_per_job:
                tmp_syst_list.append(syst)
            else:
                syst_bundles.append(','.join(tmp_syst_list))
                tmp_syst_list.clear()

        # Final fill with possible left-over systematics
        if tmp_syst_list:
            syst_bundles.append(','.join(tmp_syst_list))

        return syst_bundles

    def _build_job_file(self, config_region_syst_dict, job_filename):
        """Generates a file containing the job information needed by condor_submit

        :param Dict[str, Dict[str, List[str]]] config_region_syst_dict:
            Dictionary with config file names and associated regions and systematics in the schema returned by
            `_get_config_region_syst_dict`.
        :param str job_filename:
            Path to the script folder of the output directory.
        """
        outlines = []

        for config, region_syst_dict in config_region_syst_dict.items():
            short_config = os.path.splitext(os.path.basename(config))[0].replace('.', '_')
            if not self.split_regions:
                outlines.append(f"{config} {short_config}")
                continue

            for region in region_syst_dict['regions']:
                if not self.split_systs:
                    outlines.append(f"{config} {short_config} {region}")
                    continue

                # Build lists of systematics to be put into each file
                for syst_bundle in self._make_syst_bundle(region_syst_dict['systs']):
                    outlines.append(f"{config} {short_config} {region} {syst_bundle}")

        with open(job_filename, 'w') as f:
            f.write('\n'.join(outlines))

    def _write_batch_bash(self, script_path, actions, extra_opts=None):
        """Writes bash-script executed on HTCondor

        :param str script_path:
            Filepath of the bash-script to be generated.
        :param str actions:
            TRExFitter actions to be executed.
        :param List[str] or str or None extra_opts:
            Additional options to be supplied to TRExFitter in the format `<Option>=<Value>[,<Value2> ...]`.
            By default, no additional options are supplied.
        """
        # Make sure we don't split up strings later
        extra_opts = [extra_opts] if isinstance(extra_opts, str) else extra_opts

        # Add all options in sequence
        opts = ['Regions=${region}'] if self.split_regions else []
        opts += ['Systematics=${syst}', 'SaveSuffix=_${syst}'] if self.split_systs else []
        opts += [] if extra_opts is None else list(extra_opts)
        option_string = ":".join(opts)

        trex_setup_path = os.path.join(self.trex_folder, 'setup.sh')

        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\n\n")
            # Get config (and region and systematic, if applicable), complain if we cannot
            f.write("config=${1:?Config should be supplied as the first parameter but was not!}\n")
            if self.split_regions:
                f.write("region=${2:?Region should be supplied as the second parameter but was not!}\n")
            if self.split_systs:
                f.write("syst=${3:?Systematic should be supplied as the third parameter but was not!}\n")
            f.write("\n")
            f.write(f"source {trex_setup_path}\n")
            # We should now have `trex-fitter` in our PATH, so can simply call it directly
            f.write(f"trex-fitter {actions} ${{config}} \"{option_string}\"\n")
            f.write("pwd\n")
            f.write("ls -l\n")

        # Lastly, we also have to make the script executable
        os.chmod(script_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

    def _write_htc_submit(self,
                          submit_file_path,
                          script_path,
                          job_file,
                          log_dir,
                          result_dir=None,
                          granularity='global',
                          arguments=None,
                          run_time=None,
                          num_cpu=None,
                          universe='vanilla'):
        """Generates an HTCondor submission file

        :param str submit_file_path:
            Filepath of the HTCondor submit file to be generated.
        :param str script_path:
            Filepath of the bash-script to be executed on the worker node(s).
        :param str job_file:
            Filepath of the file containing argument information for the individual jobs.
        :param str log_dir:
            Path to the folder in which logs should be saved.
        :param str or None result_dir:
            Path to the folder into which results should be transferred if no shared filesystem between access point and
            worker nodes is available. By default, no file output transfer is performed.
        :param str or None granularity:
            Granularity, with which jobs should be launched. Here, `global` refers to a single job per config, `region`
            to one job per region, and `syst` to one job per systematic in each region. This has to be tuned to the
            information content of the `job_file`. By default, `global` granularity is used.
        :param List[str] or str or None arguments:
            Extra arguments to be supplied to the bash-script. By default, no extra arguments are supplied beyond the
            job arguments from `job_file`.
        :param int or None run_time:
            Non-standard run-time to be requested for the jobs.
        :param int or None num_cpu:
            Non-standard amount of CPU cores to be requested for the jobs.
        :param str or None universe:
            Universe to run the HTCondor jobs in. By default, `vanilla` universe is used.

        :raises KeyError:
            If `granularity` is not a key of `GRANULARITY_ARGS`.
        """
        # Check if the granularity makes sense
        if granularity not in self.GRANULARITY_ARGS:
            raise KeyError(f"\033[31mERROR: Unknown granularity '{granularity}'"
                           f"(Options are : {self.GRANULARITY_ARGS.keys()})!\033[0m")

        # Build arguments (first cluster and job ID, then possible arguments from the job_file, then anything else)
        arguments = [arguments] if isinstance(arguments, str) else arguments

        # Need all arguments coming from the file containing them
        job_file_args = ["Config", "ShortConfig"] + self.GRANULARITY_ARGS[granularity]

        # We don't need the ShortConfig for the bash-scripts
        job_option_args = ["Config"] + self.GRANULARITY_ARGS[granularity]
        job_option_args = [f"$({value})" for value in job_option_args]

        submit_args = job_option_args
        submit_args += [] if arguments is None else arguments
        submit_arg_string = ' '.join(submit_args)

        # We don't want the full Config path for the logs
        log_job_args = ["ShortConfig"] + self.GRANULARITY_ARGS[granularity]
        log_job_args = [f"$({value})" for value in log_job_args]
        log_job_options = '.'.join(log_job_args)

        log_path = os.path.join(log_dir, f'TRExFitter.{self.actions}.$(ClusterId).log')
        out_path = os.path.join(log_dir, f'TRExFitter.{self.actions}.$(ClusterId).$(ProcId).{log_job_options}.out')
        err_path = os.path.join(log_dir, f'TRExFitter.{self.actions}.$(ClusterId).$(ProcId).{log_job_options}.err')

        with open(submit_file_path, 'w') as f:
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
            f.write("requirements = (OpSysAndVer =?= \"CentOS7\")\n\n")

            # Finally, add job queue statement (with arguments read in from `job_file`)
            f.write(f"queue {', '.join(job_file_args)} from {job_file}\n")

    # Arguments supplied to batch-system scripts for different granularities (have to be listed in a job-file then)
    GRANULARITY_ARGS = {
        'global': [],
        'region': ['Region'],
        'syst':   ['Region', 'Systematic'],
    }

    SUB_DIRS = {
        'scripts': 'scripts',
        'logs':    'logs',
        'configs': 'configs',
        'results': 'results',
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Submits TRexFitter actions to an HTCondor batch system.")

    parser.add_argument(
        'trex_path', type=os.path.abspath, help='Path to the root folder of the TRExFitter repo to use.')
    parser.add_argument(
        'actions',
        help='Actions to be carried out by TRexFitter. Common options are `n` (only to be submitted on its own!),'
             '`f`, `fp`, `wfp`, `dwfp` and their multi-fit equivalents prefixed with `m`, but check the relevant'
             'TRExFitter docs under https://trexfitter-docs.web.cern.ch for a full description.'
    )
    parser.add_argument(
        '-c', '--config', metavar='PATH', action='append', dest='trex_configs', type=os.path.abspath,
        help='TRExFitter config files to use. Can be supplied multiple times.'
    )
    parser.add_argument(
        '-o', '--option', metavar='OPT=VALUE', action='append', default=None, dest='trex_options',
        help='Extra options to supply to the TRExFitter executable. Must be supplied as'
             '`<Option>=<Value>[,<Value2> ...]`.'
    )
    parser.add_argument(
        '-w', '--work-dir', metavar='PATH', default=os.path.abspath(os.getcwd()), dest='work_dir', type=os.path.abspath,
        help='Directory to store configs, scripts, logs, and outputs in. Defaults to current directory'
             '(currently %(default)s).'
    )
    parser.add_argument(
        '-n', '--dry-run', action='store_true', dest='dry_run',
        help='Enables dry-run option, where all scripts are generated but not launched.'
    )
    parser.add_argument(
        '-t', '--transfer-output', action='store_true', dest='transfer_output',
        help='Enables transfer of outputs from the HTCondor worker nodes. Needed in case access point and worker nodes'
             'do not share a common filesystem.'
    )

    job_split_procedure = parser.add_mutually_exclusive_group()
    job_split_procedure.add_argument(
        '--single-reg-n', action='store_false', dest='split_regions',
        help='Instructs TRExFitter to carry out the `n`-action in a single job for all regions and systematics.'
             '(Implies option `--single-syst-n`)'
    )
    job_split_procedure.add_argument(
        '--single-syst-n', action='store_false', dest='split_systs',
        help='Instructs TRExFitter to carry out the `n`-action in a single job for all systematics per region.'
    )
    job_split_procedure.add_argument(
        '--syst-per-job', metavar='NUM_SYSTS', type=int, default=20, dest='num_syst_per_job',
        help='How many systematics to run per `n`-job to avoid DDoSing input files. Has no impact on other actions.'
    )

    args = parser.parse_args()

    submit_jobs = TRExSubmit(
            args.trex_configs,
            args.trex_path,
            args.work_dir,
            args.actions,
            split_regions=args.split_regions,
            split_systs=args.split_systs,
            num_syst_per_job=args.num_syst_per_job,
            extra_opts=args.trex_options
    )
    submit_jobs.build_and_submit(dry_run=args.dry_run, stage_out_results=args.transfer_output)

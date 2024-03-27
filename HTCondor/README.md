### TRExFitter Batch Submission

`TRExSubmit.py` is a python script that facilitates the submission of TRExFitter jobs to a HTCondor batch system. It automates the process of generating HTCondor submit scripts and bash scripts to run on the worker nodes, and additionally submits these jobs to the batch system.

For an introduction to HTCondor, please see the following documentation at the [CERN Batch Submission Guide](https://batchdocs.web.cern.ch/index.html). For an overview of TRExFitter and some introductory tutorials, please see the central [TRExFitter Documentation](https://trexfitter-docs.web.cern.ch/trexfitter-docs/).


#### Brief Overview and features:

The script currently supports the following:

- The running of various TRExFitter `actions`, such as `n`, `w`, `f`, `d`, `p`, `l`, `r`, etc.,  and their multi-fit equivalents. These options can also be grouped together to run specicifc ations within the same jobs.
- The script allows the distribution of jobs per region and systematic. This is particularly useful mainly for the distribution of jobs for the histogram generation step, in which the generation can be time-consuming when running over all regions and systematics in one job. It is also convinient for the distribuion of ranking jobs and plotting.
- The script provides the option to run in `integrated-mode`, in which the configs and workspaces will integrated into the working directory for a more seamless execution.
- The script provides a dry-run mode, to generate scripts without submitting jobs. You can then subsequently submit these jobs using `condor_submit submit_<action>.sub`, found inside the `scripts` folder of the working directory.
- The script enables the transfer of output files from the worker nodes if a shared filesystem is not available.
- Finally, the script also offers some additional flexibility when it comes to specifying additional command-line options to the TRExFitter jobs, e.g. this can be useful for the application of fit results to specific channel distributions.

#### Usage:

To use the `TRExSubmit` script, run the script with the following command-line arguments:

```
python3 TRExSubmit.py <work-dir> <trex-path> [options]
```

where,
- `<work-dir>:` The working directory to store submit scripts, logs, job arguments, and optionally the configs and outputs
- `<trex-path>:` The path to the root folder of your cloned TRExFitter repository (so we can source the setup and run the associated execuatble in the jobs.)

The available options are then the following:

| Option                    | Description                                                                                      |
| ------------------------- | ------------------------------------------------------------------------------------------------ |
| `-a`, `--actions`         | Specify the actions to be carried out by TRExFitter.                                             |
| `-c`, `--config`          | Provide one or more TRExFitter config files to load. (You can supply this option multiple times) |
| `-u`, `--use-config`      | Specify config files to use in the current action (only applicable in integrated mode).          |
| `-o`, `--option`          | Supply extra options to the TRExFitter executable.                                               |
| `--integrate-everything`  | Integrate configs and TRExFitter workspace into the working directory.                           |
| `-n`, `--dry-run`         | Enable dry-run mode to generate scripts without submitting jobs.                                 |
| `-t`, `--transfer-output` | Enable transfer of output files from worker nodes.                                               |
| `-r`, `--run-time`        | Specify the runtime for the jobs in seconds.                                                     |
| `--split-scan`            | Carry out the likelihood scan action in multiple jobs for each step.                             |
| `--single-reg`            | Carry out the `n`-action in a single job for all regions and systematics.                        |
| `--single-np`             | Carry out the `n`- and `r`-actions in a single job for all nuisance parameters.                  |
| `--nps-per-job`           | Specify the number of nuisance parameters to run per `n`-/`r`-job (The default is 30).                               |

For further details on these running options and their usage, refer to the script's help messege by running `python3 TRExSubmit.py -h`.

#### Handling Failed Jobs
Additionally, inside the `utils` folder of `HTCondor`, you will find a script, `retry_jobs.py`. In the case that some jobs failed during the execution, this script can be used to identify and resubmit the failed jobs.

To use the script, run the script with the following command-line arguments:

```
python3 retry_jobs.py -d <directory> -o <output_log> -a <original_args_file> -n <new_args_file> -t <trex-fitter step> -e "CustomError1" -e "CustomError2"
```

where the options are the following:

| Option              | Description                                                                    |
| ------------------- | ------------------------------------------------------------------------------ |
| `-d`, `--directory` | Directory containing the `.err` files (logs) of the failed jobs.               |
| `-o`, `--output`    | The name of the output log file to store job failure information.              |
| `-a`, `--args`      | The original job arguments file used by `TRExSubmit`.                          |
| `-n`, `--newargs`   | The name of the new arguments file to be created for retrying the failed jobs. |
| `-s`, `--steps`     | The TRExFitter step used (e.g., `n`, `f`, `fp`, etc.).                         |
| `-e`, `--error`     | Additional error messages to search for in .err log files                      |

The script will then create a new job arguments files you can use to re-run the failed jobs. An additional log file will also be created to log the reason for the job failure.

For further details on these running options and their usage, refer to the script's help messege by running `python3 retry_jobs -h`.
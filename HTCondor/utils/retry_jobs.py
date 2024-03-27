#!/usr/bin/env python3

import os
import re
import argparse

"""
This script defines a class `CondorJobHandler` that handles failed Condor jobs by checking for errors in the job output logs,
extracting the names of the failed jobs, and creating a new arguments file for retrying the failed jobs.

Usage: ./retry_jobs.py -d <directory> -o <output_log> -a <original_args_file> -n <new_args_file> -t <trex-fitter step>

Example: ./retry_jobs.py -d path/to/logs/ -o failed_1l_jobs.log -a path/to/job_arguments.txt -n args_1l_retry.txt -s n

Note: You'll then need to copy the new output arguments file to the base directory of the condor workspace.
       (i.e. from original TRExSubmit script output folder)
      You can add additional/different errors to the ERROR_MESSAGES list.

TODO:
    - Add job number to log so we can repeat for multiple jobs
"""

# Default errors to check for in the job output logs
ERROR_MESSAGES = [
    "trex-fitter: command not found",
    "Error in <TFile::TFile>:",
    "ERROR::SampleHist::SmoothSyst",
]

def _clear_log_file(output_log):
        # Open the log file
        with open(output_log, mode='w') as log_file:
            log_file.truncate(0)  # Clear any previous log file contents

class CondorJobHandler:
    """
    A class that handles failed Condor jobs by checking for errors in the job output logs,
    extracting the names of the failed jobs, and creating a new arguments file for retrying
    the failed jobs.
    """

    def __init__(self, directory, output_log, original_args_file, new_args_file, steps) -> None:
        """
        Initialises a CondorJobHandler object with the given directory, output log file,
        original arguments file, new arguments file and trex step.

        Args:
        - directory (str): The directory containing the output logs for the Condor jobs.
        - output_log (str): The path to the output log file for storing error messages.
        - original_args_file (str): The path/name to the original arguments file for the Condor jobs.
        - new_args_file (str): The path/name of the new arguments file to be created for retrying
          the failed jobs.
        - steps (str): The trex-fitter step used.
        """
        self.directory = directory
        self.output_log = output_log
        self.original_args_file = original_args_file
        self.new_args_file = new_args_file
        self.steps = steps

    def check_errors(self) -> None:
        """
        Checks the condor logs for errors in the jobs and writes any error messages
        to the user specified output log file.
        """
        # Loop over error files in the directory
        for filename in os.listdir(self.directory):
            if filename.endswith(".err"):
                with open(os.path.join(self.directory, filename), "r") as file:
                    contents = file.read()
                    # Check for the user-specified errors in the file contents
                    if any(error in contents for error in ERROR_MESSAGES):
                        output_str = f"File: {filename}\nContents:\n{contents}\n\n"
                        with open(self.output_log, "a") as output_file:
                            output_file.write(output_str)

    def extract_failed_jobs(self):
        """
        Extracts the names of the failed jobs from the created output log file.
        """
        # Create an empty list to store the failed jobs
        failed_jobs = []

        with open(self.output_log, 'r') as f:
            lines = f.readlines()
        for line in lines:
            match = re.search(r'TRExFitter\.' + self.steps + r'\.\d+\.\d+\.(config_.+?)\.err', line)
            if match:
                failed_job = match.group(1)
                # Ensure the job name is a separate string
                failed_job = failed_job.strip()
                print(f"Extracted failed job: {failed_job}")
                failed_jobs.append(failed_job)
        if len(failed_jobs) == 0:
            print("No failed jobs found! :D")
        else:
            print(f"Number of failed jobs: {len(failed_jobs)}")
        return failed_jobs

    def create_new_args_file(self, failed_jobs) -> None:
        """
        Creates a new arguments file for retrying the failed jobs.
        """

        with open(self.original_args_file, 'r') as f:
            lines = f.readlines()

        with open(self.new_args_file, 'w') as f:
            for job in failed_jobs:
                # Replace the dot in the job name with a space to match the args file format
                formatted_job = job.replace('.', ' ')
                for line in lines:
                     # stripe the newline character from the line
                    line = line.rstrip('\n')
                    if formatted_job in line:
                        f.write(line + '\n')
        print(f"New arguments file created: {self.new_args_file}")
        print("Please, copy the new arguments file to the base directory of the condor workspace")

    def handle_failed_jobs(self):
        """
        Handles the failed jobs by checking for errors, extracting the names of the failed jobs,
        and creating a new arguments file for retrying the failed jobs.
        """

        self.check_errors()
        failed_jobs = self.extract_failed_jobs()
        self.create_new_args_file(failed_jobs)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Handle failed Condor jobs.")

    parser.add_argument(
        "-d", "--directory",
        type=str,
        required=True,
        help="Directory containing the .err files.")

    parser.add_argument(
        "-o", "--output",
        type=str,
        required=True,
        help="The name to call the output log file with job"
        "failure information")

    parser.add_argument(
        "-a", "--args",
        type=str,
        required=True,
        help="The original job arguments file.")

    parser.add_argument(
        "-n", "--newargs",
        type=str,
        required=True,
        help="The name of the new arguments file.")

    parser.add_argument(
        "-s", "--steps",
        type=str,
        required=True,
        help="The trex-fitter step used.")

    args = parser.parse_args()

    _clear_log_file(args.output)

    handler = CondorJobHandler(args.directory, args.output, args.args, args.newargs, args.steps)
    handler.handle_failed_jobs()
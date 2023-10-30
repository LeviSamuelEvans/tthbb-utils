#!/usr/bin/env python3

import os
import re
import argparse

"""
Description:
    - This script defines a class `CondorJobHandler` that handles failed Condor jobs by checking for errors in the job output logs,
    extracting the names of the failed jobs, and creating a new arguments file for retrying the failed jobs. The class has four
    methods: `__init__`, `check_errors`, `extract_failed_jobs`, and `create_new_args_file`. The script also includes a main
    function that parses command line arguments and creates an instance of the `CondorJobHandler` class to handle the failed jobs.

Usage:
    - ./retry_jobs.py -d <directory> -o <output_log> -a <original_args_file> -n <new_args_file>

Notes:
    - You'll then need to either copy the new output arguments to the base directory of the condor workspace or
      rename the job arguments file used in the .sh file of the job submitter
      (i.e. from original TRExSubmit script output folder)
"""

class CondorJobHandler:
    """
    A class that handles failed Condor jobs by checking for errors in the job output logs,
    extracting the names of the failed jobs, and creating a new arguments file for retrying
    the failed jobs.
    """

    def __init__(self, directory, output_log, original_args_file, new_args_file):
        """
        Initializes a CondorJobHandler object with the given directory, output log file,
        original arguments file, and new arguments file.

        Args:
        - directory (str): The directory containing the output logs for the Condor jobs.
        - output_log (str): The path to the output log file for storing error messages.
        - original_args_file (str): The path to the original arguments file for the Condor jobs.
        - new_args_file (str): The path to the new arguments file to be created for retrying
          the failed jobs.
        """
        self.directory = directory
        self.output_log = output_log
        self.original_args_file = original_args_file
        self.new_args_file = new_args_file

    def check_errors(self):
        """
        Checks the output logs for errors in the Condor jobs and writes any error messages
        to the output log file.
        """
        for filename in os.listdir(self.directory):
            if filename.endswith(".err"):
                with open(os.path.join(self.directory, filename), "r") as file:
                    contents = file.read()
                    # Find common TREx errors
                    if "trex-fitter: command not found" in contents or "Error in <TFile::TFile>:" in contents:
                        output_str = f"File: {filename}\nContents:\n{contents}\n\n"
                        with open(self.output_log, "a") as output_file:
                            output_file.write(output_str)

    def extract_failed_jobs(self):
        """
        Extracts the names of the failed jobs from the output log file.

        Returns:
        - failed_jobs (list): A list of strings representing the names of the failed jobs.
        """
        failed_jobs = []
        with open(self.output_log, 'r') as f:
            lines = f.readlines()
            for line in lines:
                # Updated regex to capture any config name
                match = re.search(r'TRExFitter\.r\.\d+\.\d+\.(config_.+?)\.err', line)
                if match:
                    failed_jobs.append(match.group(1))
        return failed_jobs


    def create_new_args_file(self, failed_jobs):
        """
        Creates a new arguments file for retrying the failed jobs.

        Args:
        - failed_jobs (list): A list of strings representing the names of the failed jobs.
        """
        with open(self.original_args_file, 'r') as f:
            lines = f.readlines()

        with open(self.new_args_file, 'w') as f:
            for job in failed_jobs:
                for line in lines:
                    if job in line:
                        f.write(line)

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
    parser.add_argument("-d", "--directory", type=str, required=True, help="Directory containing the .err files.")
    parser.add_argument("-o", "--output", type=str, required=True, help="Output log file.")
    parser.add_argument("-a", "--args", type=str, required=True, help="Original arguments file.")
    parser.add_argument("-n", "--newargs", type=str, required=True, help="New arguments file.")
    args = parser.parse_args()

    handler = CondorJobHandler(args.directory, args.output, args.args, args.newargs)
    handler.handle_failed_jobs()
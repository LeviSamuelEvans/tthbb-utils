# ============================================================================== #
# == Script to merge Histograms together when splitting by region and systematic #
# ============================================================================== #

"""
Usage:
    Requires a yaml configuration file with following structure :
"""

import os
import subprocess
import yaml
import argparse

# Define command-line options
parser = argparse.ArgumentParser(description='Merge histograms with systematics')
parser.add_argument('--systematics', type=str, choices=['STXS', 'inc'], default='STXS',
                    help='which block of systematics to use (default: %(default)s)')
args = parser.parse_args()

# Read the YAML file
with open('merge_1l_inclusive.yaml', 'r') as file:
    file_paths = yaml.safe_load(file)

# Get the input file paths from the YAML file, with error handling
try:
    input_files = file_paths['input_files']
except KeyError:
    print("Error: 'input_files' key not found in merge_1l_inclusive.yaml")
    exit(1)

# Get the baseline output file paths from the YAML file, with error handling
try:
    baseline_output_files = file_paths['baseline_output_files']
except KeyError:
    print("Error: 'baseline_output_files' key not found in merge_1l_inclusive.yaml")
    exit(1)

# Get the list of systematics from the YAML file based on the command-line option
if args.systematics == 'STXS':
    try:
        systematics = file_paths['systematics_STXS']
    except KeyError:
        print("Error: 'systematics_STXS' key not found in merge.yaml")
        exit(1)
elif args.systematics == 'inc':
    try:
        systematics = file_paths['systematics_inc']
    except KeyError:
        print("Error: 'systematics_inc' key not found in merge.yaml")
        exit(1)
else:
    print("Error: Invalid option for '--systematics'. Must be 'STXS' or 'inc'")
    exit(1)

# Loop through the input files and baseline output files and generate the output filenames
for input_file, baseline_output_file in zip(input_files, baseline_output_files):
    # Initialize the list of output files
    output_files = []

    # Loop through the list of systematics and generate the output filenames
    for systematic in systematics:
        # Format the output filename with the systematic
        output_file = baseline_output_file.format(systematic)

        # Append the output file to the list of output files
        output_files.append(output_file)

    # Join the list of output files as a single string
    output_files_str = ' '.join(output_files)

    # Define the command
    executable2 = "/scratch4/levans/TRExFitter_v4.17/TRExFitter/build/bin/hupdate.exe"
    hupdate_cmd = f"{executable2} {input_file} {output_files_str}"
    print(hupdate_cmd)
    # Run the hupdate command in the terminal
    subprocess.run(hupdate_cmd, shell=True, check=True)
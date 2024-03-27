#!/usr/bin/env python3

# ============================================================================== #
# == Script to merge Histograms together when splitting by region and systematic #
# ============================================================================== #

"""
Usage:
    Requires a yaml configuration file.
    Example file in tthbb_legacy_utilities/HTCondor/merge_1l.yaml
"""

"""
- v0.1  Basic merging script using hupdate

- v1.0 Added features:
    - yaml config file
    - some options specified

- v1.1 Added features:
    - more options to use, less hard-coding in code
    - automatically compile TRExFitter with input path
    - more error handling

 TODO: Nice to haves:
    - some auto generation of .yaml configs used, link to Condor script for n Job submission perhaps?
    - the script getSystList.py can be used here

"""

import os
import subprocess
import yaml
import argparse
import sys

# Define command-line options
parser = argparse.ArgumentParser(description='Merge TRExFitter histograms when split by region and systematics')
parser.add_argument('-c','--config', type=os.path.abspath,
                    help='path to merging YAML config file to use')
parser.add_argument('-s','--systematics', type=str, choices=['stxs', 'inc'], default='stxs',
                    help='which block of systematics to use (default: %(default)s)')
parser.add_argument('-d', '--directory', type=str,
                    help='the path to the directory containing the .root Histograms to be merged')
parser.add_argument('-t', '--trexfitter-path', type=str,
                    help='the path to the TRExFitter top directory')

# Print usage instructions if no arguments are provided
if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(0)

args = parser.parse_args()

# Set up TRExFitter environment
if args.trexfitter_path is not None:
    trexfitter_setup_script = os.path.join(args.trexfitter_path, 'setup.sh')
    if os.path.isfile(trexfitter_setup_script):
        subprocess.run(f"source {trexfitter_setup_script}", shell=True, check=True)
    else:
        print("\033[91mError: TRExFitter setup script (setup.sh) not found. Please ensure the correct path is provided.\033[0m")
        sys.exit(1)
else:
    print("\033[91mError: Please provide the path to the TRExFitter installation directory using the -t or --trexfitter-path option.\033[0m")
    sys.exit(1)

# Read the YAML file
with open('merge_1l.yaml', 'r') as file:
    file_paths = yaml.safe_load(file)

# Get the input file paths from the YAML file, with error handling
try:
    input_files = [os.path.join(args.directory, file) for file in file_paths['input_files']]
except KeyError:
    print("Error: 'input_files' key not found in merge.yaml")
    exit(1)


# Get the baseline output file paths from the YAML file, with error handling
try:
    baseline_output_files = [os.path.join(args.directory, file) for file in file_paths['baseline_output_files']]
except KeyError:
    print("Error: 'baseline_output_files' key not found in merge_1l_inclusive.yaml")
    exit(1)

# Get the list of systematics from the YAML file based on the command-line option
if args.systematics == 'stxs':
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

# Check if the directory option is provided
if args.directory is None:
    print("Error: Please provide the directory path with the Histograms to be merged using the --directory option.")
    exit(1)

# Set the working directory to the provided directory path
os.chdir(args.directory)

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
    exec = "/scratch4/levans/TRExFitter_v4.17/TRExFitter/build/bin/hupdate.exe"
    hupdate_cmd = f"{exec} {input_file} {output_files_str}"
    print(hupdate_cmd)
    # Run the hupdate command in the terminal
    subprocess.run(hupdate_cmd, shell=True, check=True)

print("\033[92mAll histograms merged, happy fitting!\033[0m")
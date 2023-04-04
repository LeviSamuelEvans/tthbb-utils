# ============================================================================== #
# == Script to merge Histograms together when splitting by region and systematic # 
# ============================================================================== #

"""
Usage:  
    Requires a yaml configuration file with following structure :
       
        input_files:
            - input_file_1.root
            - input_file_2.root
            - input_file_3.root
        baseline_output_files:
            - baseline_output_1.root
            - baseline_output_2.root
            - baseline_output_3.root
        Systematics:
            - syst1
            - syst2
            - syst3

i.e     input_file: 
            - Fit_2l_ttH_STXS1_2l_histos.root 
        baseline_output_files:
            - "Fit_2l_ttH_STXS1_2l_histos_{}.root"
        Systematics:
            - Zjets_XS
            - Wjets_XS
            - ttbb_PH7_PS

"""


import os
import subprocess
import yaml

# Read the YAML file
with open('merge_1l_inclusive.yaml', 'r') as file:
    file_paths = yaml.safe_load(file)

# Get the input file paths, baseline output file paths, and list of systematics from the YAML file
input_files = file_paths['input_files']
baseline_output_files = file_paths['baseline_output_files']
systematics = file_paths['systematics']

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

    # Run the hupdate command in the terminal
    subprocess.run(hupdate_cmd, shell=True, check=True)


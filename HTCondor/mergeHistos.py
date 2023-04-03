import os
import subprocess

# Define the command and filenames
executable2 = "/scratch4/levans/TRExFitter_v4.17/TRExFitter/build/bin/hupdate.exe"
input_file = "Fit_1l_ttH_STXS2_1l_histos.root"
base_output_file = "Fit_1l_ttH_STXS2_1l_histos_{}.root"

# Read the list of systematics from a text file
with open("syst.txt", "r") as f:
    systematics = [line.strip() for line in f.readlines()]

# Initialize the list of output files
output_files = []

# Loop through the list of systematics and generate the output filenames
for systematic in systematics:
    # Format the output filename with the systematic
    output_file = base_output_file.format(systematic)

    # Append the output file to the list of output files
    output_files.append(output_file)

# Join the list of output files as a single string
output_files_str = ' '.join(output_files)

# Build the hupdate command
hupdate_cmd = f"{executable2} {input_file} {output_files_str}"

# Run the hupdate command in the terminal
subprocess.run(hupdate_cmd, shell=True, check=True)

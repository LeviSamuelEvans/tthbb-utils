import os
import subprocess

# Define the command and filenames
executable = "/scratch4/levans/TRExFitter_v4.17/TRExFitter/build/bin/hupdate.exe"
input_file = "Fit_1l_ttH_STXS2_1l_histos.root"
base_output_file = "Fit_1l_ttH_STXS2_1l_histos_Zjets_XS.root"

# Read the list of systematics from a text file
with open("syst.txt", "r") as f:
    systematics = [line.strip() for line in f.readlines()]

# Loop through the list of systematics and run the command with the modified filenames
for systematic in systematics:
    # Replace "Zjets_XS" with the systematic
    output_file = base_output_file.replace("Zjets_XS", systematic)

    # Ensure the replacement was successful, if not, print an error message and skip the iteration
    if output_file == base_output_file:
        print(f"Failed to replace 'Zjets_XS' with '{systematic}' in the output filename.")
        continue

    # Build the command
    cmd = f"{executable} {input_file} {output_file}"

    # Run the command in the terminal
    subprocess.run(cmd, shell=True, check=True)
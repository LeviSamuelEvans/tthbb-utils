#!/usr/bin/env python3

"""
This script downloads a directory of files using rsync. It creates a thread pool to execute the download_directory function
in parallel, which can improve the performance of the script by allowing it to download multiple directories simultaneously.
The max_workers parameter of the ThreadPoolExecutor constructor specifies the maximum number of worker threads to use for
executing the submitted tasks. In this case, the value of max_workers is set to 14, which means that the executor will use
up to 14 threads to execute the download_directory function in parallel.
"""

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

def download_directory(directory, log_file):
    """
    Download a directory of files using rsync.
    """
    os.makedirs(directory, exist_ok=True)
    source = f"leevans@lxplus.cern.ch:/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/ttHbb_legacy_L2ntuples/sys_v2.1/{directory}"
    destination = f"./{directory}"
    rsync_args = ["rsync", "-vrznPe ssh", source, destination]

    result = subprocess.run(" ".join(rsync_args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    # Write individual log files for each directory
    with open(os.path.join(directory, 'rsync.log'), 'w') as f:
        f.write(result.stdout.decode())
        f.write(result.stderr.decode())

    # Write output to the overall log file
    log_file.write(f"Output for {directory}:\n")
    log_file.write(result.stdout.decode())
    log_file.write(result.stderr.decode())

def main():
    """
    Main function to execute the script.
    """
    directories = [
        '1l/5j3b_ttb/', '1l/5j3b_ttbb/', '1l/5j3b_ttc/', '1l/5j3b_ttlight/',
        '1l/5j3b_ttH/', '1l/5j3b_ttB/', '1l/boosted/', '2l/3j3b_ttb/',
        '2l/3j3b_ttbb/', '2l/3j3b_ttB/', '2l/3j3b_ttc/', '2l/3j3b_ttlight/',
        '2l/3j3b_ttH/', '2l/boosted_STXS5/', '2l/boosted_STXS6/'
    ]

    # Open an overall log file for the Python script
    with open('FullProduction.log', 'w') as log_file:
        # Execute the rsync commands in parallel using a thread pool
        with ThreadPoolExecutor(max_workers=14) as executor:
            futures = [executor.submit(download_directory, directory, log_file) for directory in directories]

        # Wait for all the downloads to finish
        for future in futures:
            future.result()

if __name__ == "__main__":
    main()
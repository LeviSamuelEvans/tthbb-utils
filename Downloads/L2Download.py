#!/usr/bin/env python3
"""
A script to assist in downloading the ttH(bb) Legacy Analysis Common L2 Ntuples from the Higgs group disk to linappserv LE v0.1 17.03.23

"""

##############
# USAGE TIPS #
##############

"""
Make sure you are using python v3.6 or onwards for this script, it does not work with python2

Run the script with 'python L2Download.py', then ctrl-z to put the process to sleep, then bg to have it run in the background

If you are running on an ssh connection, you can also disown the process so that it still runs if you get disconnected.
i.e run jobs -> get job number -> then 'disown %[JobId]'
Alternatively, use screen or nohup.

"""



import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

# Define the directories to download
directories = ['1l/5j3b_ttb/','1l/5j3b_ttbb/','1l/5j3b_ttc/','1l/5j3b_ttlight/','1l/5j3b_ttH/','1l/5j3b_ttB/','1l/boosted/', '2l/3j3b_ttb/','2l/3j3b_ttbb/','2l/3j3b_ttB/','2l/3j3b_ttc/','2l/3j3b_ttlight/','2l/3j3b_ttH/','2l/boosted/']

# Define the rsync command with options
'''
Options for rsync
-v: Verbose output, print information about each file as it is transferred
-r: Recursively copy entire directories
-a: Both recursively copy directories and copy file read/write permissions and ownership information
-z: Compress the data during transfer to reduce network traffic [HIGHLY RECOMMENDED]
-P: Show progress information and continue partial transfers if the transfer is interrupted [Needed for log files and useful for interuptions]
-n: perform a dry-run of the download to check all is working as should [RECOMMENDED TO DO BEFORE ACTUAL DOWNLOAD!]
-e ssh: This will tell rsync to use ssh for authenticaion. You can set up a ssh-key such that you won't have to enter a password. Info in the README.md about how to do this :)
-- progress : This will give an estimate of the time remaining for the download

'''

rsync_command = ["rsync", "-vrznPe ssh"] # rsync command followed by actions

# Open an overall log file for the Python script
with open('FullProduction.log', 'w') as log_file:

    # Define the function to download a directory of files
    def download_directory(directory):
        os.makedirs(directory, exist_ok=True)
        source = "leevans@lxplus.cern.ch:/eos/atlas/atlascerngroupdisk/phys-higgs/HSG8/ttHbb_legacy_L2ntuples/sys_v2.1/" + directory
        destination = "./" + directory # the "./" here specifies the cwd, but you can add any file path you want here.
        rsync_args = rsync_command + [source, destination]
        result = subprocess.run(" ".join(rsync_args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # Write log files for each individual directory being downloaded
        with open(os.path.join(directory, 'rsync.log'), 'w') as f:
            f.write(result.stdout.decode())
            f.write(result.stderr.decode())
        # Write the output of each rsync command to the overall log file
        log_file.write(f"Output for {directory}:\n")
        log_file.write(result.stdout.decode())
        log_file.write(result.stderr.decode())

    # Execute the rsync commands in parallel using a thread pool
    with ThreadPoolExecutor(max_workers=14) as executor:
        futures = [executor.submit(download_directory, directory) for directory in directories]

    # Wait for all the downloads to finish
    for future in futures:
        future.result()


################################
# A Note on using thread pool  #
################################

"""
The max_workers parameter of the ThreadPoolExecutor constructor specifies the maximum number of worker threads to use for executing the submitted tasks.
In this case, the value of max_workers is set to 14, which means that the executor will use up to 14 threads to execute the download_directory function in parallel.

The ThreadPoolExecutor creates a pool of worker threads that can execute multiple tasks concurrently, which can improve the performance of the script by allowing it to
download multiple directories simultaneously. The number of worker threads should be chosen based on the number of available CPU cores and the expected workload of the script,
to ensure that the script does not overwhelm the system or create a bottleneck. Run 'lscpu' to get more information on the specs of the machine you are using.

"""
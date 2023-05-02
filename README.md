## ttH(bb) : Legacy Analysis Utilities


This repository contains useful scripts for the ttH(bb) Run 2 Legacy analysis. This includes a python script for submitting batch jobs, in this case designed for the histogram generation
in TRExFitter, which needs to be parallelised when running using the full systematics model. A script to assist in downloading the L2 Productions is also available, plus some scripts to be used for sanity checks of the L2 samples. You can also find other useful scripts in the dedicated Utils folder. This includes scripts that can be used to help analyse fit results from TRExFitter.

#### Scripts

##### TRExFitter Batch Job Submission
TRExSubmit_v1.py is a script that can be used to submit batch jobs for TRExFitter. The script can be used for both histogram generation and running fits. Simply modify the options in the script with the desired configuration settings and execute the script to submit the job to the batch system. This will create two folders; HTCondor and BashScripts, which contain relevant condor .sub files and .sh files for executing the jobs in the condor nodes. You can add as many configs into the script and jobs for all of these will be submitted. Actions for TRExFitter can be found towards the end of the script, along with an option for region-splitting in the case of generating histograms. This script includes the option to split the histogram generation by region and by systematic, or both.


    ###### Merging
 In order to merge the generated histograms together, in the case of splitting by region and systematic, the mergeHistos_v2.py script can be used. This requires a .yaml configuration file, with a list of the associated root histogram region files that TRExFitter outputs, along with all the names of the systematics from the configuration file. This script uses the hupdate executable that comes packaged in the binary folder of TRExFitter. Therefore, to use this script you will need to have TRExFitter compiled.

##### Level 2 Sample Downloading
L2Download.py is a script that uses rsync and multithreading to facilitate in downloading level 2 samples from eos to the RHUL Tier 2 system. The script can be configured to download only a specific set of samples, and can be run in parallel to speed up the download process.

###### Making a ssh key
To prevent needing to input your password for every rsync job, you can generate a ssh key. The instruction for doing this are as follows:

- Generate an SSH key pair on your local machine using the ssh-keygen command. This will create a public key and a private key, which will be used for authentication

     `ssh-keygen`

- Copy your public key to lxplus using the ssh-copy-id command. This will add your public key to the authorized_keys file on the remote server, which will allow you to authenticate using your private key.

    `ssh-copy-id <name_of_key>.pub username@lxplus.cern.ch`


- Test your SSH connection to lxplus using the ssh command. If everything is set up correctly, you should be able to connect without entering a password.

    ` ssh username@lxplus.cern.ch`


- NOTE: This can be quite tempermental in my experience. I have found though that first setting up a kerberbos token seems to make the behaviour of using the ssh key much more stable. You can do this by:

        `kinit username@CERN.CH`

    - use klist to make sure this has worked.

##### Level 2 Event Yields Sanity Check
EventYields.cpp is a script that can be used to perform a sanity check on the event yields in the level 2 production. The script can be used to check raw and weighted yields of a production, for each sample. There is also the option to print out the results of a string of selection cuts in addition. The script assumes you have the .root samples in a directory structure, then recursivley finds all .root files in each directory, and prints out logs with tables of yield for each file, and folder.








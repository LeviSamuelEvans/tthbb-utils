## ttH(bb) Legacy Tools

This repository contains useful scripts for the ttH(bb) Run 2 Legacy analysis.

#### Overview

##### HTCondor
This folder contains the `TRExSubmit.py` script, that can be used to submit batch jobs for TRExFitter. The script can be used for both
histogram generation and running fits. Simply provide the desired command line arguments to the script during execution
to submit job(s) to the batch system. You can add as many configs into the script and jobs for all of these will be
submitted (unless you select the dry-run option `-n` in which case you can submit the jobs manually using the submit
files from the newly created `<WORKDIR>/scripts` folder).

##### Downloads
This folder contains the `Sync.py` script that uses `rsync` and multithreading to facilitate in downloading L2 productions from eos
to the RHUL Tier 2 system (or your local cluster). The script can be configured to download only a specific set of samples, and can be run in
parallel to speed up the download process.

##### Rucio
This folder contains the `rucio-download.py` script that can be used to download L1 productions using Rucio.

##### SanityChecks
This folder contains the `EventYields.cpp` script, that can be used to perform a sanity check on the event yields in the level 2 production. This script is old now, and a much better yield checker can be found at Chris Scheulen's very nice tool here: `https://gitlab.cern.ch/utils_chscheul/naf_utils/yieldcalc`.

##### Utils
This folder contains a collection of scripts used to perform studies related to the profile likelihood fit results of the analysis, and some additional study scripts. These can be found in `fit-study-scripts` and `additional-study-scripts`. Furthermore, the `utils` folder contains some additional utility scripts.

Please refer to the individual script files and their respective directories readme files for more detailed information on their usage and functionality.
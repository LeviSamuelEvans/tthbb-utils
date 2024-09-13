## Additional utility scripts

### Overview

This folder contains scripts for analysing fit results, and some additional miscellaneous scripts used for analysis-related studies.

### Fit Studies

The folder `fit-study-scripts` contains scripts that can be used to facilitate the study of fit results obtained using `TRExFitter`. This includes:

- `background-prediction.py:`: A script for comparing background predictions between different fit setups.
- `corr-diff.py:`: A script for comparing correlation martices between different fit setups and channels.
- `fitted-yields:.py`: A script for comparing pre-fit to post-fit yields in the relevant regions of phase-space
- `pie-chart.py:`: A script for creating pie charts.
- `plot-scan.py:` A script for plotting the 1D likelihood scan results.
- `poi-stxs-plot.py:` A Script for plotting the POI's for the STXS measurement.
- `post-fit-acceptance.py:` A script for analysing the post-fit acceptance effects of nuisance parameter pulls. Note, this script works by using the `PullTables` feature of TRExFitter, which is now depreciated.
- `pull-sig-dist.py:` A script for producing pull significance distributions.
- `syst-shape.py:` A script for plotting systematic shapes with respect to normalised signal contributions.
- `ttbar-fractions.py:` A script for analysing the $t\bar{t}$ flavour fractions in the analysis phase-space.
- `update-norm.py:` A super work-flow specific script for updating systematic normalisations. A tool exists to calculate these correction factors, which can be found at: https://gitlab.cern.ch/leevans/renormalisation-tool

### Some additional scripts

The folder `additional-study-scripts` contains miscellaneous analysis study scripts. This includes:

- `fsr_weights.py:` A script to save the final-state radiation weights to a `.csv` file and subsequently plot the distribution of these weights.
- `transformer-correlations:` A script to derive the linear correlations between discriminating observables and the legacy transfomer discriminants, used as the fitting observables. This script was adapted from an original script kindly by Luisa Carvalho (thanks!).

For further details on each script, please refer to the descriptions included in the relevant python script.

### Additional utilities

The folder `utils` contains any extra scripts that have been used for the analysis.

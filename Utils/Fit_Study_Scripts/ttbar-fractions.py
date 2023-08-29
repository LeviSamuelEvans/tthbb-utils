"""
================================================================
== Flavour composition fractions in ttbar 5FS/4FS PP8 samples ==
================================================================

- Tips for running locally:

    1. First, mount the location of the L2 Ntuples to your MountPoint via macFuse
    sshfs -r levans@linappserv0.pp.rhul.ac.uk:/juicefs/data/levans/L2_ttHbb_Production_212238_v3/ ~/Desktop/PhD/MountPoint/
    3. For Dismounting:
    sudo diskutil umount force /Users/levievans/Desktop/PhD/MountPoint/
    Do not forget to dismount!

- How to run on Lxplus/Tier3 sites:

    1. setup the relevant LCG enviroment with all the packages we will need via
    source /cvmfs/sft.cern.ch/lcg/views/dev3/latest/x86_64-centos7-gcc11-opt/setup.sh
    2. set up the relevant path to L2 files on EOS via `PATH` variable

- v1.0 Features:
    - Plots of inclusive phase-space split by channel
    - option to run over AFII or Nominal samples
    - basic error handling
    - plotting styles configurable in script

- v1.1 Features:
    - Added option to run over boosted or resolved regions
    - Added option to run over all regions (STXS, boosted and resolved)

- v1.2 Features:
    - Added per region plot splits (via dictionaries)
    - Added Summary plot feature for all regions in a channel

"""

import logging
import os

# Packages
import awkward as ak
import matplotlib.pyplot as plt
import mplhep
import numpy as np
import uproot

# Some basic error handling for the event counting nested loops
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Plotting style
plt.style.use("ggplot")

# Absolute path [using sshfs mounted drive]
PATH = "/Users/levievans/Desktop/PhD/MountPoint/"

# Choose the channel [Lepton+jets,Dilepton]
""" Options availabe:
- Lepton+jets
- Dilepton
- tt+≥1c 1l
- tt+≥2b 1l
- tt+1b 1l
- tt+B 1l
- tt+light 1l
- tt+≥1c 2l
- tt+≥2b 2l
- tt+1b 2l
- tt+B 2l
- tt+light 2l
"""
# Choose the channel [Lepton+jets,Dilepton]
CHANNEL = "Dilepton"

# Choose the MC generator [PowhegBox+Pythia8,PP8_AFII]
MCGEN = "PowhegBox+Pythia8"

# Choose Y-axis style [Norm,Total]
Y_AXIS_STYLE = "Norm"

# Display Full Yield Table [No,Yes]
YIELD_TABLE = "No"

# Choose the region you would like to run over [resolved,boosted or all]
REGION = "all"

# Choose the plot type [Summary,Individual]
PLOT_TYPE = "Summary"

# Define the labels used in Summary Plot
region_label_mapping = {
    f"{PATH}1l/5j3b_ttbb": "tt+≥2b",
    f"{PATH}1l/5j3b_ttb": "tt+1b",
    f"{PATH}1l/5j3b_ttB": "tt+B",
    f"{PATH}1l/5j3b_ttc": "tt+≥1c",
    f"{PATH}1l/5j3b_ttlight": "tt+light",
    f"{PATH}1l/5j3b_ttH": "ttH",
    f"{PATH}1l/boosted": "Boosted",
    f"{PATH}2l/3j3b_ttbb": "tt+≥2b",
    f"{PATH}2l/3j3b_ttb": "tt+1b",
    f"{PATH}2l/3j3b_ttB": "tt+B",
    f"{PATH}2l/3j3b_ttc": "tt+≥1c",
    f"{PATH}2l/3j3b_ttlight": "tt+light",
    f"{PATH}2l/3j3b_ttH": "ttH",
    f"{PATH}2l/boosted_STXS5": "Boosted 5",
    f"{PATH}2l/boosted_STXS6": "Boosted 6",
}


# Define the paths to the regions for each channel for mapping to user inputs
channel_to_paths = {
    "Lepton+jets": {
        "all": [ # All regions in channel
            f"{PATH}1l/5j3b_ttbb",
            f"{PATH}1l/5j3b_ttb",
            f"{PATH}1l/5j3b_ttB",
            f"{PATH}1l/5j3b_ttH",
            f"{PATH}1l/5j3b_ttc",
            f"{PATH}1l/5j3b_ttlight",
            f"{PATH}1l/boosted"
        ], # Specific regions in 1l channel
        "tt+≥1c 1l": [f"{PATH}1l/5j3b_ttc"],
        "tt+≥2b 1l": [f"{PATH}1l/5j3b_ttbb"],
        "tt+1b 1l": [f"{PATH}1l/5j3b_ttb"],
        "tt+B 1l": [f"{PATH}1l/5j3b_ttB"],
        "tt+light 1l": [f"{PATH}1l/5j3b_ttlight"],
    },
    "Dilepton": {
        "all": [ # All regions in channel
            f"{PATH}2l/3j3b_ttbb",
            f"{PATH}2l/3j3b_ttb",
            f"{PATH}2l/3j3b_ttB",
            f"{PATH}2l/3j3b_ttH",
            f"{PATH}2l/3j3b_ttc",
            f"{PATH}2l/3j3b_ttlight",
            f"{PATH}2l/boosted_STXS5",
            f"{PATH}2l/boosted_STXS6",
        ], # Specific regions in 1l channel
        "tt+≥1c 2l": [f"{PATH}2l/3j3b_ttc"],
        "tt+≥2b 2l": [f"{PATH}2l/3j3b_ttbb"],
        "tt+1b 2l": [f"{PATH}2l/3j3b_ttb"],
        "tt+B 2l": [f"{PATH}2l/3j3b_ttB"],
        "tt+light 2l": [f"{PATH}2l/3j3b_ttlight"],
    },
}

# Define label mappings for REG_SELEC for channel runs
channel_to_reg_selec = {
    "Lepton+jets": '≥5j,≥3b@70',
    "Dilepton": '≥3j,≥2b@70,≥3b@85',
}

# Error handling for unknown channels or regions
if CHANNEL not in channel_to_paths:
    raise ValueError(f"{CHANNEL} channel unknown")

if REGION not in channel_to_paths[CHANNEL]:
    raise ValueError(f"{REGION} region unknown for {CHANNEL} channel")


# For plots
INPUT_DIRECTORY = channel_to_paths.get(CHANNEL, {}).get(REGION, [])
REG_SELEC = channel_to_reg_selec.get(CHANNEL, '')


if MCGEN == "PowhegBox+Pythia8":
    INPUT_FILES_TT = ["tt_PP8_mc16a.root",
                      "tt_PP8_mc16d.root",
                      "tt_PP8_mc16e.root"
                      ]

    INPUT_FILES_TTBB = ["ttbb_PP8_mc16a.root",
                        "ttbb_PP8_mc16d.root",
                        "ttbb_PP8_mc16e.root"
                        ]
elif MCGEN == "PP8_AFII":
     INPUT_FILES_TT = ["tt_PP8_mc16a_AFII.root",
                      "tt_PP8_mc16d_AFII.root",
                      "tt_PP8_mc16e_AFII.root"
                      ]

     INPUT_FILES_TTBB = ["ttbb_PP8_mc16a_AFII.root",
                        "ttbb_PP8_mc16d_AFII.root",
                        "ttbb_PP8_mc16e_AFII.root"
                        ]
else:
    raise ValueError(f"{MCGEN} MC gen unknown")


# Define the heavy flavour selections (only addtional jets, jets coming from W of top decay not included)

HF_SELECTIONS = {
                "tt+light": lambda evts: evts["HF_SimpleClassification"] == 0,
                "tt+≥1c": lambda evts: evts["HF_SimpleClassification"] == -1,
                "tt+1b": lambda evts: (evts["HF_SimpleClassification"] == 1) & (evts["HF_Classification"] >= 1000) & (evts["HF_Classification"] < 1100),
                "tt+B": lambda evts: (evts["HF_SimpleClassification"] == 1) & (evts["HF_Classification"] >= 100) & (evts["HF_Classification"] < 200),
                "tt+≥2b": lambda evts: (evts["HF_SimpleClassification"] == 1) & (((evts["HF_Classification"] >= 200) & (evts["HF_Classification"] < 1000)) | (evts["HF_Classification"] >= 1100))
                }

# Extract the branches we will need

BRANCHES_TO_READ = [
    "HF_SimpleClassification",
    "HF_Classification",
    "weight_mc",
    "weight_normalise",
    "weight_pileup",
    "weight_leptonSF",
    "weight_jvt",
    "weight_bTagSF_DL1r_Continuous",
    "randomRunNumber",
    "L2_Class_class"
]

# Add branches for boosted overlap removal
if CHANNEL == "Lepton+jets":
    BRANCHES_TO_READ += ["passedOfflineBoostedSelection"]
elif CHANNEL == "Dilepton":
    BRANCHES_TO_READ += ["passedOfflineBoostedSelection_leading_rcjet_valid_sub_bjet_m"]
elif CHANNEL == "test":
    pass
else:
    raise ValueError(f"{CHANNEL} unknown")

# Function to compute total event weights
def _compute_weights(evts): # evts is a dict of arrays
    lumi_weights = ( # Luminosity weights
        (evts["randomRunNumber"] <= 311481) * 36646.74 +
        ((evts["randomRunNumber"] > 311481) & (evts["randomRunNumber"] <= 340453)) * 44630.6 +
        (evts["randomRunNumber"] > 340453) * 58791.6
    )  # in pb^-1
    return evts["weight_mc"] * evts["weight_normalise"] * evts["weight_pileup"] * evts["weight_leptonSF"] * \
           evts["weight_jvt"] * evts["weight_bTagSF_DL1r_Continuous"] * lumi_weights

# Initialize a dictionary to hold the total weighted events for each category
counts = {}
# Initialize a nested dictionary to hold the summary data for summary plot
summary_data = {}

# Loop over each heavy flavour selection and save weighted event counts

for flavor, HF_SELECTION in HF_SELECTIONS.items():
    total_events = 0

    # Choose the appropriate file list based on the heavy flavour
    files = INPUT_FILES_TT if flavor in ["tt+light", "tt+≥1c"] else INPUT_FILES_TTBB

    for directory in INPUT_DIRECTORY:
        #print(directory) #DEBUG
        for file in files:
            filepath = f"{directory}/{file}"
            # For printing yields
            base_name = os.path.basename(filepath)
            parent_dir = os.path.basename(os.path.dirname(filepath))
            file_info = f"{parent_dir}/{base_name}"
            try:
                with uproot.open(filepath) as f:
                    # Get the nominal_Loose tree
                    if "nominal_Loose" in f:
                        tree = f["nominal_Loose"]
                        evts = tree.arrays(BRANCHES_TO_READ)

                        # Compute weights
                        weights = _compute_weights(evts)

                        #  Print weighted event yield
                        weighted_yield = ak.sum(weights)
                        #print(f"Weighted event count for {file_info}: {weighted_yield}") #DEBUG

                        # Apply the HF_SELECTION mask
                        mask_hf_selection = HF_SELECTION(evts)

                        # Apply boosted mask based on regions and channel
                        mask_boosted = None
                        mask_L2_Class = evts["L2_Class_class"] == 0
                        if REGION == "all":
                            if CHANNEL == "Lepton+jets":
                                is_boosted = "boosted" in directory
                                if not is_boosted:
                                    mask_boosted = evts["passedOfflineBoostedSelection"] == 0
                            elif CHANNEL == "Dilepton":
                                is_boosted = "boosted_STXS5" in directory or "boosted_STXS6" in directory
                                if is_boosted:
                                    mask_boosted = mask_L2_Class  # Apply the L2_Class_class mask for boosted regions
                                else:
                                    # Apply the passedOfflineBoostedSelection mask for non-boosted regions
                                    mask_boosted = evts["passedOfflineBoostedSelection_leading_rcjet_valid_sub_bjet_m"] == 0

                        # If both masks are applicable, then lets combine them
                        if mask_boosted is not None:
                            combined_mask = mask_hf_selection & mask_boosted
                        else:
                            combined_mask = mask_hf_selection
                        # Update the summary_data dictionary
                        if directory not in summary_data:
                            summary_data[directory] = {}
                        if file not in summary_data[directory]:
                            summary_data[directory][flavor] = 0  # Initialize if not present
                        # Add the event counts (or other metrics) to the summary data
                        summary_data[directory][flavor] += ak.sum(weights[combined_mask])
                        print(f"{directory}/{flavor}",summary_data[directory][flavor]) # DEBUG
                        # Accumulate the weights via summing over the arrays
                        total_events += ak.sum(weights[combined_mask])
                        #print(f"Final values{file_info}: {total_events}")

                    else:
                        print(f"Warning: 'nominal_Loose' tree not found in {filepath}. Skipping...")
            except FileNotFoundError:
                logging.error(msg=f"File not found: {filepath}. Skipping to the next file...")
            except KeyError as ke:
                logging.error(msg=f"Missing key in file {filepath}. Error: {ke}. Skipping...")
            except Exception as e:
                logging.error(msg=f"An unexpected error occurred while processing {filepath}. Error: {e}. Stopping processing.")

    counts[flavor] = total_events # Store total weighted events for each catgeory


# printing final counts for each flavor
for flavor, count in counts.items():
    print(f"Final count for {flavor}: {count}")

print(summary_data) # DEBUG

# Initialize a dictionary to store the bottom of the bars for each region (summary plot)
bar_bottoms = {}

# Initialize an empty list to keep track of the flavors that have already been labeled (summary plot)
labeled_flavors = []

# For plotting: define the flavors and colors needed
flavors = ['tt+light', 'tt+≥1c', 'tt+1b', 'tt+B', 'tt+≥2b']
colors = ['green', 'purple', 'blue', 'darkblue', 'lightblue']


def _plot_aesthetics(CHANNEL, MCGEN, REGION, REG_SELEC, ax) -> None:
    ax.set_ylabel('Normalised Entries')
    ax.set_xlabel('Flavour Fractions')
    if PLOT_TYPE != "Summary":
        ax.set_title(f"{CHANNEL}: {REGION} {MCGEN}", x=0.65, fontsize=10)
        ax.text(0.63, 0.92, r'$\sqrt{s}$ = 13 TeV, $\mathcal{L}=$140fb$^{-1}$', transform=ax.transAxes)
        ax.text(0.63, 0.86, f"{REG_SELEC}", transform=ax.transAxes)
    if PLOT_TYPE == "Summary":
        ax.set_title(f"{CHANNEL}:{MCGEN}", x=0.65, fontsize=10)
        major_ticks = np.arange(0, 1.10, step=0.1)  # Assuming you want major ticks from 0 to 5, spaced by 1
        minor_ticks = np.arange(0,1, 0.05)
        ax.set_yticks(major_ticks)
        ax.set_yticks(minor_ticks, minor=True)
        ax.set_xlabel('Flavour Fractions per Region')
        # Rotate x-axis labels
        plt.xticks(rotation=45, ha='right')
    mplhep.atlas.text(text="Simulation Internal", loc=0, ax=ax)


# Create the figure and axes
fig, ax = plt.subplots()
# Create dummy bars for the legend (summary plot)
dummy_bars = [ax.bar(0, 0, color=color, label=flavor) for color, flavor in zip(colors, flavors)]
bar_handles = []

# == SUMMARY PLOT == #

# Loop through each region to plot the data
for region, flavor_data in summary_data.items():
    # Use the mapped label if available; otherwise use the original
    label = region_label_mapping.get(region, region)
    # Initialize the bottom of the bar for this region to 0
    bar_bottom = 0

    total_count = sum(flavor_data.values())  # Compute the total_count only once for each region

    for flavor, count in flavor_data.items():
        # Compute the normalized count, if needed
        normalized_count = count / total_count if total_count != 0 else 0

        # Choose the appropriate y-values based on the Y-axis style
        y_value = normalized_count if Y_AXIS_STYLE == "Norm" else count

        # Choose the appropriate color for this flavor
        color = colors[flavors.index(flavor)]

        # Create the bar and save the handle if this is the first bar of this flavor
        bar = ax.bar(label, y_value, bottom=bar_bottom, color=color,edgecolor='black',linewidth=0.5)
        if flavor not in bar_handles:
            bar_handles.append(bar)

        # Update the bottom of the bar for this region
        bar_bottom += y_value

    # Update the dictionary to store the bottom of the bar for each region
    bar_bottoms[label] = bar_bottom  # Use 'label' instead of 'region'

# Create the legend using the handles
labels = [f"{flavor}" for flavor in flavors]  # Modify this if you want to add more info
ax.legend([handle[0] for handle in bar_handles], labels, title='Flavour Components', loc='upper left', bbox_to_anchor=(1, 1))

_plot_aesthetics(CHANNEL, MCGEN, REGION, REG_SELEC, ax)

plt.savefig(f'fractions_{CHANNEL}_{MCGEN}_Summary.pdf', bbox_inches='tight')
plt.savefig(f'fractions_{CHANNEL}_{MCGEN}_Summary.png', bbox_inches='tight')
# Show the plot
#plt.show()


# == INDIVIDUAL PLOTS == #

total_counts = sum(counts.values())
percentage_counts = {flavor: (count/total_counts)*100 for flavor, count in counts.items()}
normalised_counts = {flavor: (count/total_counts) for flavor, count in counts.items()}


if Y_AXIS_STYLE == "Norm":
    bars = ax.bar(flavors, [normalised_counts[f] for f in flavors], color=colors)
elif Y_AXIS_STYLE == "Total":
    bars = ax.bar(flavors, [counts[f] for f in flavors], color=colors)

# Add flavour fractions to the bars
for bar, percentage in zip(bars, percentage_counts.values()):
    height = bar.get_height()
    ax.annotate('{:.2f}%'.format(percentage),
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha='center', va='bottom')

#Add a table at the bottom of the axes
if YIELD_TABLE == "Yes":
    table_data = list(zip(flavors, [counts[f] for f in flavors], list(percentage_counts.values())))
    columns = ("Flavor", "Counts", "Percentage")
    table = ax.table(cellText=table_data, colLabels=columns, loc='bottom', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.auto_set_column_width(col=list(range(len(columns))))  # Optionally set the widths of the columns
    ax_position = ax.get_position() # Adjust the table position
    ax.set_position([ax_position.x0, ax_position.y0 + ax_position.height * 0.2,
                     ax_position.width, ax_position.height * 0.8])
elif YIELD_TABLE == "No":
    pass
else:
    raise ValueError(f"{YIELD_TABLE} option unknown, put Yes or No")


# Add a legend for the bars including the total yield
labels = [f"{flavor} ({counts[flavor]:,.2f})" for flavor in flavors]
ax.legend(bars, labels, title='Component Yields', loc='upper left', bbox_to_anchor=(1, 1))


_plot_aesthetics(CHANNEL, MCGEN, REGION, REG_SELEC, ax)

#plt.savefig(f'fractions_{CHANNEL}_{MCGEN}.pdf', bbox_inches='tight')
#plt.savefig(f'fractions_{CHANNEL}_{MCGEN}.png', bbox_inches='tight')
#plt.savefig(f'fractions_{CHANNEL}_{MCGEN}_{REGION}.png', bbox_inches='tight')
#plt.show()
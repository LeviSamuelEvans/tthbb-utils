#!/usr/bin/env python3

import yaml
import matplotlib.pyplot as plt
import mplhep
import os


"""
==============================
== Fitted Yield Comparisons ==
==============================

Description:
    - Script to plot the post-fit to pre-fit yield ratio for all
      specified samples in all specified regions.

Usage:
    - ./fitted-yields.py

Notes:
    - Requires TRExFitter output YAML files
    - Configure the script using the variables below
"""

plt.style.use(mplhep.style.ROOT)

def load_yaml_data(base_path, region, fit_type):
    """ Load data from YAML file """
    with open(f"{base_path}/Plots/{region}_{channel}_{fit_type}.yaml", 'r') as f:
        data = yaml.safe_load(f)
    return data

def collect_data(base_path, regions):
    """ Collect pre-fit and post-fit data for all regions """
    data_dict = {}
    for region in regions:
        data_dict[region] = {
            'prefit': load_yaml_data(base_path, region, 'prefit'),
            'postfit': load_yaml_data(base_path, region, 'postfit')
        }
    return data_dict

def get_yield_for_sample(data, sample_name):
    """ Get yield for a given sample name """
    for sample in data["Samples"]:
        if sample["Name"] == sample_name:
            return sample["Yield"]
    return []

def calculate_ratio(data_dict, sample_name, region):
    """ Calculate post-fit to pre-fit yield ratio for a sample in a region """
    prefit_yield = get_yield_for_sample(data_dict[region]['prefit'], sample_name)
    postfit_yield = get_yield_for_sample(data_dict[region]['postfit'], sample_name)

    if not prefit_yield or not postfit_yield:
        print(f"Yield data not found for sample {sample_name} in region {region}")
        return []

    # Avoid division by zero
    return [p / pre if pre != 0 else 0 for p, pre in zip(postfit_yield, prefit_yield)]

def calculate_relative_difference(data_dict, sample_name, region):
    """ Calculate (Post - Pre) / Post for a sample in a region """
    prefit_yield = get_yield_for_sample(data_dict[region]['prefit'], sample_name)
    postfit_yield = get_yield_for_sample(data_dict[region]['postfit'], sample_name)

    if not prefit_yield or not postfit_yield:
        print(f"Yield data not found for sample {sample_name} in region {region}")
        return []

    # Avoid division by zero
    return [(post - pre) / post if post != 0 else 0 for post, pre in zip(postfit_yield, prefit_yield)]

def plot_ratio(base_path, data_dict, sample_name, region):
    """ Plot post-fit to pre-fit yield ratio for a sample in a region and save it """
    ratio = calculate_ratio(data_dict, sample_name, region)
    bin_edges = data_dict[region]['prefit']['Figure'][0]['BinEdges']

    # Modify the ratio list to extend its length by 1
    ratio.append(ratio[-1])  # Appending the last ratio value


    sample_color = color_dict.get(sample_name, "black")  # Default to black if sample not found in dictionary
    plt.step(bin_edges, ratio, where='post', linestyle='--', color=sample_color)
    plt.xlabel(data_dict[region]['prefit']['Figure'][0]['XaxisLabel'])
    plt.ylabel(f"Post-fit / Pre-fit")
    plt.title(f"{sample_name} in {region}", fontsize=20, loc='right')
    mplhep.atlas.text(text="Internal", loc=0, fontsize=20, ax=None)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Create directory if it does not exist
    directory = f"/Users/levievans/Desktop/PhD/3rd-YEAR/Fits/Fit_Results_09_10_23/Fit_Studies/PostOverPreYields/{channel}/{region}"
    if not os.path.exists(directory):
        os.makedirs(directory)

    plt.savefig(f"{directory}/{region}_{sample_name}_{channel}.pdf")
    plt.close()

def plot_all_samples(base_path, data_dict, region, sample_list, color_dict):
    """ Plot all samples for a region on the same plot """

    # Prepare the plot
    plt.figure(figsize=(14,8))

    for sample_name in sample_list:
        ratio = calculate_ratio(data_dict, sample_name, region)
        bin_edges = data_dict[region]['prefit']['Figure'][0]['BinEdges']

        # Using the previous approach to extend ratio and bin_edges
        ratio.append(ratio[-1])
        bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges) - 1)]
        bin_centers.append(bin_edges[-1])

        # Plot the step line for the current sample
        plt.step(bin_centers, ratio, where='post', linestyle='--', color=color_dict[sample_name], label=sample_name)

    # Setting up plot aesthetics
    plt.xlabel(data_dict[region]['prefit']['Figure'][0]['XaxisLabel'])
    plt.ylabel(f"Post-fit / Pre-fit")
    plt.title(f"All Samples in {region}", fontsize=20, loc='right')
    mplhep.atlas.text(text="Internal", loc=0, fontsize=20, ax=None)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=10, frameon=True, framealpha=0.2)

    # Save the combined plot
    directory = f"/Users/levievans/Desktop/PhD/3rd-YEAR/Fits/Fit_Results_09_10_23/Fit_Studies/PostOverPreYields/{channel}/{region}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    plt.savefig(f"{directory}/{region}_AllSamples_{channel}.pdf")
    plt.close()

def plot_one_sample_across_regions(base_path, data_dict, sample_name, region_list, reg_color_dict):
    """ Plot a single sample across all regions on the same plot """

    # Prepare the plot
    plt.figure(figsize=(18,8))

    for region in region_list:
        ratio = calculate_ratio(data_dict, sample_name, region)
        bin_edges = data_dict[region]['prefit']['Figure'][0]['BinEdges']

        # Using the previous approach to extend ratio and bin_edges
        ratio.append(ratio[-1])
        bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges) - 1)]
        bin_centers.append(bin_edges[-1])

        # Plot the step line for the current region
        plt.step(bin_centers, ratio, where='post', linestyle='--', color=reg_color_dict[region], label=region)

    # Setting up plot aesthetics
    plt.xlabel("Relative NN Discriminant")  # You may need to adjust this depending on your data
    plt.ylabel(f"Post-fit / Pre-fit")
    plt.title(f"{sample_name} across All Regions", fontsize=20, loc='right')
    mplhep.atlas.text(text="Internal", loc=0, fontsize=20, ax=None)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=10, frameon=True, framealpha=0.2, title="Regions")

    # Save the plot
    directory = f"/Users/levievans/Desktop/PhD/3rd-YEAR/Fits/Fit_Results_09_10_23/Fit_Studies/PostOverPreYields/{channel}/Summary"
    if not os.path.exists(directory):
        os.makedirs(directory)
    plt.savefig(f"{directory}/{sample_name}_AcrossAllRegions_{channel}.pdf")
    plt.close()


if __name__ == '__main__':
    base_path = "/Users/levievans/Desktop/PhD/3rd-YEAR/Fits/Fit_Results_09_10_23/Fits/2l_STXS_BONLY/Fit_2l"
    regions = ['tt1b',
               'ttB',
               'tt2b',
               'ttc',
               'tt_light',
               #'ttH_boost_CR',
               'Full_ttH_STXS1',
               'Full_ttH_STXS2',
               'Full_ttH_STXS3',
               'Full_ttH_STXS4',
               'Full_ttH_STXS5',
               'Full_ttH_STXS6',
               ]

    samples = ['tt + 1b', 'tt + B', 'tt + #geq2b', 'tt + #geq1c', 'tt + light']

    sample_list = ['tt + 1b', 'tt + B', 'tt + #geq2b', 'tt + #geq1c', 'tt + light']

    channel = '2l'

    color_dict = {
    "tt + 1b": "#4169E1", # Royal Blue
    "tt + B": "#0047AB", # Navy Blue
    "tt + #geq2b": "#87CEEB", #Sky blue
    "tt + #geq1c": "purple",
    "tt + light": "green",
    }

    reg_color_dict = {
    "tt1b": "#4169E1", # Royal Blue
    "ttB": "#0047AB", # Navy Blue
    "tt2b": "#87CEEB", #Sky blue
    "ttc": "purple",
    "tt_light": "green",
    "Full_ttH_STXS1": "#FFCCCC",
    "Full_ttH_STXS2": "#FF9999",
    "Full_ttH_STXS3": "#FF6666",
    "Full_ttH_STXS4": "#FF3333",
    "Full_ttH_STXS5": "#FF0000",
    "Full_ttH_STXS6": "#CC0000",
    #"ttH_boost_CR": "black",
    }

    data_dict = collect_data(base_path, regions)

    # Sample by sample
    for region in regions:
        for sample in samples:
            plot_ratio(base_path, data_dict, sample, region)

    # all samples per region
    for region in regions:
        plot_all_samples(base_path, data_dict, region, sample_list, color_dict)

    # all regions per sample
    regions = list(data_dict.keys())  # Get all the regions
    for sample in samples:
        plot_one_sample_across_regions(base_path, data_dict, sample, regions, reg_color_dict)
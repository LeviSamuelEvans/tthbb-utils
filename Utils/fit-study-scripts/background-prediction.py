#!/usr/bin/env python3

import yaml
import matplotlib.pyplot as plt
import mplhep
import glob
import os
import logging

"""
======================================
== Background Prediction Comparison ==
======================================

Description:
    - Script to compare the background prediction between two fits for a given region(s).

Usage:
    - ./background-prediction.py

Notes:
    -  All paths and configurations are simply set at the bottom of the script to avoid
        going YAML mad.
    -  The script will save the plots to the specified path, inside the IndividualPlots
        and CombinedPlots directories it creates. The total ttbar ratio plot will be
        saved in the base path specified.

"""

# use ROOT plotting style
plt.style.use(mplhep.style.ROOT)

# configure the logging
logging.basicConfig(level=logging.INFO, format="{levelname:<8s} {message}", style="{")
logger = logging.getLogger(__name__)

# Maps for sample and region names to display
sample_map = {
    "#it{t#bar{t} + 1b}": r"$\it{t\bar{t}+1b}$",
    "#it{t#bar{t} + B}": r"$\it{t\bar{t}+B}$",
    "#it{t#bar{t} + #geq 2b}": r"$\it{t\bar{t}+\geq 2b}$",
    "#it{t#bar{t} + #geq 1c}": r"$\it{t\bar{t}+\geq 1c}$",
    "#it{t#bar{t}} + light": r"$\it{t\bar{t}+ \text{light}}$",
}

region_map = {
    "ttH_STXS1_1l": r"$\it{t\bar{t}H\;p_{T}^{H}} [0-60)$",
    "ttH_STXS2_1l": r"$\it{t\bar{t}H\;p_{T}^{H}} [60-120)$",
    "ttH_STXS3_1l": r"$\it{t\bar{t}H\;p_{T}^{H}} [120-200)$",
    "ttH_STXS4_1l": r"$\it{t\bar{t}H\;p_{T}^{H}} [200-300)$",
    "ttH_STXS5_1l": r"$\it{t\bar{t}H\;p_{T}^{H}} [300-450)$",
    "ttH_STXS6_1l": r"$\it{t\bar{t}H\;p_{T}^{H}} [450-inf)$",
}


def load_yaml_data(file_path):
    """Load data from a YAML file."""
    try:
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error loading YAML file: {file_path}")
        logger.error(str(e))
        return None


def calculate_total_yield(data):
    """Calculate the total yield for a region by summing up the yields of all samples."""
    total_yield = 0
    for sample in data.get("Samples", []):
        if isinstance(sample.get("Yield"), list):
            total_yield += sum(sample["Yield"])
        else:
            total_yield += sample.get("Yield", 0)
    return total_yield


def get_yield_for_sample(data, sample_name):
    """Extract yield for a given sample name from loaded data"""
    for sample in data.get("Samples", []):
        if sample.get("Name") == sample_name:
            return sample.get("Yield")
    logger.warning(f"Sample {sample_name} not found in data! Check the sample names.")
    return None


def collect_data(base_path_1, base_path_2, regions):
    """Collect post-fit data for both fits across all regions"""
    data_dict = {}
    for region in regions:
        file_path_1 = os.path.join(base_path_1, f"{region}_postfit.yaml")
        file_path_2 = os.path.join(base_path_2, f"{region}_postfit.yaml")

        if os.path.isfile(file_path_1) and os.path.isfile(file_path_2):
            postfit1 = load_yaml_data(file_path_1)
            postfit2 = load_yaml_data(file_path_2)
            data_dict[region] = {
                "fit1": postfit1,
                "fit2": postfit2,
            }
        else:
            logging.warning(
                f"Files for region '{region}' not found in one or both specified paths."
            )
    return data_dict


def calculate_ratio(data1, data2, sample_name):
    """Calculate post-fit yield ratio between two fits for a sample"""
    yield1 = get_yield_for_sample(data1, sample_name)
    yield2 = get_yield_for_sample(data2, sample_name)

    if not yield1 or not yield2:
        logging.warning(f"Yield data not found for sample {sample_name}")
        return []
    logging.info(f"Yields from Fit 1 for {sample_name}: {yield1}")
    logging.info(f"Yields from Fit 2 for {sample_name}: {yield2}")

    # avoid division by zero
    return [y2 / y1 if y1 != 0 else 0 for y1, y2 in zip(yield1, yield2)]


def calculate_normalised_ratio(data1, data2, sample_name, total_yield_region):
    """Calculate yield ratios normalised to the total yield in the region."""
    yield1 = get_yield_for_sample(data1, sample_name)
    yield2 = get_yield_for_sample(data2, sample_name)

    if not yield1 or not yield2 or not total_yield_region:
        logging.warning(
            f"Data not found for sample {sample_name} or total yield is missing"
        )
        return []

    normalised_yield1 = [y / total_yield_region for y in yield1]
    normalised_yield2 = [y / total_yield_region for y in yield2]

    # calc the ratio of normalised yields
    normalised_ratio = [
        y2 / y1 if y1 != 0 else 0
        for y1, y2 in zip(normalised_yield1, normalised_yield2)
    ]

    return normalised_ratio


def calculate_total_ratio(data1, data2, samples):
    """Calculate the total yield ratio for a set of samples between two setups."""
    total_yield1 = 0
    total_yield2 = 0
    for sample_name in samples:
        yield1 = sum(get_yield_for_sample(data1, sample_name))
        yield2 = sum(get_yield_for_sample(data2, sample_name))
        total_yield1 += yield1
        total_yield2 += yield2

    return total_yield1 / total_yield2 if total_yield1 != 0 else 0


def plot_comparison(base_path, data_dict, sample_name, region):
    """Plot comparison of post-fit yield ratios for a sample between two fits"""
    logging.info(f"Plotting comparison for {sample_name} in region {region}")
    fit1_data = data_dict[region]["fit1"]
    fit2_data = data_dict[region]["fit2"]
    ratio = calculate_normalised_ratio(
        fit1_data, fit2_data, sample_name, calculate_total_yield(fit1_data)
    )
    bin_edges = fit1_data["Figure"][0]["BinEdges"]

    ratio.append(ratio[-1])
    logging.info(f"Calculated Ratios: {ratio}")

    display_name = sample_map.get(sample_name, sample_name)

    plt.figure(figsize=(12, 8))
    plt.step(
        bin_edges, ratio, where="post", linestyle="--", color="blue", label="Fit1/Fit2"
    )
    plt.xlabel(r"$t\bar{t}{H}$ Discriminant")
    plt.ylabel("Fit1 / Fit2 ratio")
    plt.grid(True)
    plt.legend(
        title=f"{display_name}",
        bbox_to_anchor=(1, 0.95),
        loc="upper right",
        fontsize=18,
    )
    plt.title(f"Region {region_map.get(region, region)}", fontsize=18, loc="right")
    # Save the plot
    directory = os.path.join(save_path, "IndividualPlots", region)
    if not os.path.exists(directory):
        os.makedirs(directory)
    plt.savefig(os.path.join(directory, f"{sample_name}_comparison.pdf"))
    plt.close()


def plot_combined_comparison(base_path, data_dict, samples, region):
    """Plot comparison of post-fit yield ratios for all samples in a region between two fits"""
    plt.figure(figsize=(10, 8))

    for sample_name in samples:
        fit1_data = data_dict[region]["fit1"]
        fit2_data = data_dict[region]["fit2"]
        ratio = calculate_normalised_ratio(
            fit1_data, fit2_data, sample_name, calculate_total_yield(fit1_data)
        )
        if not ratio:
            continue
        bin_edges = fit1_data["Figure"][0]["BinEdges"]
        ratio.append(ratio[-1])
        display_name = sample_map.get(sample_name, sample_name)

        plt.step(bin_edges, ratio, where="post", label=display_name)

    mplhep.atlas.text(text="Internal", loc=0, fontsize=20, ax=None)
    plt.xlabel(r"$t\bar{t}{H}$ Discriminant")
    plt.ylabel(
        r"$\frac{N_{t\bar{t}+x}^{\text{Baseline}}}{N_{t\bar{t}+x}^{Split-fit}}$ ratio"
    )
    plt.title(f"Region {region_map.get(region, region)}", fontsize=18, loc="right")
    plt.grid(True)
    plt.legend(title="Samples", loc="upper right", bbox_to_anchor=(1, 1), fontsize=16)

    plt.subplots_adjust(right=0.75)
    plt.tight_layout()

    # make dir and save plot
    directory = os.path.join(base_path, "CombinedPlots", region)
    if not os.path.exists(directory):
        os.makedirs(directory)
    plt.savefig(os.path.join(directory, "combined_comparison.pdf"))
    plt.savefig(os.path.join(directory, "combined_comparison.png"))
    plt.close()


def plot_total_ttbar_ratio(base_path, data_dict, samples, regions):
    """Plot the total ttbar ratio across regions."""
    plt.figure(figsize=(12, 8))
    total_ratios = []
    for region in regions:
        fit1_data = data_dict[region]["fit1"]
        fit2_data = data_dict[region]["fit2"]
        total_ratio = calculate_total_ratio(fit1_data, fit2_data, samples)
        total_ratios.append(total_ratio)
        logging.info(f"Total ratio for region {region}: {total_ratio}")

    region_labels = [region_map.get(region, region) for region in regions]
    x_positions = range(len(regions))

    mplhep.atlas.text(text="Internal", loc=0, fontsize=20, ax=None)
    plt.step(
        x_positions,
        total_ratios,
        where="mid",
        marker="D",
        linestyle="--",
        color="red",
        label="Total $t\\bar{t}$ ratio",
    )
    plt.xticks(x_positions, region_labels, rotation=60, fontsize=12)
    plt.ylabel("Post-fit $t\\bar{t}$ yield", fontsize=20)
    plt.xlabel("Region", fontsize=20)
    plt.legend(loc="upper right", fontsize=18)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.axhline(y=1, color="black", linestyle="--", alpha=0.7)
    plt.ylim(0.85, 1.15)
    plt.text(
        0.11,
        0.92,
        r"Lepton + jets",
        fontweight="bold",
        transform=plt.gca().transAxes,
        fontsize=15,
        ha="center",
        va="center",
    )
    plt.text(
        0.235,
        0.86,
        r"$\it{\geq5j,\geq3b@70, \text{DL1r}}, \sqrt{s}$ = 13 TeV, 140 fb$^{-1}$",
        transform=plt.gca().transAxes,
        fontsize=15,
        ha="center",
        va="center",
    )
    plt.tight_layout()
    plt.savefig(os.path.join(base_path, "total_ttbar_ratio.pdf"))
    plt.savefig(os.path.join(base_path, "total_ttbar_ratio.png"))
    plt.close()


if __name__ == "__main__":

    # ============================= CONFIGURATION =============================

    # regions to compare (names must match those in the YAML files!)
    regions = [
        "ttH_STXS1_1l",
        "ttH_STXS2_1l",
        "ttH_STXS3_1l",
        "ttH_STXS4_1l",
        "ttH_STXS5_1l",
        "ttH_STXS6_1l",
    ]

    # samples to compare (names must match those in the YAML files!)
    samples = [
        "#it{t#bar{t} + 1b}",
        "#it{t#bar{t} + B}",
        "#it{t#bar{t} + #geq 2b}",
        "#it{t#bar{t} + #geq 1c}",
        "#it{t#bar{t}} + light",
    ]

    # path to yields for the two fits to compare
    base_path_1 = "/Users/levievans/Desktop/PhD/3rd-YEAR/Fits/Fit_Results_04_03_24/Fits/1l_STXS_BONLY/Fit_1l/Plots"

    base_path_2 = "/Users/levievans/Desktop/PhD/3rd-YEAR/Fits/Fit_Results_04_03_24/Fit_Studies/STXS_split_CR/1l_tt2b_STXS_split_BONLY/Fit_1l/Plots"

    # path to save the plots
    save_path = "/Users/levievans/Desktop/PhD/3rd-YEAR/Fits/Fit_Results_04_03_24/Fit_Studies/STXS_split_CR/BackgroundPrediction"

    data_dict = collect_data(base_path_1, base_path_2, regions)

    for region in regions:
        for sample in samples:
            # per sample per region plots
            plot_comparison(base_path_1, data_dict, sample, region)
        # per region plots
        plot_combined_comparison(save_path, data_dict, samples, region)

    # total ttbar ratio across all specified regions
    plot_total_ttbar_ratio(save_path, data_dict, samples, regions)

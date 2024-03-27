#!/usr/bin/env python3

import argparse
import awkward as ak
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import uproot

"""
=================================
== Systematic shape comparison ==
=================================

Description:
    - Small script to compare systematic variations to normalised signal contributions in the ttH signal region(s).

Usage:
    - run like so: ./shape.py -c 1l -r STXS3 -s ttH3 -p /path/to/save/figures

Notes:
    - Currently, the systematic variation is hard-coded, along with the signal samples to use.
    - The binning used for the histograms is also hard-coded in the script

TODO:
    - could add cli arguments to specify the systematic variation to use
    - could add cli args for vairable to plot
"""

# paths to the samples
base_path = "/scratch4/levans/L2_ttHbb_Production_212238_v5/"


def get_signal_path(channel):
    if channel == "1l":
        return base_path + f"{channel}/5j3b_discriminant_ttH/"
    if channel == "2l":
        return base_path + f"{channel}/3j3b_discriminant_ttH/"
    raise ValueError("Invalid channel specified.")

# signal samples
signal_files = [
    "ttH_PP8_mc16a.root",
    "ttH_PP8_mc16d.root",
    "ttH_PP8_mc16e.root",
]

# ttbb pThard samples
syst_uncertainty_files = [
    # = ptHard = 1 =
    "ttbb_PP8_pthard1_mc16a.root",
    "ttbb_PP8_pthard1_mc16d.root",
    "ttbb_PP8_pthard1_mc16e.root",

    #  = dipole PS =
    # "ttbb_PP8_dipolerecoil_mc16a_AFII.root",
    # "ttbb_PP8_dipolerecoil_mc16d_AFII.root",
    # "ttbb_PP8_dipolerecoil_mc16e_AFII.root",
]

# ttbb samples
nominal_files = [
    "ttbb_PP8_mc16a.root",
    "ttbb_PP8_mc16d.root",
    "ttbb_PP8_mc16e.root",
]

# define the branches to read
branches = [
    "HF_SimpleClassification",
    "HF_Classification",
    "weight_mc",
    "weight_normalise",
    "weight_pileup",
    "weight_leptonSF",
    "weight_jvt",
    "weight_L2_bTag_DL1r_Continuous",
    "weight_leptonSF_SOFTMU_corr_based",
    "randomRunNumber",
    "L2_Class_ttH_discriminant",
    "L2_Reco_higgs_pt",
    "truth_higgs_pt",
]


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Plot Systematic shape comparisons with normalised signal"
    )
    parser.add_argument(
        "--signal_path",
        type=str,
        help="Path to the signal sample",
    )
    parser.add_argument(
        "-c",
        "--channel",
        type=str,
        help="The channel to plot. Options: 1l, 2l",
    )
    parser.add_argument(
        "-r",
        "--region",
        type=str,
        help="The signal region to plot."
        "Options: STXS1, STXS2, STXS3, STXS4, STXS5, STXS6, all",
    )
    parser.add_argument(
        "-s",
        "--signal-sample",
        type=str,
        help="The signal sample to plot."
        "Options: ttH1, ttH2, ttH3, ttH4, ttH5, ttH6, all",
    )
    parser.add_argument(
        "-p",
        "--savepath",
        type=str,
        help="Path to save the plots.",
    )
    return parser.parse_args()


def xsec_norm(events):
    # values taken from https://gitlab.cern.ch/atlasHTop/ANA-HIGG-2020-24/ttHbb-fits/-/blob/master/legacy_analysis/replacements.yaml?ref_type=heads
    return events * 1.083924506 # pThard1
    # return events *

def symmetrise_variation(nominal_hist, variation_hist):
    return 2 * nominal_hist - variation_hist


def selection_tt2b(events):
    return (events.HF_SimpleClassification == 1) & (
        ((events.HF_Classification >= 200) & (events.HF_Classification < 1000))
        | (events.HF_Classification >= 1100)
    )


def selection_ttH(events, signal):
    criteria = {
        "ttH1": (events.truth_higgs_pt >= 0) & (events.truth_higgs_pt < 60000),
        "ttH2": (events.truth_higgs_pt >= 60000) & (events.truth_higgs_pt < 120000),
        "ttH3": (events.truth_higgs_pt >= 120000) & (events.truth_higgs_pt < 200000),
        "ttH4": (events.truth_higgs_pt >= 200000) & (events.truth_higgs_pt < 300000),
        "ttH5": (events.truth_higgs_pt >= 300000) & (events.truth_higgs_pt < 450000),
        "ttH6": (events.truth_higgs_pt >= 450000),
        "all": (events.truth_higgs_pt >= 0),
    }
    return criteria[signal]


def region_criteria_STXS(events, channel, region):
    criteria = {
        "1l": {
            "STXS1": (events.L2_Reco_higgs_pt >= 0) & (events.L2_Reco_higgs_pt < 60000),
            "STXS2": (events.L2_Reco_higgs_pt >= 60000)
            & (events.L2_Reco_higgs_pt < 114000),
            "STXS3": (events.L2_Reco_higgs_pt >= 114000)
            & (events.L2_Reco_higgs_pt < 192000),
            "STXS4": (events.L2_Reco_higgs_pt >= 192000)
            & (events.L2_Reco_higgs_pt < 282000),
            "STXS5": (events.L2_Reco_higgs_pt >= 282000)
            & (events.L2_Reco_higgs_pt < 408000),
            "STXS6": (events.L2_Reco_higgs_pt >= 408000),
        },
        "2l": {
            "STXS1": (events.L2_Reco_higgs_pt >= 0) & (events.L2_Reco_higgs_pt < 60000),
            "STXS2": (events.L2_Reco_higgs_pt >= 60000)
            & (events.L2_Reco_higgs_pt < 114000),
            "STXS3": (events.L2_Reco_higgs_pt >= 114000)
            & (events.L2_Reco_higgs_pt < 186000),
            "STXS4": (events.L2_Reco_higgs_pt >= 186000)
            & (events.L2_Reco_higgs_pt < 270000),
            "STXS5": (events.L2_Reco_higgs_pt >= 270000)
            & (events.L2_Reco_higgs_pt < 402000),
            "STXS6": (events.L2_Reco_higgs_pt >= 402000),
        },
    }
    return criteria[channel][region]


def event_weight(events):
    luminosity_weight = ak.where(
        events.randomRunNumber <= 311481,
        36646.74,
        ak.where(events.randomRunNumber <= 340453, 44630.6, 58791.6),
    )
    return (
        events.weight_normalise
        * events.weight_mc
        * events.weight_pileup
        * events.weight_leptonSF
        * events.weight_jvt
        * events.weight_L2_bTag_DL1r_Continuous
        * events.weight_leptonSF_SOFTMU_corr_based
        * luminosity_weight
    )


def normalise_histogram(hist, bin_edges):
    bin_widths = np.diff(bin_edges)
    hist_norm = hist  # / (hist.sum() * bin_widths)  # integral of 1 [removed this form of normalisation]
    return hist_norm

def normalise_signal_to_nominal(signal_hist, nominal_hist):
    """
    Normalise signal contribution to the nominal ttbb contribution.
    i.e scale total signal events to the same number of total events as the nominal ttbb sample.
    scaling factor is applied to each event.
    """
    signal_norm_factor = nominal_hist.sum() / signal_hist.sum()
    signal_hist_norm = signal_hist * signal_norm_factor
    return signal_hist_norm


def process_files(
    file_paths,
    selection_func=None,
    region_criteria_func=None,
    weight_func=None,
    xsec_norm=None,
):
    """
    Process multiple files and return concatenated events and weights.

    Args:
        file_paths (list): List of file paths to process.
        selection_func (function, optional): Function to apply event selection criteria. Default is None.
        region_criteria_func (function, optional): Function to apply region criteria. Default is None.
        weight_func (function, optional): Function to calculate event weights. Default is None.
        xsec_norm (float, optional): Cross-section normalization factor. Default is None.

    Returns:
        tuple: A tuple containing two arrays - concatenated events and concatenated weights.
    """
    all_events = []
    all_weights = []
    for file_path in file_paths:
        with uproot.open(file_path) as file:
            tree = file["nominal_Loose"]
            events = tree.arrays(branches, library="ak")
            if selection_func:
                events = events[selection_func(events)]
            if region_criteria_func:
                events = events[region_criteria_func(events)]
            all_events.append(events)
            if weight_func:
                weights = weight_func(events)
                all_weights.append(weights)
            else:
                print(f"INFO: No weights applied for file {file_path}.")
    return ak.concatenate(all_events), ak.concatenate(all_weights)


def binning(channel, region):
    bin_edges = {
        "1l": {
            "STXS1": np.array([4.072, 5.031, 6.576, 9.511, 50]),
            "STXS2": np.array([4.072, 5.050, 6.662, 9.799, 50]),
            "STXS3": np.array([4.072, 5.146, 6.940, 10.63, 50]),
            "STXS4": np.array([4.072, 5.290, 7.429, 12.01, 50]),
            "STXS5": np.array([4.072, 5.538, 7.602, 12.82, 50]),
            "STXS6": np.array([4.072, 5.242, 7.583, 13.05, 50]),
        },
        "2l": {
            "STXS1": np.array([9.031, 10.76, 13.24, 17.61, 50]),
            "STXS2": np.array([9.031, 10.80, 13.44, 18.22, 50]),
            "STXS3": np.array([9.031, 10.87, 13.85, 19.36, 50]),
            "STXS4": np.array([9.031, 11.20, 14.80, 21.60, 50]),
            "STXS5": np.array([9.031, 11.72, 16.23, 25.12, 50]),
            "STXS6": np.array([9.031, 12.15, 17.31, 28.09, 50]),
        },
    }
    return bin_edges[channel][region]


def plot_shapes(
    bin_edges,
    signal_hist_norm,
    nom_hist,
    syst_hist,
    syst_hist_minus1sigma,
    args,
):
    plt.style.use(hep.style.ROOT)
    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(11, 6),
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05},
        sharex=True,
    )

    ax1.hist(
        bin_edges[:-1],
        bins=bin_edges,
        weights=signal_hist_norm,
        label=r"$\it{t\bar{t}H \; 3}\;\text{Normalised}$",
        histtype="step",
        linewidth=2,
        linestyle="--",
        color="red",
    )
    ax1.hist(
        bin_edges[:-1],
        bins=bin_edges,
        weights=nom_hist,
        label=r"$\it{t\bar{t} + \geq 2b}$ Nominal",
        histtype="step",
        linewidth=2,
        color="black",
    )
    ax1.hist(
        bin_edges[:-1],
        bins=bin_edges,
        weights=syst_hist,
        label=r"$\it{t\bar{t} + \geq 2b\;p_{T}^{Hard} = 1 \;(+1\sigma)}$",
        histtype="step",
        linewidth=2,
        color="blue",
        linestyle="-.",
    )
    ax1.hist(
        bin_edges[:-1],
        bins=bin_edges,
        weights=syst_hist_minus1sigma,
        label=r"$\it{t\bar{t} + \geq 2b\;p_{T}^{Hard} = 1 \;(-1\sigma)}$",
        histtype="step",
        linewidth=2,
        color="green",
        linestyle="-.",
    )

    ax1.set_ylabel("Number of Events", fontsize=16)
    ax1.set_xlim(4, 50)
    ax1.legend(title="", fontsize=10, title_fontsize=14)
    hep.atlas.text(text="Internal", loc=0, ax=ax1, fontsize=14)
    ax1.grid(True, which="both", axis="both", linestyle="--", linewidth=0.5)
    ax1.tick_params(axis="both", which="major", labelsize=14)

    ratio_syst_nom = ((syst_hist - nom_hist) / nom_hist) * 100
    ratio_syst_nom_symm = ((syst_hist_minus1sigma - nom_hist) / nom_hist) * 100
    ratio_sig_syst = ((signal_hist_norm - syst_hist) / syst_hist) * 100

    ax2.stairs(
        ratio_syst_nom,
        bin_edges,
        linestyle="-",
        label="(Sys Up - Nom) / Nom",
        color="blue",
        linewidth=2,
    )
    ax2.stairs(
        ratio_syst_nom_symm,
        bin_edges,
        linestyle="-",
        label="(Sys Down - Nom) / Nom",
        color="green",
        linewidth=2,
    )
    ax2.stairs(
        ratio_sig_syst,
        bin_edges,
        linestyle="--",
        label="(Signal - Nom) / Nom",
        color="red",
        linewidth=2,
    )
    ax2.axhline(y=0, color="black", linestyle="--", linewidth=1)
    ax2.set_xlabel(r"$\it{t\bar{t}H}$ Discriminant", fontsize=16)
    ax2.set_ylabel(r"$\frac{(Syst - Nom)}{Nom}$ (%)", fontsize=14)
    ax2.set_ylim(-30, 30)

    ax2.grid(True, which="both", axis="both", linestyle="--", linewidth=0.5)
    ax2.tick_params(axis="both", which="major", labelsize=14)
    plt.subplots_adjust(right=0.75)

    plt.savefig(f"{args.savepath}/shape_comparison_{args.channel}_{args.region}.pdf")


def main():
    args = parse_arguments()
    signal_path = get_signal_path(args.channel)
    print("INFO: Starting processing")

    signal_events, signal_weights = process_files(
        [signal_path + f for f in signal_files],
        selection_func=lambda events: selection_ttH(events, args.signal_sample),
        region_criteria_func=lambda events: region_criteria_STXS(
            events, args.channel, args.region
        ),
        weight_func=event_weight,
    )

    syst_events, syst_weights = process_files(
        [signal_path + f for f in syst_uncertainty_files],
        selection_func=selection_tt2b,
        region_criteria_func=lambda events: region_criteria_STXS(
            events, args.channel, args.region
        ),
        weight_func=event_weight,
        xsec_norm=xsec_norm,
    )

    nom_events, nom_weights = process_files(
        [signal_path + f for f in nominal_files],
        selection_func=selection_tt2b,
        region_criteria_func=lambda events: region_criteria_STXS(
            events, args.channel, args.region
        ),
        weight_func=event_weight,
    )

    print(f"INFO: Raw signal events processed: {len(signal_events)}")
    print(f"INFO: Raw nominal events processed: {len(nom_events)}")
    print(f"INFO: Raw systematic variation events processed: {len(syst_events)}")

    # define the observable to plot
    signal_discriminant = signal_events["L2_Class_ttH_discriminant"]
    syst_discriminant = syst_events["L2_Class_ttH_discriminant"]
    nom_discriminant = nom_events["L2_Class_ttH_discriminant"]

    bin_edges = binning(args.channel, args.region)

    signal_hist, _ = np.histogram(
        ak.to_numpy(signal_discriminant),
        bins=bin_edges,
        weights=ak.to_numpy(signal_weights),
    )
    syst_hist, _ = np.histogram(
        ak.to_numpy(syst_discriminant),
        bins=bin_edges,
        weights=ak.to_numpy(syst_weights),
    )
    nom_hist, _ = np.histogram(
        ak.to_numpy(nom_discriminant), bins=bin_edges, weights=ak.to_numpy(nom_weights)
    )

    # symmetrise the variation for systematic uncertainty
    syst_hist_minus1sigma = symmetrise_variation(nom_hist, syst_hist)

    # mormalise signal to systematic
    signal_hist_norm = normalise_signal_to_nominal(signal_hist, nom_hist)

    # plot the comparison
    plot_shapes(
        bin_edges,
        signal_hist_norm,
        nom_hist,
        syst_hist,
        syst_hist_minus1sigma,
        args,
    )

    print(
        f"INFO: Plotting completed. Plots saved to {args.savepath} as shape_comparison_{args.channel}_{args.region}"
    )


if __name__ == "__main__":
    main()

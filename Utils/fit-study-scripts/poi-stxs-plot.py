#!/usr/bin/env python3

import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
import mplhep
import numpy as np

"""
===================
== POI STXS Plot ==
===================

Description:
    - Script to plot the POI values for each STXS bin.

Usage:
    - ./poi-stxs-plot.py

Notes:
    - point to the correct fit results file in the start of the script
    - requires stat-only fits
    - run all fits with MINOS errors on POIs

"""

# YOU WILL NEED TO RUN THIS "source /cvmfs/sft.cern.ch/lcg/views/dev3/latest/x86_64-centos7-gcc11-opt/setup.sh" BEFORE RUNNING THIS SCRIPT
mpl.style.use("seaborn-colorblind")

# Get the current date
current_date = datetime.datetime.now().strftime("%d_%m_%y")


def read_results(fit="bb", data=False, statonly=False):
    fname = '/scratch4/levans/legacy_fit_studies/Fit_Studies_Aug23_INT_NOTE_v0.4_part4_forUnblinding/Results/bb_full.txt"'
    if fit == "bb":
        if data:
            if statonly:
                fname = "/scratch4/levans/legacy_fit_studies/Fit_Studies_Aug23_INT_NOTE_v0.4_part4_forUnblinding/Results/bb_stat.txt"
            else:
                fname = "/scratch4/levans/legacy_fit_studies/Fit_Studies_Aug23_INT_NOTE_v0.4_part4_forUnblinding/Results/bb_full.txt"

    with open(fname) as f:
        lines = f.readlines()

    labels = []
    bestfit = []
    error = []
    err_up = []
    err_down = []
    for line in lines:
        try:
            split = line.split()
            labels.append(split[0])
            bestfit.append(float(split[2]))
            err_up.append(float(split[4].split(",")[0].strip("()")))
            err_down.append(float(split[4].split(",")[1].strip("()")))
            sym_err = (
                abs(err_up[-1]) + abs(err_down[-1])
            ) / 2  # Calculation for symmetric errors if needed
            if sym_err > 2:
                sym_err = 0
            error.append(sym_err)
        except:
            continue
    results = {
        "labels": labels,
        "bestfit": bestfit,
        "error": error,
        "up": err_up,
        "down": err_down,
    }
    print(results)
    return results


def plot_results(with_systs, stat_only):
    n_pois = len(with_systs["labels"])
    fig, ax = plt.subplots(figsize=(10, 5.2))

    spacing_factor = (
        1.1  # Adjust this value to increase/decrease spacing of mus in the plot
    )
    y_pos = np.arange(0, n_pois * spacing_factor, spacing_factor)[::-1]

    # line through SM
    ax.plot([1, 1], [-1, n_pois - 0.2], "--", color="grey")

    # Calculate upward and downward systematic uncertainties via quadrature subtraction
    syst_err_up = np.sqrt(
        np.array(with_systs["up"]) ** 2 - np.array(stat_only["up"]) ** 2
    )
    syst_err_down = np.sqrt(
        np.array(with_systs["down"]) ** 2 - np.array(stat_only["down"]) ** 2
    )

    # Store upward and downward statistical uncertainties for plotting
    stat_err_up = np.array(stat_only["up"])
    stat_err_down = np.array(stat_only["down"])

    # calculate systematic error via quadrature subtraction (FOR SYMMETRIC ERRORS if needed)
    syst_err = np.sqrt(
        np.asarray(with_systs["error"]) ** 2 - np.asarray(stat_only["error"]) ** 2
    )

    # stat-only error (using asymmetric errors for better representation)
    ax.errorbar(
        with_systs["bestfit"],
        y_pos - 0.15,
        # xerr=[np.array(stat_only['error']), np.array(stat_only['error'])],
        xerr=[stat_err_down, stat_err_up],
        fmt="o",
        linewidth=15,
        color="C4",
        label="stat. only",
    )

    # syst-only error (using asymmetric errors for better representation)
    ax.errorbar(
        with_systs["bestfit"],
        y_pos - 0.15,
        xerr=[syst_err_down, syst_err_up],
        fmt="o",
        linewidth=8,
        color="C5",
        label="syst. only",
    )

    # full error (using MINOS errors)
    ax.errorbar(
        with_systs["bestfit"],
        y_pos - 0.15,
        xerr=[with_systs["down"], with_systs["up"]],
        fmt="o",
        linewidth=2.5,
        color="black",
        label="with systematics",
        capsize=8,
        elinewidth=2.5,
        markeredgewidth=2.5,
    )

    x_min = min(np.asarray(with_systs["bestfit"]) - np.asarray(with_systs["error"]))
    x_max = max(np.asarray(with_systs["bestfit"]) + np.asarray(with_systs["error"]))

    # ATLAS Logo, dataset
    mplhep.atlas.text(text="Internal", loc=0, ax=ax, fontsize=14)
    ax.text(-0.9, n_pois + 0.8, r"$\sqrt{s}$ = 13 TeV, 140 fb$^{-1}$", fontsize=14)

    ax.text(x_max + 1.40, n_pois - 0.10, "Total", fontsize=13.5, weight="bold")
    ax.text(x_max + 2.10, n_pois - 0.10, "(stat.  syst.)", fontsize=13.5)
    for i, label in enumerate(with_systs["labels"]):
        # Best-fit Values
        ax.text(
            x_max + 0.7,
            y_pos[i] - 0.15,
            f"{with_systs['bestfit'][i]:.2f}",
            fontsize=15,
            weight="bold",
            verticalalignment="center",
        )
        # Total uncertainty
        ax.text(
            x_max + 1.45,
            y_pos[i] - 0.15,
            f"+{with_systs['up'][i]:.2f}\n-{with_systs['down'][i]:.2f}",
            fontsize=10,
            verticalalignment="center",
            weight="bold",
            multialignment="center",
        )
        # Statistical uncertainties
        ax.text(
            x_max + 2.10,
            y_pos[i] - 0.15,
            f"+{stat_only['up'][i]:.2f}\n-{stat_only['down'][i]:.2f}",
            fontsize=10,
            verticalalignment="center",
            multialignment="center",
        )
        # Systematic uncertainties
        ax.text(
            x_max + 2.65,
            y_pos[i] - 0.15,
            f"+{syst_err_up[i]:.2f}\n-{syst_err_down[i]:.2f}",
            fontsize=10,
            verticalalignment="center",
            multialignment="center",
        )

    ax.legend(frameon=False, fontsize="large", ncol=2)

    for item in (
        [ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels()
    ):
        item.set_fontsize("large")

    ax.tick_params(axis="both", which="major", pad=8)
    ax.tick_params(direction="in", top=True, right=True, which="both")
    ax.set_xlim([-1, 5.5])
    ax.set_ylim([-1, n_pois + 1.5])
    major_ticks = np.arange(
        0, 6, 1
    )  # Assuming you want major ticks from 0 to 5, spaced by 1
    minor_ticks = np.arange(-1, 6, 0.2)  # Assuming you want minor ticks spaced by 0.5
    ax.set_xticks(major_ticks)
    ax.set_xticks(minor_ticks, minor=True)
    ax.set_yticks(y_pos)
    nice_labels = [
        r"$\mu_{t\bar{t}H}$ ($p_T^H$ < 60 GeV)",
        r"$\mu_{t\bar{t}H}$ (60 GeV < $p_T^H$ < 120 GeV)",
        r"$\mu_{t\bar{t}H}$ (120 GeV < $p_T^H$ < 200 GeV)",
        r"$\mu_{t\bar{t}H}$ (200 GeV < $p_T^H$ < 300 GeV)",
        r"$\mu_{t\bar{t}H}$ (300 GeV < $p_T^H$ < 450 GeV)",
        r"$\mu_{t\bar{t}H}$ (450 GeV < $p_T^H$)",
    ]
    ax.set_yticklabels(nice_labels)
    ax.set_xlabel(
        r"$\mu_{t\overline{t}H} = \frac{\sigma_{t\overline{t}H}}{\sigma^{\mathrm{SM}}_{t\overline{t}H}}$",
        fontsize=20,
        labelpad=10,
    )
    # Adjust the position of x-axis label
    label = ax.xaxis.get_label()
    x, y = label.get_position()
    offset_value = 0.35  # Adjust this value to your liking
    label.set_position((x + offset_value, y))

    # Add a grid to the plot if you want
    # ax.grid(which='both')        # Display major and minor grid lines
    # ax.grid(which='minor', alpha=0.2)  # Make minor grid lines less prominent
    # ax.grid(which='major', alpha=0.5)  # Adjust alpha as needed

    fig.tight_layout()
    plt.savefig(filename_pdf)
    plt.savefig(filename_png)


if __name__ == "__main__":
    fit = "bb"
    data = True

    # Plot names that are saved
    filename_pdf = f"POI_STXS_MINOS_{current_date}.pdf"
    filename_png = f"POI_STXS_MINOS_{current_date}.png"

    stat_only = read_results(fit=fit, data=data, statonly=True)
    with_systs = read_results(fit=fit, data=data, statonly=False)
    # breakpoint()
    plot_results(with_systs, stat_only)

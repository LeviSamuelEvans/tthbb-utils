#!/usr/bin/env python3

import argparse
import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
import mplhep
import numpy as np
import yaml

"""
===================
== POI STXS Plot ==
===================

Description:
    - Script to plot the POI values for the ttH(bb) Legacy fits

Usage:
    - ./poi-stxs-plot.py -c config.yaml

Notes:
    - point to the correct fit results file in the start of the script
    - requires stat-only fits
    - run all fits with MINOS errors on POIs
    - source /cvmfs/sft.cern.ch/lcg/views/dev3/latest/x86_64-centos7-gcc11-opt/setup.sh if using lxplus

"""

plt.style.use(mplhep.style.ROOT)

current_date = datetime.datetime.now().strftime("%d_%m_%y")


def read_results(config, fit_key):
    labels = []
    bestfit = []
    error = []
    err_up = []
    err_down = []
    for item in config[fit_key]:
        key, value = item.split(" = ")
        labels.append(key.strip())
        bestfit.append(float(value.split(" +/- ")[0]))
        err_range = value.split(" +/- ")[1].strip("()")
        err_down.append(float(err_range.split(",")[0]))
        err_up.append(float(err_range.split(",")[1]))
        sym_err = (abs(err_up[-1]) + abs(err_down[-1])) / 2
        if sym_err > 2:
            sym_err = 0
        error.append(sym_err)
    fit_type, channel, _ = fit_key.split("_")
    results = {
        "labels": labels,
        "bestfit": bestfit,
        "error": error,
        "up": err_up,
        "down": err_down,
        "fit_type": fit_type,
        "channel": channel,
    }
    return results


def read_inclusive_results(config, fit_key):
    labels = []
    bestfit = []
    error = []
    err_up = []
    err_down = []
    for item in config[fit_key]:
        key, value = item.split(" = ")
        labels.append(key.strip())
        bestfit.append(float(value.split(" +/- ")[0]))
        err_range = value.split(" +/- ")[1].strip("()")
        err_down.append(float(err_range.split(",")[0]))
        err_up.append(float(err_range.split(",")[1]))
        sym_err = (abs(err_up[-1]) + abs(err_down[-1])) / 2
        if sym_err > 2:
            sym_err = 0
        error.append(sym_err)
    fit_type, channel, _ = fit_key.split("_")
    results = {
        "labels": labels,
        "bestfit": bestfit,
        "error": error,
        "up": err_up,
        "down": err_down,
        "fit_type": fit_type,
        "channel": "Inclusive",
    }
    return results


def plot_results(fit_results, inclusive_results):
    n_pois = len(fit_results[0]["labels"])
    fig, axs = plt.subplots(1, 3, figsize=(20, 7), sharey=True)

    spacing_factor = 1.05
    y_pos = np.arange(0, n_pois * spacing_factor, spacing_factor)[::-1]
    inclusive_y_pos = -1.1
    line_width_full = 3.0
    line_width_stat = 10.0
    line_width_syst = 5.0
    capsize = -0.5
    elinewidth = 2.0
    markeredgewidth = 2.5
    for i, ax in enumerate(axs):

        results_full = fit_results[i * 2]
        results_stat = fit_results[i * 2 + 1]
        inclusive_full = inclusive_results[i * 2]
        inclusive_stat = inclusive_results[i * 2 + 1]

        colors = [
            "#FFD700",
            "#069AF3",
            "black",
        ]  # gold, blue, black (https://matplotlib.org/stable/users/explain/colors/colors.html)

        x_min = min(
            np.asarray(results_full["bestfit"]) - np.asarray(results_full["down"])
        )
        x_max = max(
            np.asarray(results_full["bestfit"]) + np.asarray(results_full["up"])
        )

        # statistical error bars
        ax.errorbar(
            results_full["bestfit"],
            y_pos,
            xerr=[results_stat["down"], results_stat["up"]],
            fmt="o",
            # linewidth=line_width_stat,
            color=colors[0],
            label="Stat. only",
            capsize=capsize,
            elinewidth=line_width_stat,
            markeredgewidth=markeredgewidth,
            zorder=2,
        )

        # systematic error bars
        syst_err_up = np.sqrt(
            np.array(results_full["up"]) ** 2 - np.array(results_stat["up"]) ** 2
        )
        syst_err_down = np.sqrt(
            np.array(results_full["down"]) ** 2 - np.array(results_stat["down"]) ** 2
        )
        ax.errorbar(
            results_full["bestfit"],
            y_pos,
            xerr=[syst_err_down, syst_err_up],
            fmt="o",
            color=colors[1],
            label="Syst. only",
            capsize=capsize,
            elinewidth=line_width_syst,  # error bar line width
            markeredgewidth=markeredgewidth,
            zorder=3,
        )

        # total error bars
        ax.errorbar(
            results_full["bestfit"],
            y_pos,
            xerr=[results_full["down"], results_full["up"]],
            fmt="o",
            # linewidth=line_width_full,
            color=colors[2],
            label="Total Unc.",
            capsize=8,
            capthick=1.5,
            elinewidth=line_width_full,
            markeredgewidth=markeredgewidth,
            zorder=1,
        )

        ### INCLUSIVE PLOT

        inc_syst_err_up = np.sqrt(
            np.array(inclusive_full["up"]) ** 2 - np.array(inclusive_stat["up"]) ** 2
        )
        inc_syst_err_down = np.sqrt(
            np.array(inclusive_full["down"]) ** 2
            - np.array(inclusive_stat["down"]) ** 2
        )

        # dashed line to separate STXS and inclusive results
        ax.axhline(y=-0.5, linestyle="--", color="black", linewidth=1.5)

        # inclusive statistical error bars
        ax.errorbar(
            inclusive_full["bestfit"],
            inclusive_y_pos,
            xerr=[inclusive_stat["down"], inclusive_stat["up"]],
            fmt="o",
            color=colors[0],
            capsize=capsize,
            elinewidth=line_width_stat,
            markeredgewidth=markeredgewidth,
            zorder=2,
        )

        # inclusive systematic error bars
        ax.errorbar(
            inclusive_full["bestfit"],
            inclusive_y_pos,
            xerr=[inc_syst_err_down, inc_syst_err_up],
            fmt="o",
            color=colors[1],
            capsize=capsize,
            elinewidth=line_width_syst,
            markeredgewidth=markeredgewidth,
            zorder=3,
        )

        # Plot inclusive total error bars
        ax.errorbar(
            inclusive_full["bestfit"],
            inclusive_y_pos,
            xerr=[inclusive_full["down"], inclusive_full["up"]],
            fmt="o",
            color=colors[2],
            capsize=8,
            capthick=1.5,
            elinewidth=line_width_full,
            markeredgewidth=markeredgewidth,
            zorder=1,
        )

        ax.text(x_max + 1.4, n_pois - 0.10, "Total", fontsize=18, weight="bold")
        ax.text(x_max + 2.6, n_pois - 0.10, "(Stat.", fontsize=15)
        ax.text(x_max + 3.6, n_pois - 0.10, "Syst.)", fontsize=15)

        # STXS
        for k, label in enumerate(results_full["labels"]):
            ax.text(
                x_max + 0.35,
                y_pos[k],
                f"{results_full['bestfit'][k]:.2f}",
                fontsize=18,
                weight="bold",
                verticalalignment="center",
            )
            ax.text(
                x_max + 1.45,
                y_pos[k],
                f"+{results_full['up'][k]:.2f}\n-{results_full['down'][k]:.2f}",
                fontsize=14,
                verticalalignment="center",
                multialignment="center",
            )
            ax.text(
                x_max + 2.6,
                y_pos[k],
                f"+{results_stat['up'][k]:.2f}\n-{results_stat['down'][k]:.2f}",
                fontsize=14,
                verticalalignment="center",
                multialignment="center",
            )
            ax.text(
                x_max + 3.55,
                y_pos[k],
                f"+{syst_err_up[k]:.2f}\n-{syst_err_down[k]:.2f}",
                fontsize=14,
                verticalalignment="center",
                multialignment="center",
            )
        # INCLUSIVE
        for k, label in enumerate(inclusive_full["labels"]):
            ax.text(
                x_max + 0.35,
                inclusive_y_pos,
                f"{inclusive_full['bestfit'][k]:.2f}",
                fontsize=18,
                weight="bold",
                verticalalignment="center",
            )
            ax.text(
                x_max + 1.45,
                inclusive_y_pos,
                f"+{inclusive_full['up'][k]:.2f}\n-{inclusive_full['down'][k]:.2f}",
                fontsize=14,
                verticalalignment="center",
                multialignment="center",
            )
            ax.text(
                x_max + 2.6,
                inclusive_y_pos,
                f"+{inclusive_stat['up'][k]:.2f}\n-{inclusive_stat['down'][k]:.2f}",
                fontsize=14,
                verticalalignment="center",
                multialignment="center",
            )
            ax.text(
                x_max + 3.55,
                inclusive_y_pos,
                f"+{inc_syst_err_up[k]:.2f}\n-{inc_syst_err_down[k]:.2f}",
                fontsize=14,
                verticalalignment="center",
                multialignment="center",
            )
        ax.plot(
            [1, 1], [ax.get_ylim()[0], n_pois - 0.2], "--", color="grey"
        )  # vertical line through SM
        ax.set_xlim([x_min - 0.5, x_max + 5.0])
        ax.set_ylim([-1.8, n_pois + 1.2])
        if results_full["fit_type"] == "Combined":
            ax.text(
                4.9,
                6.5,
                f"{results_full['fit_type']}",
                fontsize=16,
                weight="bold",
                style="italic",
            )
        if results_full["fit_type"] == "Single-lepton":
            ax.text(
                4.5,
                6.5,
                f"{results_full['fit_type']}",
                fontsize=16,
                weight="bold",
                style="italic",
            )
        if results_full["fit_type"] == "Dilepton":
            ax.text(
                6.25,
                6.5,
                f"{results_full['fit_type']}",
                fontsize=16,
                weight="bold",
                style="italic",
            )
        ax.tick_params(axis="both", which="major", pad=8, labelsize=12)
        ax.tick_params(axis="both", which="minor", pad=8, labelsize=12)
        ax.tick_params(direction="in", top=True, right=True, which="both")

    nice_labels_inclusive = [
        r"$\mu_{t\bar{t}H}^{\mathrm{inc}}$",
    ]
    nice_labels_stxs = [
        r"$\mu_{t\bar{t}H}^{p_{T}^{H}[0-60)}$",
        r"$\mu_{t\bar{t}H}^{p_{T}^{H}[60-120)}$",
        r"$\mu_{t\bar{t}H}^{p_{T}^{H}[120-200)}$",
        r"$\mu_{t\bar{t}H}^{p_{T}^{H}[200-300)}$",
        r"$\mu_{t\bar{t}H}^{p_{T}^{H}[300-450)}$",
        r"$\mu_{t\bar{t}H}^{p_{T}^{H}[450-\inf)}$",
    ]

    axs[0].set_yticks(np.append(y_pos, inclusive_y_pos))
    nice_labels_stxs.extend(
        nice_labels_inclusive
    )  # some ugly hack to append the inclusive label to the STXS labels for now :/
    axs[0].set_yticklabels(nice_labels_stxs, fontsize=22)

    axs[2].set_xlabel(
        r"$\mu_{t\overline{t}H} = \frac{\sigma_{t\overline{t}H}}{\sigma^{\mathrm{SM}}_{t\overline{t}H}}$",
        fontsize=26,
        labelpad=10,
        loc="right",
    )

    axs[0].legend(frameon=False, fontsize=14, loc="upper left", ncol=2)
    axs[1].legend(frameon=False, fontsize=14, loc="upper left", ncol=2)
    axs[2].legend(frameon=False, fontsize=14, loc="upper left", ncol=2)

    atlas_label = mplhep.atlas.text("Internal", ax=axs[0], loc=0, fontsize=20)
    ax.text(-0.9, n_pois + 0.8, r"$\sqrt{s}$ = 13 TeV, 140 fb$^{-1}$", fontsize=14)

    fig.tight_layout()
    plt.subplots_adjust(wspace=0.10, top=0.9)
    plt.savefig(filename_pdf)
    plt.savefig(filename_png)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plot POI values for ttH(bb) Legacy Fits."
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        help="Path to the YAML configuration file",
    )
    args = parser.parse_args()

    filename_pdf = f"POI_{current_date}.pdf"
    filename_png = f"POI_{current_date}.png"

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    fit_results = [
        read_results(config, "Combined_STXS_full"),
        read_results(config, "Combined_STXS_stat"),
        read_results(config, "1l_STXS_full"),
        read_results(config, "1l_STXS_stat"),
        read_results(config, "2l_STXS_full"),
        read_results(config, "2l_STXS_stat"),
    ]

    inclusive_results = [
        read_inclusive_results(config, "Combined_inclusive_full"),
        read_inclusive_results(config, "Combined_inclusive_stat"),
        read_inclusive_results(config, "1l_inclusive_full"),
        read_inclusive_results(config, "1l_inclusive_stat"),
        read_inclusive_results(config, "2l_inclusive_full"),
        read_inclusive_results(config, "2l_inclusive_stat"),
    ]

    plot_results(fit_results, inclusive_results)

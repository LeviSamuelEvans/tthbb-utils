#!/usr/bin/env python3

import argparse
import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
import mplhep
import numpy as np
import yaml
import warnings
from matplotlib.ticker import AutoMinorLocator
import matplotlib.font_manager as fm


"""
===============
== POI Plots ==
===============

Description:
    - Script to plot the POI values for the ttH(bb) Legacy fits

Usage:
    - ./poi-stxs-plot.py -c xsec.yaml

Notes:
    - please refer to the xsec.yaml for the format of the input file
    - run all fits with MINOS errors on POIs
    - source /cvmfs/sft.cern.ch/lcg/views/dev3/latest/x86_64-centos7-gcc11-opt/setup.sh if using (lxplus or ur local cluster)

"""



current_date = datetime.datetime.now().strftime(
    "%d_%m_%y"
)  # for appending date to filename

# suppress some warnings that are not relevant
warnings.filterwarnings("ignore", category=RuntimeWarning)

# use ROOT style for the plots
plt.style.use(mplhep.style.ROOT)

font = fm.FontProperties(family="sans-serif", weight="bold", size=14)


def read_results(config, fit_key, channel=None):
    """Read the results from the config file and return them as a dictionary."""
    SCALING_FACTOR = 1.003700781
    labels = []
    bestfit = []
    error = []
    err_up = []
    err_down = []
    for item in config[fit_key]:
        key, value = item.split(" = ")
        labels.append(key.strip())
        bestfit.append(float(value.split(" +/- ")[0]) * SCALING_FACTOR)
        err_range = value.split(" +/- ")[1].strip("()")
        err_up.append(float(err_range.split(",")[0]) * SCALING_FACTOR)
        err_down.append(float(err_range.split(",")[1]) * SCALING_FACTOR)
        sym_err = (abs(err_up[-1]) + abs(err_down[-1])) / 2
        if sym_err > 2:
            sym_err = 0
        error.append(sym_err)
    fit_type, _, _ = fit_key.split("_")
    if channel is None:
        channel = fit_key.split("_")[1]
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


class Plotter:
    """Base class for the plotter."""

    def __init__(self, fit_results, inclusive_results):
        self.fit_results = fit_results
        self.inclusive_results = inclusive_results
        self.colors = [
            (255 / 255, 169 / 255, 14 / 255),
            (63 / 255, 144 / 255, 218 / 255),
            "black",
        ]  # orange, blue, black (aligns with Data/MC plots in paper.)

        # defining the theory uncertainties
        # https://docs.google.com/spreadsheets/d/1t4H9HfBx-pFtsTzJvgrx5dCZKAkklu6zGdtP88pjnf4/edit?gid=0#gid=0
        # PDF + dy + migrations for STXS, in quadrature
        # PDF + dy for inclusive, in quadrature
        # \lambda_y  --> (+5.8%,-9.2%)
        self.theory_uncertainties = [
            0.1349,
            0.1110,
            0.1205,
            0.1397,
            0.1582,
            0.1757,
            0.0988, # for symmetric, refer to below for the asymmetric values
        ]
        self.INC_THEORY_UP = 0.0680
        self.INC_THEORY_DOWN = 0.0988

    def plot(self):
        raise NotImplementedError

    def save_plot(self, fig, filename):
        fig.savefig(filename)
        print(f"Plot saved as {filename}")


class CombinedPlotter(Plotter):
    """Class to plot the POI values for the combined, single-lepton, and dilepton cases in a single plot.


    Parameters
    ----------
    fit_results : list
        List of dictionaries containing the fit results for the combined, single-lepton, and dilepton cases.
    inclusive_results : list
        List of dictionaries containing the inclusive results for the combined, single-lepton, and dilepton cases.
    output_format : str
        The output format for the plot. Can be 'pdf', 'png', or 'both'.

    """

    def __init__(self, fit_results, inclusive_results, output_format):
        super().__init__(fit_results, inclusive_results)
        self.output_format = output_format

    def plot(self):
        "Set up the plot and save it in the requested format."
        fig, axs = plt.subplots(1, 3, figsize=(32, 8), sharey=True)
        labels = ["Combined", "Single lepton", "Dilepton"]
        for i in range(3):
            if i == 0:
                axs[i].text(
                    -0.52, 5.9, labels[0], fontsize=21, #weight="bold", style="italic"
                )
            if i == 1:
                axs[i].text(
                    -0.39, 5.9, labels[1], fontsize=21, #weight="bold", style="italic"
                )
            else:
                axs[2].text(
                    -2.45, 5.9, labels[2], fontsize=21, #weight="bold", style="italic"
                )
            self.plot_single_result(
                axs[i],
                self.fit_results[i * 2],
                self.fit_results[i * 2 + 1],
                self.inclusive_results[i * 2],
                self.inclusive_results[i * 2 + 1],
            )
        fig.tight_layout()

        # set aspect ratio to auto
        for ax in axs:
            ax.set_aspect("auto")

        # ATLAS logo with internal label
        mplhep.atlas.text(ax=axs[0], loc=0, fontsize=22,) #text="Internal")

        # CME, lumi and higgs mass
        ax.text(
            -23.8,
            7.35,
            r"$\sqrt{s}\, =\, 13\,TeV,\, 140\, fb^{-1},\,m_{H}=125.09\, \text{GeV}$",
            fontsize=20,
            style="normal",
        )

        # x-axis label for x-sec measurement
        axs[2].set_xlabel(
            r"$\sigma_{\mathit{t\bar{t}H}}\,$/$\,{\sigma^{\mathrm{SM}}}$",
            fontsize=32,
            labelpad=8,
            loc="right",
        )

        # adjust space between subplots
        fig.subplots_adjust(wspace=0.1)

        # adjust space between subplots and figure border
        plt.subplots_adjust(left=0.14, right=0.95, top=0.90, bottom=0.15)

        # output formats
        filename = f"POI_{current_date}"
        if self.output_format == "pdf" or self.output_format == "both":
            self.save_plot(fig, f"{filename}.pdf")
        if self.output_format == "png" or self.output_format == "both":
            self.save_plot(fig, f"{filename}.png")

    def plot_single_result(
        self, ax, results_full, results_stat, inclusive_full, inclusive_stat
    ):
        """Plot the POI values for a single case (combined, single-lepton, or dilepton)."""
        n_pois = len(results_full["labels"])
        spacing_factor = 1.05
        y_pos = np.arange(0, n_pois * spacing_factor, spacing_factor)[::-1]
        inclusive_y_pos = -1.1

        # line widths
        line_width_full = 4.0
        line_width_stat = 20.0
        line_width_syst = 12.0

        capsize = 1.8
        elinewidth = 2.5
        markeredgewidth = 3.5

        x_min = min(
            np.asarray(results_full["bestfit"]) - np.asarray(results_full["down"])
        )
        x_max = max(
            np.asarray(results_full["bestfit"]) + np.asarray(results_full["up"])
        )

        band_height = 0.6

        # shaded band for the theory uncerts
        for i, y in enumerate(np.append(y_pos, inclusive_y_pos)):
            if i == len(y_pos):  # for inclusive
                theory_uncertainty_up = self.INC_THEORY_UP
                theory_uncertainty_down = self.INC_THEORY_DOWN
            else:
                theory_uncertainty_up = self.theory_uncertainties[i]
                theory_uncertainty_down = self.theory_uncertainties[i]

            label = "SM + Theory" if i == 0 else None
            ax.add_patch(
                plt.Rectangle(
                    (1 - theory_uncertainty_down, y - band_height / 2),
                    theory_uncertainty_up + theory_uncertainty_down,
                    band_height,
                    fill=False,
                    alpha=0.15,
                    hatch="xxxxxx",
                    label=label,
                )
            )

        # STXS stat. only bar
        ax.errorbar(
            results_full["bestfit"],
            y_pos,
            xerr=[results_stat["down"], results_stat["up"]],
            fmt="o",
            color=self.colors[0],
            label="Stat. only",
            elinewidth=line_width_stat,
            markeredgewidth=markeredgewidth,
            zorder=1,
        )

        # calculate the systematic uncertainties via quadrature subtraction
        syst_err_up = np.sqrt(
            np.array(results_full["up"]) ** 2 - np.array(results_stat["up"]) ** 2
        )
        syst_err_down = np.sqrt(
            np.array(results_full["down"]) ** 2 - np.array(results_stat["down"]) ** 2
        )

        # STXS syst. only bar
        ax.errorbar(
            results_full["bestfit"],
            y_pos,
            xerr=[syst_err_down, syst_err_up],
            fmt="o",
            color=self.colors[1],
            label="Syst. only",
            elinewidth=line_width_syst,
            markeredgewidth=markeredgewidth,
            zorder=2,
        )

        # STXS full uncert bar
        ax.errorbar(
            results_full["bestfit"],
            y_pos,
            xerr=[results_full["down"], results_full["up"]],
            fmt="o",
            color=self.colors[2],
            label="Total Unc.",
            capsize=8,
            capthick=2.0,
            elinewidth=line_width_full,
            markeredgewidth=markeredgewidth,
            zorder=3,
        )

        # calculate the inclusive systematic uncertainties via quadrature subtraction
        inc_syst_err_up = np.sqrt(
            np.array(inclusive_full["up"]) ** 2 - np.array(inclusive_stat["up"]) ** 2
        )
        inc_syst_err_down = np.sqrt(
            np.array(inclusive_full["down"]) ** 2
            - np.array(inclusive_stat["down"]) ** 2
        )

        # add horizontal line at the bottom to separate the inclusive results from the STXS ones
        ax.axhline(y=-0.5, linestyle="--", color="black", linewidth=1.5, zorder=0)

        # inclusive stat. only bar
        ax.errorbar(
            inclusive_full["bestfit"],
            inclusive_y_pos,
            xerr=[inclusive_stat["down"], inclusive_stat["up"]],
            fmt="o",
            color=self.colors[0],
            elinewidth=line_width_stat,
            markeredgewidth=markeredgewidth,
            zorder=1,
        )

        # inclusive syst. only bar
        ax.errorbar(
            inclusive_full["bestfit"],
            inclusive_y_pos,
            xerr=[inc_syst_err_down, inc_syst_err_up],
            fmt="o",
            color=self.colors[1],
            elinewidth=line_width_syst,
            zorder=2,
        )

        # inclusive full uncert bar
        ax.errorbar(
            inclusive_full["bestfit"],
            inclusive_y_pos,
            xerr=[inclusive_full["down"], inclusive_full["up"]],
            fmt="o",
            color=self.colors[2],
            capsize=8,
            capthick=2.0,
            elinewidth=line_width_full,
            markeredgewidth=markeredgewidth,
            zorder=3,
        )

        # Add txt for the total, stat, syst uncertainties
        ax.text(x_max + 1.62, n_pois - 0.10, "Total", fontsize=22, weight="bold")
        ax.text(x_max + 2.7, n_pois - 0.10, "( Stat.", fontsize=20)
        ax.text(x_max + 3.75, n_pois - 0.10, "Syst. )", fontsize=20)

        # add all values
        for k, label in enumerate(results_full["labels"]):
            ax.text(
                x_max + 0.75,
                y_pos[k],
                f"{results_full['bestfit'][k]:.2f}",
                fontsize=21,
                weight="bold",
                verticalalignment="center",
            )
            ax.text(
                x_max + 1.75,
                y_pos[k],
                f"+ {results_full['up'][k]:.2f}\n - {results_full['down'][k]:.2f}",
                fontsize=15,
                weight="bold",
                verticalalignment="center",
                multialignment="left",
                fontproperties=font,
            )
            ax.text(
                x_max + 2.70,
                y_pos[k],
                f" + {results_stat['up'][k]:.2f}\n -  {results_stat['down'][k]:.2f}",
                fontsize=15,
                verticalalignment="center",
                multialignment="left",
            )
            ax.text(
                x_max + 3.65,
                y_pos[k],
                f" + {syst_err_up[k]:.2f}\n -  {syst_err_down[k]:.2f}",
                fontsize=15,
                verticalalignment="center",
                multialignment="left",
            )
        for k, label in enumerate(inclusive_full["labels"]):
            ax.text(
                x_max + 0.75,
                inclusive_y_pos,
                f"{inclusive_full['bestfit'][k]:.2f}",
                fontsize=21,
                weight="bold",
                verticalalignment="center",
            )
            ax.text(
                x_max + 1.75,
                inclusive_y_pos,
                f"+ {inclusive_full['up'][k]:.2f}\n - {inclusive_full['down'][k]:.2f}",
                fontsize=14,
                weight="bold",
                verticalalignment="center",
                multialignment="center",
            )
            ax.text(
                x_max + 2.70,
                inclusive_y_pos,
                f" + {inclusive_stat['up'][k]:.2f}\n -  {inclusive_stat['down'][k]:.2f}",
                fontsize=14,
                verticalalignment="center",
                multialignment="left",
            )
            ax.text(
                x_max + 3.65,
                inclusive_y_pos,
                f" + {inc_syst_err_up[k]:.2f}\n -  {inc_syst_err_down[k]:.2f}",
                fontsize=14,
                verticalalignment="center",
                multialignment="left",
            )
        ax.plot([1, 1], [ax.get_ylim()[0], n_pois - 0.2], "--", color="grey", alpha=0.6, zorder=0)
        ax.set_xlim([x_min - 0.5, x_max + 5.0])
        ax.set_ylim([-1.8, n_pois + 1.2])
        ax.tick_params(axis="both", which="major", pad=14, labelsize=12)
        ax.tick_params(axis="both", which="minor", pad=8, labelsize=12)
        ax.tick_params(direction="in", top=True, right=True, which="both")
        ax.tick_params(axis="x", labelsize=24)
        nice_labels_inclusive = ["Inclusive"]
        nice_labels_stxs = [
            r"${\hat{p}_{T}^{H}\in[0,60)}$ GeV",
            r"${\hat{p}_{T}^{H}\in[60,120)}$ GeV",
            r"${\hat{p}_{T}^{H}\in[120,200)}$ GeV",
            r"${\hat{p}_{T}^{H}\in[200,300)}$ GeV",
            r"${\hat{p}_{T}^{H}\in[300,450)}$ GeV",
            r"${\hat{p}_{T}^{H}\in[450,\infty)}$ GeV",
        ]
        ax.set_yticks(np.append(y_pos, inclusive_y_pos))
        nice_labels_stxs.extend(nice_labels_inclusive)
        ax.set_yticklabels(nice_labels_stxs, fontsize=22)

        ax.xaxis.set_minor_locator(AutoMinorLocator(0))
        ax.yaxis.set_minor_locator(AutoMinorLocator(0))

        handles, labels = ax.get_legend_handles_labels()

        ax.legend(
            handles[::-1],
            labels[::-1],
            frameon=False,
            fontsize=19,
            loc="upper left",
            ncols=4,
            handlelength=0.6,
            handletextpad=0.5,
            borderpad=0.4,
            labelspacing=0.1,
            columnspacing=1.5,
            bbox_to_anchor=(0.025, 0.99),
        )


class SeparatePlotter(Plotter):
    """Class to plot the POI values for the combined, single-lepton, and dilepton cases in separate plots.

    Parameters
    ----------

    fit_results : list
        List of dictionaries containing the fit results for the combined, single-lepton, and dilepton cases.
    inclusive_results : list
        List of dictionaries containing the inclusive results for the combined, single-lepton, and dilepton cases.
    output_format : str
        The output format for the plot. Can be 'pdf', 'png', or 'both'.

    """

    def __init__(self, fit_results, inclusive_results, output_format):
        super().__init__(fit_results, inclusive_results)
        self.output_format = output_format

    def plot(self):
        for i in range(3):
            fig, ax = plt.subplots(figsize=(14, 8))
            self.plot_single_result(
                ax,
                self.fit_results[i * 2],
                self.fit_results[i * 2 + 1],
                self.inclusive_results[i * 2],
                self.inclusive_results[i * 2 + 1],
            )

            plt.subplots_adjust(left=0.28, right=0.90, top=0.90, bottom=0.15)
            if i == 0:
                filename = f"POI_Combined_{current_date}"
            elif i == 1:
                filename = f"POI_1l_{current_date}"
            else:

                filename = f"POI_2l_{current_date}"

            if self.output_format == "pdf" or self.output_format == "both":
                self.save_plot(fig, f"{filename}.pdf")
            if self.output_format == "png" or self.output_format == "both":
                self.save_plot(fig, f"{filename}.png")

    def plot_single_result(
        self, ax, results_full, results_stat, inclusive_full, inclusive_stat
    ):
        n_pois = len(results_full["labels"])
        spacing_factor = 1.05
        y_pos = np.arange(0, n_pois * spacing_factor, spacing_factor)[::-1]
        inclusive_y_pos = -1.1
        # line_width_full = 2.0
        # line_width_stat = 15.0
        # line_width_syst = 8.0

        line_width_full = 3.0
        line_width_stat = 17.0
        line_width_syst = 10.0

        capsize = 1.8
        elinewidth = 2.5

        # NOTE: if this is set, it will overide capthick -> https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.errorbar.html
        markeredgewidth = 3.0

        x_min = min(
            np.asarray(results_full["bestfit"]) - np.asarray(results_full["down"])
        )
        x_max = max(
            np.asarray(results_full["bestfit"]) + np.asarray(results_full["up"])
        )

        band_height = 0.6
        for i, y in enumerate(np.append(y_pos, inclusive_y_pos)):
            if i == len(y_pos):  # for inclusive
                theory_uncertainty_up = self.INC_THEORY_UP
                theory_uncertainty_down = self.INC_THEORY_DOWN
            else:
                theory_uncertainty_up = self.theory_uncertainties[i]
                theory_uncertainty_down = self.theory_uncertainties[i]

            label = "SM + Theory" if i == 0 else None
            ax.add_patch(
                plt.Rectangle(
                    (1 - theory_uncertainty_down, y - band_height / 2),
                    theory_uncertainty_up + theory_uncertainty_down,
                    band_height,
                    fill=False,
                    alpha=0.15,
                    hatch="xxxxxx",
                    label=label,
                )
            )

        ax.errorbar(
            results_full["bestfit"],
            y_pos,
            xerr=[results_stat["down"], results_stat["up"]],
            fmt="o",
            color=self.colors[0],
            label="Stat. only",
            elinewidth=line_width_stat,
            markeredgewidth=markeredgewidth,
            zorder=1,
        )

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
            color=self.colors[1],
            label="Syst. only",
            elinewidth=line_width_syst,
            markeredgewidth=markeredgewidth,
            zorder=2,
        )

        ax.errorbar(
            results_full["bestfit"],
            y_pos,
            xerr=[results_full["down"], results_full["up"]],
            fmt="o",
            color=self.colors[2],
            label="Total Unc.",
            capsize=8,
            capthick=2.0,
            elinewidth=line_width_full,
            markeredgewidth=markeredgewidth,
            zorder=3,
        )

        inc_syst_err_up = np.sqrt(
            np.array(inclusive_full["up"]) ** 2 - np.array(inclusive_stat["up"]) ** 2
        )
        inc_syst_err_down = np.sqrt(
            np.array(inclusive_full["down"]) ** 2
            - np.array(inclusive_stat["down"]) ** 2
        )
        ax.axhline(y=-0.5, linestyle="--", color="black", linewidth=1.5, zorder=0)

        ax.errorbar(
            inclusive_full["bestfit"],
            inclusive_y_pos,
            xerr=[inclusive_stat["down"], inclusive_stat["up"]],
            fmt="o",
            color=self.colors[0],
            elinewidth=line_width_stat,
            markeredgewidth=markeredgewidth,
            zorder=1,
        )

        ax.errorbar(
            inclusive_full["bestfit"],
            inclusive_y_pos,
            xerr=[inc_syst_err_down, inc_syst_err_up],
            fmt="o",
            color=self.colors[1],
            elinewidth=line_width_syst,
            zorder=2,
        )

        ax.errorbar(
            inclusive_full["bestfit"],
            inclusive_y_pos,
            xerr=[inclusive_full["down"], inclusive_full["up"]],
            fmt="o",
            color=self.colors[2],
            capsize=8,
            #capthick=0.2,
            elinewidth=line_width_full,
            markeredgewidth=markeredgewidth,
            zorder=3,
        )

        ax.text(x_max + 1.62, n_pois - 0.10, "Total", fontsize=22, weight="bold")
        ax.text(x_max + 2.7, n_pois - 0.10, "( Stat.", fontsize=20)
        ax.text(x_max + 3.5, n_pois - 0.10, "Syst. )", fontsize=20)

        for k, label in enumerate(results_full["labels"]):
            ax.text(
                x_max + 0.85,
                y_pos[k],
                f"{results_full['bestfit'][k]:.2f}",
                fontsize=21,
                weight="bold",
                verticalalignment="center",
            )
            ax.text(
                x_max + 1.75,
                y_pos[k],
                f"+ {results_full['up'][k]:.2f}\n - {results_full['down'][k]:.2f}",
                fontsize=15,
                weight="bold",
                verticalalignment="center",
                multialignment="left",
                fontproperties=font,
            )
            ax.text(
                x_max + 2.78,
                y_pos[k],
                f" + {results_stat['up'][k]:.2f}\n -  {results_stat['down'][k]:.2f}",
                fontsize=15,
                verticalalignment="center",
                multialignment="left",
            )
            ax.text(
                x_max + 3.46,
                y_pos[k],
                f" + {syst_err_up[k]:.2f}\n -  {syst_err_down[k]:.2f}",
                fontsize=15,
                verticalalignment="center",
                multialignment="left",
            )
        for k, label in enumerate(inclusive_full["labels"]):
            ax.text(
                x_max + 0.85,
                inclusive_y_pos,
                f"{inclusive_full['bestfit'][k]:.2f}",
                fontsize=20,
                weight="bold",
                verticalalignment="center",
            )
            ax.text(
                x_max + 1.75,
                inclusive_y_pos,
                f"+ {inclusive_full['up'][k]:.2f}\n - {inclusive_full['down'][k]:.2f}",
                fontsize=14,
                weight="bold",
                verticalalignment="center",
                multialignment="center",
            )
            ax.text(
                x_max + 2.78,
                inclusive_y_pos,
                f" + {inclusive_stat['up'][k]:.2f}\n -  {inclusive_stat['down'][k]:.2f}",
                fontsize=14,
                verticalalignment="center",
                multialignment="left",
            )
            ax.text(
                x_max + 3.46,
                inclusive_y_pos,
                f" + {inc_syst_err_up[k]:.2f}\n -  {inc_syst_err_down[k]:.2f}",
                fontsize=14,
                verticalalignment="center",
                multialignment="left",
            )
        ax.plot([1, 1], [ax.get_ylim()[0], n_pois - 0.2], "--", color="grey", alpha=0.6, zorder=0)
        ax.set_xlim([x_min - 0.5, x_max + 5.0])
        ax.set_ylim([-1.8, n_pois + 1.2])
        ax.tick_params(axis="both", which="major", pad=14, labelsize=12)
        ax.tick_params(axis="both", which="minor", pad=8, labelsize=12)
        ax.tick_params(direction="in", top=True, right=True, which="both")
        ax.tick_params(axis="x", labelsize=19)
        nice_labels_inclusive = ["Inclusive"]
        nice_labels_stxs = [
            r"${\hat{p}_{T}^{H}\in[0,60)}$ GeV",
            r"${\hat{p}_{T}^{H}\in[60,120)}$ GeV",
            r"${\hat{p}_{T}^{H}\in[120,200)}$ GeV",
            r"${\hat{p}_{T}^{H}\in[200,300)}$ GeV",
            r"${\hat{p}_{T}^{H}\in[300,450)}$ GeV",
            r"${\hat{p}_{T}^{H}\in[450,\infty)}$ GeV",
        ]

        ax.set_yticks(np.append(y_pos, inclusive_y_pos))
        nice_labels_stxs.extend(nice_labels_inclusive)
        ax.set_yticklabels(nice_labels_stxs, fontsize=22)
        ax.xaxis.set_minor_locator(AutoMinorLocator(0))
        ax.yaxis.set_minor_locator(AutoMinorLocator(0))

        ax.set_xlabel(
            r"$\sigma_{\mathit{t\bar{t}H}}\,$/$\,{\sigma^{\mathrm{SM}}}$",
            fontsize=28,
            labelpad=8,
            loc="right",
        )

        handles, labels = ax.get_legend_handles_labels()

        ax.legend(
            handles[::-1],
            labels[::-1],
            frameon=False,
            fontsize=15,
            loc="upper right",
            ncols=4,
            handlelength=0.6,
            handletextpad=0.5,
            borderpad=0.4,
            labelspacing=0.1,
            bbox_to_anchor=(0.99, 0.98),
            columnspacing=1.5,
        )

        mplhep.atlas.text(ax=ax, loc=4, fontsize=18, text="Internal")

        ax.text(
            -0.38,
            5.9,
            r"$\sqrt{s}\, =\, 13\,TeV,\, 140\, fb^{-1},\,m_{H}=125.09\, \text{GeV}$",
            fontsize=17,
            style="normal",
        )


def main(config_path, output_format, separate):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    def generate_results(config, channels, fit_types):
        """Generate a list of results for the given channels and fit types."""
        results = []
        for channel in channels:
            for fit_type in fit_types:
                results.append(read_results(config, f"{channel}_{fit_type}"))
        return results

    channels = ["Combined", "1l", "2l"]

    # STXS
    fit_types = ["STXS_full", "STXS_stat"]
    fit_results = generate_results(config, channels, fit_types)

    # INC
    fit_types = ["inclusive_full", "inclusive_stat"]
    inclusive_results = generate_results(config, channels, fit_types)

    # Are we generating separate plots or a combined one?
    plotter_class = SeparatePlotter if separate else CombinedPlotter
    plotter = plotter_class(fit_results, inclusive_results, output_format)

    # generate the plot
    plotter.plot()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plot POI values for ttH(bb) Legacy Fits."
    )
    parser.add_argument(
        "-c", "--config", required=True, help="Path to the YAML configuration file"
    )
    parser.add_argument(
        "-f",
        "--format",
        required=False,
        default="pdf",
        help="Specify the output format for the plot (pdf/png/both). Default is pdf",
    )
    parser.add_argument(
        "-s",
        "--separate",
        action="store_true",
        help="Generate separate plots for combined, single lepton, and dilepton cases",
    )
    args = parser.parse_args()

    main(args.config, args.format, args.separate)

#!/usr/bin/env python3

import re
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as ticker
import mplhep
import numpy as np
from math import nan

"""
=============================================================
== Post-fit Acceptance Effects of Nuisance Parameter Pulls ==
=============================================================

Description:
    - Script to visualise the post-fit acceptance effects of nuisance parameter
      pulls,both in terms of normalisation and shape effects.

Usage:
    - ./post-fit-acceptance.py
    - configure the script using the variables below main()

Notes:
    - Requires TRExFitter BuildPullTable output .tex files (NORM+SHAPE)

"""

class PFATableExtractor:
    """
    A class for extracting data from .tex files containing post-fit acceptance tables.
    Plots the results in various formats.

    Attributes:
    - base_path (str): The base path of the directory containing the .tex files.
    - sub_directory (str): The subdirectory within the base path containing the .tex files.
    - exclude_files (list): A list of filenames to exclude from the extraction process.
    - region (str): The current region being processed.
    - samples (list): A list of sample names to extract data for.
    - samples_order (list): The order in which the samples should be plotted.
    - region_order (list): The order in which the regions should be plotted.
    - Channel (str): The channel being analyzed.

    Methods:
    - extract_data_from_tex(filepath): Extracts data from a single .tex file and returns a structured dictionary.
    - extract_data_from_multiple_files(): Extracts data from multiple .tex files within a directory.
    - region_divide(pivot_norm): Draws vertical lines to divide the plot by region.
    - sample_divide(pivot_norm): Draws horizontal lines to divide the plot by sample.
    - bin_divide(pivot_norm): Draws vertical lines to divide the plot by bins.
    - plot_data(all_data): Plots the extracted data in different formats.
    """

    def __init__(self, base_path, sub_directory, exclude_files=[]):
        self.base_path = base_path
        self.sub_directory = sub_directory
        self.exclude_files = exclude_files
        self.region = None
        self.samples = ['tt+1b', 'tt+B', 'tt+≥2b','tt+≥1c', 'tt+light']
        self.samples_order = ['tt+1b', 'tt+B', 'tt+≥2b','tt+≥1c', 'tt+light']
        self.region_order = ['tt1b','ttB','tt2b','ttc','tt_light']
        self.Channel = channel

    def extract_data_from_tex(self, filepath):
        """
        Extracts data from a LaTeX file containing post-fit acceptance results.

        Args:
            filepath (str): The path to the LaTeX file.

        Returns:
            list: A list of dictionaries containing the extracted data. Each dictionary contains the following keys:
                - type (str): The type of systematic uncertainty ('norm' or 'shape').
                - sample (str): The name of the sample.
                - systematic_name (str): The name of the systematic uncertainty.
                - region (str): The name of the region.
                - bin (int): The bin number (only present for shape uncertainties).
                - percentage_change (float): The percentage change in the acceptance due to the systematic uncertainty.
        """
        # Regular expressions for extraction
        norm_pattern = re.compile(r'norm\s+(.+?)&([-\d.]+)\s+\\%')
        shape_pattern = re.compile(r'shape\s+(.+?)\sbin\s(\d+)&([-\d.]+)\s+\\%')
        sample_separator_pattern = re.compile(r'{\\color{blue}{.*?\\rightarrow.*?}} & \\')

        # Storage for extracted data
        data = []
        self.sample_index = -1
        with open(filepath, 'r') as f:
            for line in f:
                # Check for sample separator
                if sample_separator_pattern.search(line):
                    self.sample_index += 1
                    if self.sample_index >= len(self.samples):
                        print(f"Warning: sample_index ({self.sample_index}) exceeded number of samples in {filepath}")
                    continue

                # Check for norm pattern
                match = norm_pattern.search(line)
                if match:
                    data.append({
                        'type': 'norm',
                        'sample': self.samples[self.sample_index] if 0 <= self.sample_index < len(self.samples) else "unknown",
                        'systematic_name': match.group(1),
                        'region': self.region,
                        'percentage_change': float(match.group(2))
                    })

                    continue

                # Check for shape pattern
                match = shape_pattern.search(line)
                if match:
                    data.append({
                        'type': 'shape',
                        'sample': self.samples[self.sample_index] if 0 <= self.sample_index < len(self.samples) else "unknown",
                        'systematic_name': match.group(1),
                        'bin': int(match.group(2)),
                        'region': self.region,
                        'percentage_change': float(match.group(3))
                    })

        return data

    def extract_data_from_multiple_files(self):
        """
        Extracts data from multiple .tex files in a directory and returns a dictionary of the extracted data.

        Returns:
        data_dict (dict): A dictionary containing the extracted data from the .tex files.
        """
        directory_path = os.path.join(self.base_path, self.sub_directory)
        all_files = os.listdir(directory_path)

        tex_files = [f for f in all_files if f.startswith('Pulls') and f.endswith('.tex') and f not in self.exclude_files]

        data_dict = {}

        for tex_file in tex_files:
            self.region = tex_file.split('Pulls_')[1].rsplit('_', 1)[0]
            file_path = os.path.join(directory_path, tex_file)
            data = self.extract_data_from_tex(file_path)
            data_dict[tex_file] = data

        return data_dict

    def region_divide(self, pivot_norm):
        """
        Divides the regions in the pivot_norm dataframe and plots bold lines to separate them.

        Args:
        pivot_norm (pandas.DataFrame): A pandas dataframe containing the normalized pivot table.

        Returns:
        None
        """
        regions_in_order = pivot_norm.index.get_level_values('region').tolist()
        ytick_positions = []

        for idx in range(1, len(regions_in_order)):
            if regions_in_order[idx] != regions_in_order[idx-1]:
                ytick_positions.append(idx)
            idx += 1

        # Plot the bold lines based on calculated positions
        for ytick in ytick_positions:
            plt.axhline(y=ytick, color='black', linewidth=2.0)

    def sample_divide(self, pivot_norm):
        """
        Divides the samples in the pivot_norm dataframe and plots vertical lines to separate them.

        Args:
        pivot_norm (pandas.DataFrame): A dataframe containing the normalized pivot table.

        Returns:
        None
        """
        samples_in_order = pivot_norm.columns.get_level_values('sample').tolist()
        xtick_positions = []

        for idx in range(1, len(samples_in_order)):
            if samples_in_order[idx] != samples_in_order[idx-1]:
                xtick_positions.append(idx)
            idx += 1

        for xtick in xtick_positions:
            plt.axvline(xtick, color='black', linewidth=2.0)

    def bin_divide(self, pivot_norm):
        """
        Divides the bins in the pivot_norm dataframe and plots vertical lines to separate them.

        Args:
        pivot_norm (pandas.DataFrame): A dataframe containing the normalized pivot table.

        Returns:
        None
        """
        bins_in_order = pivot_norm.columns.get_level_values('bin').tolist()
        xtick_positions = []

        for idx in range(1, len(bins_in_order)):
            if bins_in_order[idx] != bins_in_order[idx-1]:
                xtick_positions.append(idx)
            idx += 1

        for xtick in xtick_positions:
            plt.axvline(xtick, color='black', linewidth=2.0)

    def plot_data(self, all_data):
        """
        Plots various graphs based on the input data.

        Parameters:
        all_data (dict): A dictionary containing data for normalisation and shape effects.

        Returns:
        None
        """
        # Extract the relevant data
        norm_data = [item for sublist in all_data.values() for item in sublist if item['type'] == 'norm']
        shape_data = [item for sublist in all_data.values() for item in sublist if item['type'] == 'shape']

        norm_df = pd.DataFrame(norm_data)
        shape_df = pd.DataFrame(shape_data)

        # ========== Bar Plot for Acceptance effects over all regions specified  ==========
        plt.figure(figsize=(15, 7))
        sns.barplot(x='sample', y='percentage_change', data=norm_df, ci='sd', capsize=0.2)
        plt.title("Normalisation Effects")
        plt.grid(True, axis='y')
        mplhep.atlas.text(text="Simulation Internal", loc=0, fontsize=16, ax=None)
        plt.tight_layout()
        plt.savefig(f'{save_directory}test_Norm.pdf', bbox_inches='tight')

        # ======= Heatmap for Shape Effects per region, per bin ==========
        shape_df.set_index(['region', 'systematic_name'], inplace=True)
        pivot_shape = shape_df.pivot_table(values='percentage_change', index=['region', 'systematic_name'], columns='bin', fill_value=nan)

        # Reset the index for sorting
        pivot_shape_reset = pivot_shape.reset_index()
        pivot_shape_reset['region_rank'] = pivot_shape_reset['region'].apply(lambda x: self.region_order.index(x) if x in self.region_order else len(self.region_order))
        pivot_shape_sorted = pivot_shape_reset.sort_values(['region_rank', 'systematic_name']).drop('region_rank', axis=1).set_index(['region', 'systematic_name'])

        plt.figure(figsize=(20, 10))
        sns.heatmap(pivot_shape_sorted, cmap="coolwarm", center=0, annot=True, fmt=".2f")
        self.region_divide(pivot_shape_sorted)
        self.bin_divide(pivot_shape_sorted)
        plt.title(f"Post-fit Shape Effects (%) {self.Channel}", fontsize=18)
        plt.rcParams["font.family"] = "Arial"
        plt.xlabel("Bin Number", fontsize=20)
        plt.ylabel("Region | Systematic", fontsize=20)
        plt.tight_layout()
        mplhep.atlas.text(text="Simulation Internal", loc=0, fontsize=16, ax=None)
        plt.savefig(f"{save_directory}test_shape_Heat.pdf", bbox_inches='tight')

        # ======= Box Plot for Acceptance effects over all regions ==========

        plt.figure(figsize=(15, 7))
        sns.boxplot(x='sample', y='percentage_change', data=norm_df)
        plt.title("Distribution of Percentage Changes")
        plt.grid(True, axis='y')
        mplhep.atlas.text(text="Simulation Internal", loc=0, fontsize=16, ax=None)
        plt.tight_layout()
        plt.savefig(f"{save_directory}test_Box_norm.pdf", bbox_inches='tight')

        # ======= Heatmap for Norm Effects per Region per sample (specified) ==========

        norm_df.set_index(['region', 'systematic_name'], inplace=True)
        pivot_norm = norm_df.pivot_table(values='percentage_change', index=['region', 'systematic_name'], columns='sample', fill_value=np.nan)
        # Order samples on the x-axis of heatmap based on ordering given in self.samples_order
        pivot_norm = pivot_norm[self.samples_order]
        pivot_norm_reset = pivot_norm.reset_index()
        pivot_norm_reset['region_rank'] = pivot_norm_reset['region'].apply(lambda x: self.region_order.index(x) if x in self.region_order else len(self.region_order))
        pivot_norm_sorted = pivot_norm_reset.sort_values(['region_rank', 'systematic_name']).drop('region_rank', axis=1).set_index(['region', 'systematic_name'])

        plt.figure(figsize=(30, 20))
        sns.heatmap(pivot_norm_sorted, cmap="coolwarm", center=0, annot=True, fmt=".2f")#, linewidths=.5, linecolor='gray')
        self.region_divide(pivot_norm_sorted)
        self.sample_divide(pivot_norm_sorted)
        plt.title(f"Post-fit Normalisation Effects (%) {self.Channel}", fontsize=18)
        plt.rcParams["font.family"] = "Arial"
        plt.tight_layout()
        mplhep.atlas.text(text="Simulation Internal", loc=0, fontsize=16, ax=None)
        plt.xticks(fontsize=16)
        plt.xlabel("Sample", fontsize=20)
        plt.ylabel("Region_Systematic", fontsize=20)
        plt.savefig(f"{save_directory}test_norm_Heat.pdf", bbox_inches='tight')


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = #

if __name__ == '__main__':
    base_path = "/Users/levievans/Desktop/PhD/3rd-YEAR/Fits/Fit_Results_09_10_23/Fits/2l_STXS_BONLY/Fit_2l/"
    #base_path = "/Users/levievans/Desktop/PhD/3rd-YEAR/Fits/Fit_Results_09_10_23/Fits/1l_STXS_BONLY/Fit_1l/"

    sub_directory = "Tables/"

    save_directory = "images/2l/"
    #save_directory = "images/1l/"

    # Excluding signal regions for now
    channel = "2l"
    #channel = "1l"

    exclude_list = [
        "Pulls_ttH_STXS1_1l.tex",
        "Pulls_ttH_STXS2_1l.tex",
        "Pulls_ttH_STXS3_1l.tex",
        "Pulls_ttH_STXS4_1l.tex",
        "Pulls_ttH_STXS5_1l.tex",
        "Pulls_ttH_STXS6_1l.tex",
        "Pulls_Full_ttH_STXS1_1l.tex",
        "Pulls_Full_ttH_STXS2_1l.tex",
        "Pulls_Full_ttH_STXS3_1l.tex",
        "Pulls_Full_ttH_STXS4_1l.tex",
        "Pulls_Full_ttH_STXS5_1l.tex",
        "Pulls_Full_ttH_STXS6_1l.tex",
        "Pulls_Full_ttH_boost_SR_1l.tex",
        "Pulls_ttH_boost_CR_1l.tex",
        "Pulls_ttH_STXS1_2l.tex",
        "Pulls_ttH_STXS2_2l.tex",
        "Pulls_ttH_STXS3_2l.tex",
        "Pulls_ttH_STXS4_2l.tex",
        "Pulls_ttH_STXS5_2l.tex",
        "Pulls_ttH_STXS6_2l.tex",
        "Pulls_Full_ttH_STXS1_2l.tex",
        "Pulls_Full_ttH_STXS2_2l.tex",
        "Pulls_Full_ttH_STXS3_2l.tex",
        "Pulls_Full_ttH_STXS4_2l.tex",
        "Pulls_Full_ttH_STXS5_2l.tex",
        "Pulls_Full_ttH_STXS6_2l.tex",
        "Pulls_Full_ttH_STXS5_2l_boost.tex",
        "Pulls_Full_ttH_STXS6_2l_boost.tex",
    ]

    extractor = PFATableExtractor(base_path, sub_directory, exclude_list)
    all_data = extractor.extract_data_from_multiple_files()

    extractor.plot_data(all_data)
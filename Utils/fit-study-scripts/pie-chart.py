#!/usr/bin/env python3

import yaml
import numpy as np
import matplotlib.pyplot as plt
import mplhep

# source /cvmfs/sft.cern.ch/lcg/views/dev3/latest/x86_64-centos7-gcc11-opt/setup.sh

"""
================
== Pie Charts ==
================

Description:
    - Script to plot pie charts for region composition.

Usage:
    - ./fitted-yields.py
    - you will then be prompted to enter the path to your YAML file (pre or post-fit) and the channel

Notes:
    - Requires TRExFitter output YAML files
    - Configure the script

"""

class PieChart:
    def __init__(self):
        pass

    def parse_yaml(self, file_name):
        with open(file_name, 'rb') as f:
            data = yaml.safe_load(f)
        return data

    @staticmethod
    def extract_region_name(file_path):
        file_name = file_path.split("/")[-1]
        region_name = file_name.split(".")[0]
        return region_name

    def calculate_yields(self, parsed_data):
        categories = [sample["Name"] for sample in parsed_data["Samples"]]
        yields = [sum(sample["Yield"]) for sample in parsed_data["Samples"]]
        return categories, yields

    def generate_pie_chart(self, categories, yields, channel_input, region_name):
        def func(pct, allvalues):
            absolute = int(pct / 100.*np.sum(allvalues))
            return "{:.1f}%\n({:d} Events)".format(pct, absolute)

        colors = [
            (0.8, 0.6, 0.8),
            (0.50, 0.0, 0.50),
            (0.29, 0.0, 0.51),
        ]

        fig, ax = plt.subplots(figsize=(12, 10))
        wedges, texts, autotexts = ax.pie(yields, autopct=lambda pct: func(pct, yields),
                                          textprops=dict(color="black"), colors=colors, pctdistance=0.7, startangle=100,
                                          wedgeprops=dict(width=0.8, edgecolor='white', linewidth=2))

        # Add composition percentages to legend
        composition_percentages = [f"{yields[i]/sum(yields)*100:.1f}%" for i in range(len(yields))]
        legend_labels = [f"{categories[i]} ({composition_percentages[i]})" for i in range(len(categories))]
        ax.legend(wedges, legend_labels, title="Categories", loc="upper right", fontsize=18, title_fontsize=18, bbox_to_anchor=(1.15, 1.0))

        plt.setp(autotexts, size=14, weight="bold")
        plt.setp(texts, size=14)

        ax.set_title(region_name.replace("_", " "), fontsize=24, weight='bold')

        mplhep.atlas.text(text="Simulation Internal", loc=2, ax=ax, fontsize=20)

        plt.tight_layout()
        plt.savefig(f"PieCharts/{channel_input}_{region_name}.png")
        plt.savefig(f"PieCharts/{channel_input}_{region_name}.pdf")

    def save_pie_chart(self, file_name, channel):
        parsed_data = self.parse_yaml(file_name)
        categories, yields = self.calculate_yields(parsed_data)
        region_name = self.extract_region_name(file_name)
        self.generate_pie_chart(categories, yields, channel, region_name)

if __name__ == "__main__":
    yaml_parser = PieChart()
    file_name = input("Enter the path to your YAML file: ")
    channel = input("Enter the channel: ")
    yaml_parser.save_pie_chart(file_name, channel)
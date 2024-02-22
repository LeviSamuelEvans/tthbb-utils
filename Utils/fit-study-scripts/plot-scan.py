import os
import yaml
import matplotlib.pyplot as plt
import glob
import mplhep as hep
import argparse

plt.style.use(hep.style.ROOT)


def read_yaml_files(folder_path, systematic) -> tuple:
    """Reads yaml files and extract x and NLL values."""
    data = []
    file_pattern = os.path.join(folder_path, f"NLLscan_{systematic}Step*.yaml")
    print(f"\n")
    print(f"INFO: Looking for files with pattern: {file_pattern}\n")
    for filename in glob.glob(file_pattern):
        # print(f"Reading file: {filename}")
        with open(filename, "r") as file:
            yaml_content = yaml.safe_load(file)
            if yaml_content:
                for entry in yaml_content:
                    data.append((entry["X"], entry["minusdeltaNLL"]))
            else:
                print(f"WARNING: No data found in {filename}")
    return data, systematic


def plot_likelihood_scan(data, systematic, savepath) -> None:
    """Plots the likelihood scan"""
    data.sort(key=lambda x: x[0])
    x_values, y_values = zip(*data)
    plt.plot(x_values, y_values, marker="o", linestyle="-", markersize=3)
    plt.xlabel(f"{systematic}", fontsize=18, fontfamily="serif")
    plt.ylabel(r"$-\Delta \ln(L)$", fontsize=18, fontfamily="serif")
    plt.grid(True)
    plt.savefig(f"{savepath}/LHscan_{systematic}.png")
    plt.savefig(f"{savepath}/LHscan_{systematic}.pdf", dpi=700)
    plt.close()
    print(
        f"INFO: Plots saved to {savepath} as LHscan_{systematic}.png and LHscan_{systematic}.pdf"
    )


def main(folder_path, systematics):
    for systematic in systematics:
        data, systematic = read_yaml_files(folder_path, systematic)
        if data:
            plot_likelihood_scan(data, systematic, save_path)
        else:
            print(f"WARNING: No data found for {systematic}, skipping plot.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plot 1D likelihood scans for given systematics."
    )
    parser.add_argument(
        "-f",
        "--folder-path",
        type=str,
        help="Path to the folder containing scan YAML files.",
    )
    parser.add_argument(
        "-p", "--save-path", type=str, help="path of the folder to save the plots."
    )
    parser.add_argument(
        "-s",
        "--systematics",
        type=str,
        help="Comma-separated list of systematics to plot.",
    )
    args = parser.parse_args()

    folder_path = args.folder_path
    systematics = args.systematics.split(",")
    save_path = args.save_path

    main(folder_path, systematics)
    print("INFO: Done!")

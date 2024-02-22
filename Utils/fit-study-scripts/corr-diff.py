#!/usr/bin/env python3

"""
===================================
== Correlation Matrix Comparison ==
===================================

visualize difference between TRExFitter correlation matrices
partially based on https://github.com/alexander-held/cabinetry/

Updated script to handle uncommon paramters and matrices of
different sizes.
Original script taken from :
https://github.com/alexander-held/TRExFitter-tools/blob/master/corrMatDiff.py

Description:
    - Script to evaluate difference in Correlation Matrices
      Useful for comparing different fit setups

Usage:
    - corr-diff.py path/to/<corr_mat_yaml1> path/to/<corr_mat_yaml2>"

"""

import pathlib
import sys
from typing import List, Tuple
import numpy as np

import matplotlib.pyplot as plt
import numpy as np
import yaml
import mplhep


PRUNING_THRESHOLD = 0.40


def load_matrices(
    m1_path: str, m2_path: str
) -> Tuple[List[str], np.ndarray, np.ndarray]:
    m1 = yaml.safe_load(pathlib.Path(m1_path).read_text())
    m2 = yaml.safe_load(pathlib.Path(m2_path).read_text())

    # Find common parameters between the two matrices
    common_params = set(m1[0]["parameters"]).intersection(set(m2[0]["parameters"]))
    if len(common_params) == 0:
        raise ValueError("no common parameters found in matrices")

    # Filter the matrices to only include rows and columns for the common parameters
    m1_indices = [m1[0]["parameters"].index(p) for p in common_params]
    m2_indices = [m2[0]["parameters"].index(p) for p in common_params]
    m1_corr_rows = np.asarray(m1[1]["correlation_rows"])[np.ix_(m1_indices, m1_indices)]
    m2_corr_rows = np.asarray(m2[1]["correlation_rows"])[np.ix_(m2_indices, m2_indices)]

    # Convert set to list for consistent ordering
    common_params_list = list(common_params)

    return common_params_list, m1_corr_rows, m2_corr_rows


def get_diff_with_threshold(
    labels: List[str], m1: np.ndarray, m2: np.ndarray, threshold=0.1
) -> Tuple[np.ndarray, np.ndarray]:
    """calculate difference between correlation matrices, and apply minimum threshold"""
    print(f"pruning threshold: {threshold}")
    if m1.shape != m2.shape:
        # resize matrices to have the same shape
        max_rows = max(m1.shape[0], m2.shape[0])
        max_cols = max(m1.shape[1], m2.shape[1])
        m1_resized = np.zeros((max_rows, max_cols))
        m2_resized = np.zeros((max_rows, max_cols))
        m1_resized[: m1.shape[0], : m1.shape[1]] = m1
        m2_resized[: m2.shape[0], : m2.shape[1]] = m2
        m1 = m1_resized
        m2 = m2_resized
        print(len(labels))
        print(m1.shape)
        print(m2.shape)

    # Check if the length of labels matches the number of rows/columns in the matrices
    if len(labels) != m1.shape[0] or len(labels) != m1.shape[1]:
        raise ValueError(
            "The length of labels does not match the number of rows/columns in the matrices."
        )

    corr_mat_diff = m1 - m2
    delete_indices = np.where(np.all(np.abs(corr_mat_diff) < threshold, axis=0))
    corr_mat_diff_pruned = np.delete(
        np.delete(corr_mat_diff, delete_indices, axis=1), delete_indices, axis=0
    )
    labels_pruned = np.delete(labels, delete_indices)
    return labels_pruned, corr_mat_diff_pruned


def visualize_corr_mat(
    labels: np.ndarray, corr_mat: np.ndarray, figure_path: str
) -> None:
    """visualize correlation matrix and save to file"""
    fig, ax = plt.subplots(
        figsize=(round(5 + len(labels) / 1.6, 1), round(3 + len(labels) / 1.6, 1)),
        dpi=100,
    )
    im = ax.imshow(corr_mat, vmin=-2, vmax=2, cmap="RdBu", origin="lower")

    # Adjust the ticks to align with grid lines
    ax.set_xticks(np.arange(len(labels)) - 0.5, minor=True)
    ax.set_yticks(np.arange(len(labels)) - 0.5, minor=True)
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))

    # Set the tick labels
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)

    # Rotate and align the x tick labels
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)
        tick.set_horizontalalignment("right")

    # Add grid lines to separate cells
    ax.grid(which="minor", color="w", linestyle="-", linewidth=2)
    ax.tick_params(which="minor", size=0)

    fig.colorbar(im, ax=ax)
    ax.set_aspect("equal", "box")
    fig.tight_layout(pad=1.1)
    fig.subplots_adjust(top=0.90, bottom=0.15)
    mplhep.atlas.text(text="Internal", loc=0, fontsize=16, ax=None)

    # Center the numbers in the grid cells
    for (j, i), corr in np.ndenumerate(corr_mat):
        text_color = "white" if abs(corr_mat[j, i]) > 0.75 else "black"
        if abs(corr) > 0.005:
            ax.text(i, j, f"{corr*100:.2f}", ha="center", va="center", color=text_color)

    print(f"saving figure as {figure_path}")
    fig.savefig(figure_path)
    plt.close(fig)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"run like this: python {__file__} corr_mat_1.yaml corr_mat_2.yaml")
        raise SystemExit
    labels, m1, m2 = load_matrices(sys.argv[-2], sys.argv[-1])
    labels_pruned, m_diff_pruned = get_diff_with_threshold(
        labels, m1, m2, threshold=PRUNING_THRESHOLD
    )
    visualize_corr_mat(labels_pruned, m_diff_pruned, "corr_diff.pdf")

#!/usr/bin/env python3

"""
===================================
== Correlation Matrix Comparison ==
===================================

Description:
    - Script to evaluate difference in Correlation Matrices
      Useful for comparing different fit setups

Usage:
    - CorrDiff.py path/to/<yaml_file1> path/to/<yaml_file2>"

Notes:
    - if you using the yaml files from TRExFitter, you'll
      need to slightly change the formatting of the yaml
      files
      e.g -parameters to parameters
          -correlation_rows to correlation rows
      This ensures we load the correct type (dictionary)
      when loading the yaml files.

- v1.0 Features:
    - Outputs a list of parameters that are above the threshold in one matrix
      but not the other
    - Calculates the relative difference between two correlation matrices
    - Calculates the absolute difference between two correlation matrices

TODO:
    - Add option to save the difference matrix as a yaml file
      This could be used as input into TRExFitter (Hacky)
    - Fix the plotting of the difference matrix
    - fix printout of non-matching parameters
    - Add option to specify threshold value in cmd line
    - command line options in general (e.g. save plots, save yaml file, etc)
"""

import sys
import numpy as np
import yaml
import matplotlib.pyplot as plt

 # Load the correlation matrix from a YAML file
def load_correlation_matrix_from_yaml(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    # Check if the loaded data is a dictionary
    if not isinstance(data, dict):
        print("Error: The YAML file is not formatted correctly.")
        sys.exit(1)

    parameters = data.get("parameters")
    correlation_rows = data.get("correlation_rows")

    if parameters is None or correlation_rows is None:
        print("Error: The YAML files do not contain both 'parameters' and 'correlation_rows' fields.")
        sys.exit(1)

    correlation_matrix = np.array(correlation_rows)

    if len(parameters) != correlation_matrix.shape[0] or correlation_matrix.shape[0] != correlation_matrix.shape[1]:
        print("Error: The parameters and the dimensions of the correlation matrix do not match.")
        sys.exit(1)

    return parameters, correlation_matrix

# Calculate the relative difference between two matrices
def calculate_relative_difference(matrix1, matrix2):
    # Check for identical zero values
    is_both_zero = np.logical_and(matrix1 == 0, matrix2 == 0)
    # Avoid division by zero
    matrix1_copy = matrix1.copy()
    matrix1_copy[matrix1_copy == 0] = 1e-10
    relative_difference = (matrix2 - matrix1) / matrix1_copy
    # Assign 0 for positions where both matrices have a value of 0
    relative_difference[is_both_zero] = 0
    return relative_difference

# Calculate the absolute difference between two matrices
def calculate_absolute_difference(matrix1, matrix2):
    # Check for identical zero values
    is_both_zero = np.logical_and(matrix1 == 0, matrix2 == 0)
    # Calculate absolute difference
    absolute_difference = np.abs(matrix2 - matrix1)
    # Assign 0 for positions where both matrices have a value of 0
    absolute_difference[is_both_zero] = 0
    return absolute_difference

# Filter out values below a certain threshold
def filter_min_correlation(matrix, min_value):
    return np.where(matrix >= min_value, matrix, np.nan)

def main():
    if len(sys.argv) != 3:
        print("Usage: python calculate_correlation_difference.py <yaml_file1> <yaml_file2>")
        sys.exit(1)

    # Set the correlation level threshold at 20% (akin to standard TRExFitter)
    threshold = 0.20

    yaml_file1 = sys.argv[1]
    yaml_file2 = sys.argv[2]

    parameters1, correlation_matrix1 = load_correlation_matrix_from_yaml(yaml_file1)
    parameters2, correlation_matrix2 = load_correlation_matrix_from_yaml(yaml_file2)

    # 1. Apply the Threshold Condition
    correlation_matrix1 = filter_min_correlation(correlation_matrix1, threshold)
    correlation_matrix2 = filter_min_correlation(correlation_matrix2, threshold)

    # 2. Identify Matching Parameters
    common_parameters = list(set(parameters1) & set(parameters2))
    common_indices1 = [parameters1.index(param) for param in common_parameters]
    common_indices2 = [parameters2.index(param) for param in common_parameters]

    # List to store significant parameters
    significant_diff_params = []
    significant_diff_params_abs = []


    # 3. Compute the Relative Differences for the Common Parameters
    filtered_matrix1 = correlation_matrix1[np.ix_(common_indices1, common_indices1)]
    filtered_matrix2 = correlation_matrix2[np.ix_(common_indices2, common_indices2)]
    relative_difference_matrix = calculate_relative_difference(filtered_matrix1, filtered_matrix2)

    absolute_difference_matrix = calculate_absolute_difference(filtered_matrix1, filtered_matrix2)

    # Filter out relative differences below 20%
    relative_difference_matrix = np.where(relative_difference_matrix < 0.2, np.nan, relative_difference_matrix)

    absolute_difference_matrix = np.where(absolute_difference_matrix < 0.2, np.nan, absolute_difference_matrix)

    #print(relative_difference_matrix)
    print(absolute_difference_matrix)
    # Plotting
    n_common_params = len(common_parameters)
    fig_width = max(8, n_common_params * 0.5)
    fig_height = max(6, n_common_params * 0.4)
    plt.figure(figsize=(fig_width, fig_height))

    # For the aboslute difference matrix
    plt.imshow(absolute_difference_matrix, cmap='coolwarm', vmin=0, vmax=1)
    ax = plt.gca()  # Get current axis
    for i in range(absolute_difference_matrix.shape[0]):
        for j in range(i+1, absolute_difference_matrix.shape[1]):  # This ensures we don't check the same pair twice
            if not np.isnan(absolute_difference_matrix[i, j]):
                ax.text(j, i, f"{absolute_difference_matrix[i, j]*100:.1f}%",
                    ha='center', va='center', color='k', fontsize=8)
                # Add the parameter pair to the list
                if i != j:  # to exclude diagonal elements
                    significant_diff_params_abs.append((common_parameters[i], common_parameters[j], absolute_difference_matrix[i, j]))

    # For the relative difference difference matrix
    plt.imshow(relative_difference_matrix, cmap='coolwarm', vmin=0, vmax=1)
    ax = plt.gca()  # Get current axis
    for i in range(relative_difference_matrix.shape[0]):
        for j in range(i+1, relative_difference_matrix.shape[1]):
            if not np.isnan(relative_difference_matrix[i, j]):
                ax.text(j, i, f"{relative_difference_matrix[i, j]*100:.1f}%",
                        ha='center', va='center', color='k', fontsize=8)
                # Add the parameter pair to the list
                if i != j:  # to exclude diagonal elements
                    significant_diff_params.append((common_parameters[i], common_parameters[j], relative_difference_matrix[i, j]))

    plt.colorbar(label='Relative Difference')
    plt.title('Relative Differences Between Correlation Matrices')
    plt.xticks(np.arange(len(common_parameters)), common_parameters, rotation=45, ha='right')
    plt.yticks(np.arange(len(common_parameters)), common_parameters)
    plt.xlabel('Parameters')
    plt.ylabel('Parameters')
    plt.tight_layout()
    plt.savefig("CorrDiff.png")

    # 4. Print Non-Matching Parameters
    non_matching_params1 = [p for p in parameters1 if np.nanmax(correlation_matrix1[parameters1.index(p), :]) >= threshold]
    non_matching_params2 = [p for p in parameters2 if np.nanmax(correlation_matrix2[parameters2.index(p), :]) >= threshold]
    non_matching_params1 = set(non_matching_params1) - set(common_parameters)
    non_matching_params2 = set(non_matching_params2) - set(common_parameters)


    # For dynamic print statements here...
    threshold_percent = threshold * 100
    print("============================================================")
    print("Parameters above threshold in Matrix 1 but not in Matix 2")
    print("============================================================")
    if non_matching_params2:
        print(f"Parameters above {threshold_percent}%threshold but not present in the first matrix:", ", ".join(non_matching_params2))

    print()
    print("============================================================")
    print("Parameters above threshold in Matrix 1 but not in Matix 2")
    print("============================================================")
    if non_matching_params1:
        print(f"Parameters above {threshold_percent}%threshold but not present in the second matrix:", ", ".join(non_matching_params1))

    print()
    print("============================================================")
    print("Relative Difference Matrix")
    print("============================================================")
    print("\nParameters with significant differences:")
    for param1, param2, diff in significant_diff_params:
        value1 = filtered_matrix1[common_parameters.index(param1), common_parameters.index(param2)]
        value2 = filtered_matrix2[common_parameters.index(param1), common_parameters.index(param2)]
        print(f"Difference between {param1} ({value1*100:.1f}%) and {param2} ({value2*100:.1f}%) is {diff*100:.1f}%, which is above {threshold_percent}%.")

    print()
    print()

    print("============================================================")
    print("Absolute Difference Matrix")
    print("============================================================")
    print("\nParameters with significant differences:")
    for param1, param2, diff in significant_diff_params_abs:
        value1 = filtered_matrix1[common_parameters.index(param1), common_parameters.index(param2)]
        value2 = filtered_matrix2[common_parameters.index(param1), common_parameters.index(param2)]
        print(f"Difference between {param1} ({value1*100:.1f}%) and {param2} ({value2*100:.1f}%) is {diff*100:.1f}%, which is above {threshold_percent}%.")

if __name__ == "__main__":
    main()
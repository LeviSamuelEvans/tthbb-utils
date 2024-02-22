import numpy as np
import mplhep
import matplotlib.pyplot as plt

from scipy.stats import norm, shapiro, chisquare
from scipy.optimize import curve_fit
from sympy import symbols

"""
====================================
== Pull Significance Distribution ==
====================================

Description:
    - Script to plot the distribution of pull significances for a given fit.
      (Run fits with `MINOS: all` for best results)

Usage:
    - ./pull-sig-dist.py
    - point towards the fit results file in start of the script

Notes:

"""


plt.style.use(style="ggplot")

# Load fit results from file
fit_results_file = "combined_STXS_BONLY.txt"
fit_results = np.loadtxt(fname=fit_results_file, dtype=str, skiprows=1)


# Extract relevant columns from the fit results
nuisance_parameters = fit_results[:, 0]
best_fit_values = fit_results[:, 1].astype(dtype=float)
up_uncertainties = fit_results[:, 2].astype(dtype=float)
down_uncertainties = fit_results[:, 3].astype(dtype=float)

# Calculate pull significances
pull_significances = np.abs(best_fit_values - 0) / np.sqrt(
    1 - np.maximum(up_uncertainties, down_uncertainties) ** 2
)

# Filter positive pull significances and remove non-finite values (like inf or NaN)
positive_pull_significances = pull_significances[
    (pull_significances > 0) & np.isfinite(pull_significances)
]
mu, std = norm.fit(data=positive_pull_significances)
xmin, xmax = plt.xlim()
x = np.linspace(start=0, stop=xmax, num=10)
# Conduct the Shapiro-Wilk test for normality
stat, p = shapiro(positive_pull_significances)
print("Shapiro-Wilk Test: Statistics=%.3f, p=%.6f" % (stat, p))

# Interpret the result
alpha = 0.05
if p > alpha:
    print("Sample looks Gaussian (fail to reject H0)")
else:
    print("Sample does not look Gaussian (reject H0)")


# Define the half-Gaussian PDF
def half_gaussian(x, mu, sigma):
    return 2 * norm.pdf(x, mu, sigma)


# Create figure and axis objects
fig, ax = plt.subplots()

# Get histogram data using ax object
observed_values, bin_edges, _ = ax.hist(
    positive_pull_significances,
    bins=10,
    color="lightblue",
    edgecolor="black",
    alpha=0.7,
    density=True,
    label="Data",
)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
y = norm.pdf(x, mu, std)

# Fit the data
params, _ = curve_fit(half_gaussian, bin_centers, observed_values)

# Use mplhep function with ax to add text
mplhep.atlas.text(text="Internal", loc=0, ax=ax)

# Add Shapiro-Wilk test result to the plot
shapiro_text = "Shapiro-Wilk Test: W Statistic=%.3f, p=%.3f, α = %.3f" % (
    stat,
    p,
    alpha,
)
ax.text(
    0.99,
    0.82,
    shapiro_text,
    transform=ax.transAxes,
    fontsize=10,
    verticalalignment="top",
    horizontalalignment="right",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.5),
)

# Calculate goodness of fit using chi-squared test
expected_values = len(positive_pull_significances) * np.diff(bin_edges) * y
expected_values = expected_values / np.sum(expected_values) * np.sum(observed_values)
chi2_val, p_value = chisquare(f_obs=observed_values, f_exp=expected_values, ddof=1)

dof = len(bin_edges) - 1 - 2
chi2_per_dof = chi2_val / dof

# Display statistics in a combined box
stats_text = f"χ^2/dof = {chi2_per_dof:.2f}\np-value = {p_value:.4f}\nMean = {mu:.2f}\nStd Dev. = {std:.2f}"
ax.text(
    0.95,
    0.65,
    stats_text,
    horizontalalignment="right",
    verticalalignment="top",
    transform=ax.transAxes,
    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
)

# Plot the fit on the same ax object
plt.xlabel("Pull Significance")
plt.ylabel("Density")
plt.title("Combined Pull Significances", x=0.6)
xmin, xmax = ax.get_xlim()
x = np.linspace(0, xmax, 100)
ax.plot(x, half_gaussian(x, *params), "r-", label="Fit")
ax.legend()

# Saving the figure
plt.savefig("PullSignificance_plots/combined_pull_sig_v2.png", bbox_inches="tight")
plt.savefig("PullSignificance_plots/combined_pull_sig_v2.pdf", bbox_inches="tight")

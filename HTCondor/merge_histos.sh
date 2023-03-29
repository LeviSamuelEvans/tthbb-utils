#!/bin/bash

dir1="Histograms"
dir2="Histograms_rest"
output_dir="MergedHistograms"

mkdir -p "$output_dir"

histo_files=(
    "Fit_1l_Full_ttH_boost_SR_1l_histos.root"
    "Fit_1l_Full_ttH_STXS1_1l_histos.root"
    "Fit_1l_Full_ttH_STXS2_1l_histos.root"
    "Fit_1l_Full_ttH_STXS3_1l_histos.root"
    "Fit_1l_Full_ttH_STXS4_1l_histos.root"
    "Fit_1l_Full_ttH_STXS5_1l_histos.root"
    "Fit_1l_Full_ttH_STXS6_1l_histos.root"
    "Fit_1l_tt1b_1l_histos.root"
    "Fit_1l_tt2b_1l_histos.root"
    "Fit_1l_ttB_1l_histos.root"
    "Fit_1l_ttc_1l_histos.root"
    "Fit_1l_ttH_boost_CR_1l_histos.root"
    "Fit_1l_ttH_boost_SR_1l_histos.root"
    "Fit_1l_ttH_STXS1_1l_histos.root"
    "Fit_1l_ttH_STXS2_1l_histos.root"
    "Fit_1l_ttH_STXS3_1l_histos.root"
    "Fit_1l_ttH_STXS4_1l_histos.root"
    "Fit_1l_ttH_STXS5_1l_histos.root"
    "Fit_1l_ttH_STXS6_1l_histos.root"
    "Fit_1l_tt_light_1l_histos.root"
)

for file in "${histo_files[@]}"; do
    hadd -f "${output_dir}/${file}" "${dir1}/${file}" "${dir2}/${file}"
done

echo "Merged histograms saved to ${output_dir}"
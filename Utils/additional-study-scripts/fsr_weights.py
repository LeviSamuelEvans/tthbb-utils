"""
===================================
== Final State Radiation Weights ==
===================================

Description:
    Script to plot distributions of FSR weights
    The FSR systematic is parameterised by generator weights where alpha_s is varied by
    a factor of 0.5 and 2.0. The nominal weight is the central value of the alpha_s variation.
    
    However, these weights have been shown to produce a systematic variation that is 
    dominated by noise. Hence, this supplements a study into placing a cut on weights in the 
    tail of the distribution, to reduce impact of the systematic.

Usage: 
    Simply run with python3 weights.py
    a CSV file will be saved with all weights per sample and region specified
    plots will be saved in the plots directory, individually and combined
    
Notes: 

"""


import ROOT
from copy import deepcopy
import os
import matplotlib.pyplot as plt
import mplhep as hep
import pandas as pd
import csv
import numpy as np

# ttlight selection
def selection_ttlight(event):
    return event.HF_SimpleClassification == 0

# full event weight
def event_weight(event):
    if event.randomRunNumber <= 311481:
        luminosity_weight = 36646.74
    elif event.randomRunNumber <= 340453:
        luminosity_weight = 44630.6
    else:
        luminosity_weight = 58791.6
    return (event.weight_normalise * event.weight_mc * event.weight_pileup *
            event.weight_leptonSF * event.weight_jvt * event.weight_L2_bTag_DL1r_Continuous *
            event.weight_leptonSF_SOFTMU_corr_based * luminosity_weight)
# monte-carlo weight
def weight_mc(event):
    return event.weight_mc

# ht reweight weights
def weight_ht_reweight_nominal(event):
    return event.weight_ht_reweight_nominal

# fsr (up/down)
def calculate_fsr_var(event):
    fsr_up_value = getattr(event, 'weight_fsr_up', 1) 
    return fsr_up_value

# fsr/mc weights (up/down)
def calculate_fsr_mc(event):
    weight_mc_value = weight_mc(event) 
    fsr_up_value = getattr(event, 'weight_fsr_up', 1) 
    return fsr_up_value / weight_mc_value

def apply_selection(event, selection_criteria):
    """
    Apply selection criteria to an event.

    Parameters:
    - event: The event to evaluate.
    - selection_criteria: A function that takes an event and returns a boolean indicating if the event passes the selection.

    Returns:
    - Boolean indicating if the event passes the selection.
    """
    return selection_criteria(event)

def save_fsr_weights_to_csv(chains, selections, weights, output_csv):
    """
    Save FSR weight distributions for given samples and selections to a CSV file.

    Parameters:
    - chains: Dictionary of ROOT TChains for each sample.
    - selections: Dictionary of selection functions for each sample.
    - weights: Dictionary of weight expressions for each sample.
    - output_csv: String, path to the output CSV file.
    """
    with open(output_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Sample', 'FSR_Weight', 'FSR_Weight_MC'])

        for sample, chain in chains.items():
            if sample not in selections or sample not in weights:
                print(f"Skipping {sample} due to missing selection or weight definition.")
                continue

            # get selection and weight functions
            selection_criteria = selections[sample]
            weight_function = weights[sample] 
            
            # loop over events in chain and then apply our selections
            for event in chain:
                if apply_selection(event, selection_criteria):
                    fsr_weight = calculate_fsr_var(event) * weight_function(event)
                    fsr_weight_mc = calculate_fsr_mc(event) * weight_function(event)
                    writer.writerow([sample, fsr_weight, fsr_weight_mc])
                    
def plot_fsr_weights_from_csv(input_csv, output_directory='plots/'):
    # label dictionary for plot aesthetics
    label_dict = {
        "FSR_Weight ttlight ttH Region": r"$\it{t\bar{t} + light}$ in $\it{t\bar{t}H}$ Region",
        "FSR_Weight ttlight tt1b Region": r"$\it{t\bar{t} + light}$ in $\it{t\bar{t} + 1b}$ Region",
        "FSR_Weight ttlight ttB Region": r"$\it{t\bar{t} + light}$ in $\it{t\bar{t} + 1B}$ Region",
        "FSR_Weight ttlight tt2b Region": r"$\it{t\bar{t} + light}$ in $\it{t\bar{t} + \geq{2b}}$ Region",
        "FSR_Weight ttlight ttc Region": r"$\it{t\bar{t} + light}$ in $\it{t\bar{t} + \geq{1c}}$ Region",
        "FSR_Weight ttlight ttlight Region": r"$\it{t\bar{t} + light}$ in $\it{t\bar{t} + light}$ Region",
    }
    
    # read the csv file
    df = pd.read_csv(input_csv)
    
    os.makedirs(output_directory, exist_ok=True)
    
    # split the sample column
    df[['Sample', 'Region']] = df['Sample'].str.split('_', expand=True)
    
    # define the cases to plot and their properties
    cases = ['FSR_Weight', 'FSR_Weight_MC']
    ranges = {'FSR_Weight': [-200, 50000], 'FSR_Weight_MC': [0, 5]}
    bins_values = {'FSR_Weight': np.linspace(-200, 50000, 100), 'FSR_Weight_MC': np.linspace(0, 5, 50)}
    
    # loop over each weight case for combined plots
    for case in cases:
        fig_combined, ax_combined = plt.subplots()

        # loop over the samples and regions for individual plots
        for sample in df['Sample'].unique():
            for region in df['Region'].unique():
                sample_df = df[(df['Sample'] == sample) & (df['Region'] == region)]
                
                plot_label = f'{case} {sample} {region} Region'
                print(f"Original label: {plot_label}")
                
                if case in sample_df:
                    fig, ax = plt.subplots()
                    counts, bins, patches = ax.hist(sample_df[case], bins=bins_values[case], range=ranges[case], histtype='step', label=f'{case} {sample} {region} Region', density=False)
                    ax_combined.hist(sample_df[case], bins=bins_values[case], range=ranges[case], histtype='step', label=f'{case} {sample} {region} Region', density=False)
                    
                    # calc stats
                    entries = len(sample_df[case])
                    mean = sample_df[case].mean()
                    std_dev = sample_df[case].std()
                    
                    # text-box for statistics
                    stats_text = f'Entries: {entries}\nMean: {mean:.2f}\nStd Dev: {std_dev:.2f}'
                    ax.text(0.70, 0.87, stats_text, transform=ax.transAxes, fontsize=18,
                            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))
                    
                    # indi plots
                    handles, labels = ax.get_legend_handles_labels()
                    labels = [label_dict.get(label, label) for label in labels]
                    ax.set_xlabel('Final State Radiation Generator Weights', fontsize=18)
                    ax.set_ylabel('Events')
                    ax.legend(handles, labels)
                    ax.set_yscale('log')
                    ax.set_title('FSR Up Variation', fontsize=28, x=0.52, y=1.07)
                    hep.atlas.text(text="Internal", loc=0, fontsize=20, ax=ax)
                    
                    plt.savefig(f"{output_directory}/{sample}_{region}_{case}.png")
                    plt.close(fig)
        
        # combined plot
        handles_combined, labels_combined = ax_combined.get_legend_handles_labels()
        labels_combined = [label_dict.get(label, label) for label in labels_combined]
        ax_combined.set_xlabel('Final State Radiation Generator Weights', fontsize=18)
        ax_combined.set_ylabel('Events', fontsize=18)
        ax_combined.legend(handles_combined, labels_combined)
        ax_combined.set_yscale('log')
        ax_combined.set_title('FSR Up Variation', fontsize=28, x=0.52, y=1.07)
        hep.atlas.text(text="Internal", loc=0, fontsize=20, ax=ax_combined)
        
        plt.savefig(f"{output_directory}/combined_{case}.png")
        plt.savefig(f"{output_directory}/combined_{case}.pdf")
        plt.close(fig_combined)


def chain_samples(ntuple_path, regions, samples, data, chain_dict):
    for s in samples:
        file_dict_aux = {}
        tree_dict_aux = {}
        tchain = ROOT.TChain('nominal_Loose')
        if s=='data':
            data_aux = data_data
        else:
            data_aux = data
        for r in regions:
            for d in data_aux:
                # Open file
                file_dict_aux['f_'+r+'_'+s+'_'+d] = ntuple_path+regions[r]+samples[s]+data_aux[d]+'.root'
        for entry in file_dict_aux:
            tchain.Add(file_dict_aux[entry])
        chain_dict[s] = deepcopy(tchain)


if __name__ == "__main__":
    
    ROOT.gROOT.SetBatch(ROOT.kTRUE)
    ROOT.gStyle.SetOptStat(0)
    
    ntuple_path = '/scratch4/levans/L2_ttHbb_Production_212238_v5/'
    
    regions = {
    '5j3b_ttbb':'1l/5j3b_discriminant_ttbb/',
    '5j3b_ttb':'1l/5j3b_discriminant_ttb/',
    '5j3b_ttB':'1l/5j3b_discriminant_ttB/',
    '5j3b_ttc':'1l/5j3b_discriminant_ttc/',
    '5j3b_ttH':'1l/5j3b_discriminant_ttH/',
    '5j3b_ttlight':'1l/5j3b_discriminant_ttlight/',
    }

    samples = {
    'ttlight_ttH':'tt_PP8',
    'ttlight_tt1b':'tt_PP8',
    'ttlight_ttB':'tt_PP8',
    'ttlight_tt2b':'tt_PP8',
    'ttlight_ttc':'tt_PP8',
    'ttlight_ttlight':'tt_PP8',
    }

    data = {
    'mc16a':'_mc16a',
    'mc16d':'_mc16d',
    'mc16e':'_mc16e',
    }
    
    chain_dict = {}
    
    chain_samples(ntuple_path, regions, samples, data, chain_dict)


    mc_weight = 'weight_normalise*weight_mc*weight_pileup*weight_leptonSF*weight_jvt*weight_L2_bTag_DL1r_Continuous*weight_leptonSF_SOFTMU_corr_based*(randomRunNumber<=311481 ? 36646.74 : (randomRunNumber<=340453 ? 44630.6 : 58791.6))'
    

    weight_dict = {
        'data': '1',  
        'ttbb': mc_weight, 
        'tt': mc_weight,  
        'ttH': mc_weight,
        'ttlight_ttH': weight_ht_reweight_nominal,
        'ttlight_tt1b': weight_ht_reweight_nominal,
        'ttlight_ttB': weight_ht_reweight_nominal,
        'ttlight_tt2b': weight_ht_reweight_nominal,
        'ttlight_ttc': weight_ht_reweight_nominal,
        'ttlight_ttlight': weight_ht_reweight_nominal,
    }

    # set up the selections needed
    # sel_5j3b = '(passedOfflineBoostedSelection == 0)'
    # sel_ttb = '(HF_SimpleClassification == 1 && (HF_Classification >= 1000 && HF_Classification < 1100))'
    # sel_ttB = '(HF_SimpleClassification == 1 && ((HF_Classification >= 200 && HF_Classification < 1000) || HF_Classification >= 1100))'
    # sel_ttbb = '(HF_SimpleClassification == 1 && ((HF_Classification >= 200 && HF_Classification < 1000) || HF_Classification >= 1100))'
    # sel_ttc = '(HF_SimpleClassification == -1)*(weight_ht_reweight_nominal)'
    # sel_ttlight = '(HF_SimpleClassification == 0)*(weight_ht_reweight_nominal)'
    
    
    # Region selections
    
    def sel_5j3b(event):
        return event.passedOfflineBoostedSelection == 0
    
    def sel_ttH_node(event):
        return event.L2_Class_discriminant_class == 0
    
    def sel_tt1b_node(event):
        return event.L2_Class_discriminant_class == 1
    
    def sel_ttB_node(event):
        return event.L2_Class_discriminant_class == 2
    
    def sel_tt2b_node(event):
        return event.L2_Class_discriminant_class == 3
    
    def sel_ttc_node(event):
        return event.L2_Class_discriminant_class == 4
    
    def sel_ttlight_node(event):
        return event.L2_Class_discriminant_class == 5


    # the selection dictionary for all samples
    
    sel_dict = {
        'ttlight_ttH': lambda event: selection_ttlight(event) and sel_ttH_node(event),           
        'ttlight_tt1b': lambda event: selection_ttlight(event) and sel_tt1b_node(event),
        'ttlight_ttB': lambda event: selection_ttlight(event) and sel_ttB_node(event),
        'ttlight_tt2b': lambda event: selection_ttlight(event) and sel_tt2b_node(event),
        'ttlight_ttc': lambda event: selection_ttlight(event) and sel_ttc_node(event),
        'ttlight_ttlight': lambda event: selection_ttlight(event) and sel_ttlight_node(event),
    }
     
    print("working on it :D...")
    save_fsr_weights_to_csv(chain_dict, sel_dict, weight_dict, output_csv='fsr_weights_up_full.csv')
    print("FSR weights saved to CSV.")
    
    plot_fsr_weights_from_csv(input_csv='/Users/levievans/Desktop/Test/weights/FSR_up.csv') 
    print("FSR weight distribution plots saved.")
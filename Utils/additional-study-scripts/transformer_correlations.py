"""
===================================
== Transformer Node Correlations ==
===================================

Description:
    Script based on Luisa's code to create 2D correlation plots for the different nodes of the transformer model.

Usage: 
    configure dictionaries and chains below then run with `python correlations.py`

Notes: 
    - Two functions exist for plotting, one will normalise per column.
    - slight switching when plotting nJets in plot_histo function

"""


import ROOT
from copy import deepcopy
import os

# for nJet plots
nJets_min = 5
nJets_max = 10
nJets_bins = nJets_max - nJets_min + 1 

ev_sel = "5j,3b@70% DL1r"

# Dictionary to map variable names for better axis labels
var_name_map = {
    
    # Higher-level features
    'nJets': 'Number of Jets',
    'HT_all*0.001': 'H_{T}^{all}',
    'dRbb_avg_Sort4': '#Delta R_{bb}^{avg, sort4}',
    'dEtajj_MaxdEta': '#Delta#eta_{jj}^{max #Delta#eta}',
    'L2_Reco_higgs_m*0.001': 'm_{H}^{reco}',
    'L2_Reco_higgs_pt*0.001': 'p_{T}^{H}^{reco}',
    'H2_jets': 'H_{2}^{jets}',
    'Aplanarity_jets': 'Aplanarity_{jets}',
    'dRbb_HiggsMass_70': '#Delta R_{bb}^{H mass 70}',
    'H0_all': 'H_{0}^{all}',
    'H1_all': 'H_{1}^{all}',
    'L2_Class_tt2b_discriminant': '#it{t#bar{t} + #geq 2b} Discriminant',
    'L2_Class_tt1b_discriminant': '#it{t#bar{t} + 1b} Discriminant',
    'L2_Class_ttH_discriminant': '#it{t#bar{t}H} Discriminant',
    'L2_Class_ttc_discriminant': '#it{t#bar{t} + #geq 1c} Discriminant',
    'L2_Class_tt1B_discriminant': '#it{t#bar{t} + B} Discriminant',
    'L2_Class_ttlight_discriminant': '#it{t#bar{t} + light} Discriminant',
    
    # Lower-level features
    'jet_pt[jet_index_PCBT_ordered[0]]*0.001': 'Leading PCBT ordered Jet p_{T}',
    'jet_pt[jet_index_PCBT_ordered[1]]*0.001': 'Sub-leading PCBT ordered Jet p_{T}',
    'jet_pt[jet_index_PCBT_ordered[3]]*0.001': '3^{rd} leading PCBT ordered Jet p_{T}',
    'jet_pt[jet_index_PCBT_ordered[4]]*0.001': '4^{th} leading PCBT ordered Jet p_{T}',
    
    'jet_eta[jet_index_PCBT_ordered[0]]': 'Leading PCBT ordered Jet \eta',
    'jet_eta[jet_index_PCBT_ordered[1]]': 'Sub-leading PCBT ordered Jet \eta',
    'jet_eta[jet_index_PCBT_ordered[3]]': '3^{rd} leading PCBT ordered Jet \eta',
    'jet_eta[jet_index_PCBT_ordered[4]]': '4^{th} leading PCBT ordered Jet \eta',
    
    'jet_phi[jet_index_PCBT_ordered[0]]': 'Leading PCBT ordered Jet \phi',
    'jet_phi[jet_index_PCBT_ordered[1]]': 'Sub-leading PCBT ordered Jet \phi',
    'jet_phi[jet_index_PCBT_ordered[3]]': '3^{rd} leading PCBT ordered Jet \phi',
    'jet_phi[jet_index_PCBT_ordered[4]]': '4^{th} leading PCBT ordered Jet \phi',
    
    # Ratio Quantities
    'L2_Class_ttH_discriminant/L2_Class_tt2b_discriminant': 'LR #it{t#bar{t}H} / #it{t#bar{t} + #geq 2b} Discriminant',
    'L2_Class_tt2b_discriminant/L2_Class_tt1c_discriminant': 'LR #it{t#bar{t} + #geq 2b} / #it{t#bar{t} + #geq 1c} Discriminant',
    'L2_Class_ttH_discriminant/L2_Class_tt1c_discriminant': 'LR #it{t#bar{t}H} / #it{t#bar{t} + #geq 1c} Discriminant',
    
}

sample_name_map = {
    'data': 'Data',
    'ttbb': 't#bar{t}+b#bar{b}',
    'tt': 't#bar{t}',
    'ttH': 't#bar{t}H',
}

node_label_map = {
    'tt2b': '#it{t#bar{t} + #geq 2b} Node',
    'tt1b': '#it{t#bar{t} + 1b} Node',
    'ttH': '#it{t#bar{t}H} Node',
    'ttc': '#it{t#bar{t} + #geq 1c} Node',
    'ttB': '#it{t#bar{t} + B} Node',
    'ttlight': '#it{t#bar{t} + light} Node',
    'ratio': 'LR #it{t#bar{t}H / t#bar{t} + \geq2b}',
    'ratio2': 'LR #it{t#bar{t} + \geq2b / t#bar{t} + #geq 1c}',
    'ratio3': 'LR #it{{t#bar{t}H} / t#bar{t} + #geq 1c}'
}

# helper function to create directories and save plots 
def save_plot(canvas, sample_type, var_code, node_label):
    directory = f"plots_inclusive_norm_ptHard/{var_code}/{node_label}"
    os.makedirs(directory, exist_ok=True)
    filename = f"{directory}/corr5j3b_{sample_type}_{var_code}_{node_label}_node"
    canvas.SaveAs(f"{filename}.png")
    canvas.SaveAs(f"{filename}.pdf")

# helper function to set axis titles, uses var map above
def set_axis_titles(histogram, var_code):
    x_title = var_name_map.get(var_code.replace("", ""), var_code)
    y_title = "NN Discriminant"
    histogram.GetXaxis().SetTitle(x_title)
    histogram.GetYaxis().SetTitle(y_title)


# helper function to create a TLatex object to display correlation information and sample/node on the plots
def get_text(corr, ev_sel, sample, node_label):
    latex = ROOT.TLatex()
    latex.SetNDC()                   # Position text relative to the canvas size, not the axis scale
    latex.SetTextSize(0.035)         # Set the text size
    latex.SetTextAlign(13)           # Align at top left
    latex.SetTextColor(ROOT.kBlack)  # Set text color

    
    sample_desc = sample_name_map.get(sample, sample)
    node_desc = node_label_map.get(node_label, node_label)
    ev_sel_desc = ev_sel
    text = f"{sample_desc}, {node_desc}: Correlation = {corr:.2f}"
    text_sel = f"{ev_sel_desc}"
    # (x1, y1, text)
    latex.DrawLatex(0.35, 0.95, text)
    
    #latex.SetTextColor(ROOT.kWhite)
    latex.DrawLatex(0.15, 0.87, text_sel)

    return latex

# for drawing the ATLAS label (set label text for type)
def draw_atlas_label(canvas, label_text="Internal"):
    canvas.cd()
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextFont(72)
    latex.SetTextSize(0.05)
    latex.DrawLatex(0.1, 0.91, f"#font[72]{{ATLAS}} #scale[0.6]{{#font[42]{{{label_text}}}}}")
    return latex

def plot_histograms(var, var_range, node, node_label, chains, selections, weights):
    directory = f"plots/{var}"
    os.makedirs(directory, exist_ok=True)

    # Loopin over data, tt+bb, ttbar and ttH
    for sample in ['data', 'ttbb', 'tt', 'ttH']:
        c = ROOT.TCanvas(f"c_{sample}", f"c_{sample}", 1000, 700)
        c.SetRightMargin(0.15)
        hist_name = f"h_{sample}_{var}_{node_label}"
        h = ROOT.TH2F(hist_name, "", 50, var_range[0], var_range[1], 100, 0, 20) # 20 for 2b, 10 for rest, 50 for ttH
        #h = ROOT.TH2F(hist_name, "", nJets_bins, nJets_min, nJets_max+1, 50, 0, 20) # if running for jet multiplcity
        set_axis_titles(h, var)
        draw_option = "colz" if sample == 'data' else "colz same"
        selection = selections[sample]
        weight = weights[sample] if sample in weights else ""
        chains[sample].Draw(f"{node}:{var}>>{hist_name}", f"{weight} * {selection}", draw_option)
        corr = h.GetCorrelationFactor()
        get_text(corr, f"{ev_sel}, {sample}, {node_label}")
        draw_atlas_label(c)
        save_plot(c, sample, var, node_label)
        c.Close()
        h.Delete()

def plot_norm_histograms(var, var_range, node, node_label, chains, selections, weights):
    directory = f"plots/{var}"
    os.makedirs(directory, exist_ok=True)

    for sample in ['data', 'ttbb', 'tt', 'ttH']:
        c = ROOT.TCanvas(f"c_{sample}", f"c_{sample}", 1000, 700)
        c.SetRightMargin(0.15)
        hist_name = f"h_{sample}_{var}_{node_label}"
        h = ROOT.TH2F(hist_name, "", 50, var_range[0], var_range[1], 100, 0, 20)
        #h = ROOT.TH2F(hist_name, "", nJets_bins, nJets_min, nJets_max+1, 50, 0, 20) # if running for jet multiplcity
        set_axis_titles(h, var)
        draw_option = "colz" if sample == 'data' else "colz same"
        selection = selections[sample]
        weight = weights[sample] if sample in weights else ""
        chains[sample].Draw(f"{node}:{var}>>{hist_name}", f"{weight} * {selection}", draw_option)
        
        # calculate corr before normalising! :D
        corr = h.GetCorrelationFactor()
        
        # normalise per column
        for ix in range(1, h.GetNbinsX()+1):
            col_total = sum(h.GetBinContent(ix, iy) for iy in range(1, h.GetNbinsY()+1))
            if col_total > 0:
                for iy in range(1, h.GetNbinsY()+1):
                    bin_content = h.GetBinContent(ix, iy)
                    h.SetBinContent(ix, iy, bin_content / col_total)

        get_text(corr, f"{ev_sel}", sample, node_label)
        draw_atlas_label(c)
        save_plot(c, sample, var, node_label)
        c.Close()
        h.Delete()


if __name__ == "__main__":
    
    # set up ROOT
    ROOT.gROOT.SetBatch(ROOT.kTRUE)
    ROOT.gStyle.SetOptStat(0)
    
    ntuple_path = '/scratch4/levans/L2_ttHbb_Production_212238_v5/'
    
    # define our regions where we get our ntuples from
    regions = {
    '5j3b_ttbb':'1l/5j3b_discriminant_ttbb/',
    '5j3b_ttb':'1l/5j3b_discriminant_ttb/',
    '5j3b_ttB':'1l/5j3b_discriminant_ttB/',
    '5j3b_ttc':'1l/5j3b_discriminant_ttc/',
    '5j3b_ttH':'1l/5j3b_discriminant_ttH/',
    '5j3b_ttlight':'1l/5j3b_discriminant_ttlight/',
    }

    # define our samples
    samples = {
    'data':'data',
    'ttb':'ttbb_PP8_pthard1',
    'ttB':'ttbb_PP8_pthard1',
    'ttbb':'ttbb_PP8_pthard1',
    'tt':'tt_PP8',
    'ttH':'ttH_PP8',
    'ttlight':'tt_PP8'
    }

    # define mc years
    data = {
    'mc16a':'_mc16a',
    'mc16d':'_mc16d',
    'mc16e':'_mc16e',
    }

    # define data years
    data_data = {
    '2015':'_2015',
    '2016':'_2016',
    '2017':'_2017',
    '2018':'_2018',
    }

    # create chains for each sample
    chain_dict = {}

    # loop over and create the chains
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

    print('ttbb:',chain_dict['ttbb'].GetEntries())
    print('tt:',chain_dict['tt'].GetEntries())
    print('ttH:',chain_dict['ttH'].GetEntries())
    print('data:',chain_dict['data'].GetEntries())

    # Plot 2D with weights
    mc_weight = 'weight_normalise*weight_mc*weight_pileup*weight_leptonSF*weight_jvt*weight_L2_bTag_DL1r_Continuous*weight_leptonSF_SOFTMU_corr_based*(randomRunNumber<=311481 ? 36646.74 : (randomRunNumber<=340453 ? 44630.6 : 58791.6))'

    print('Using weight:',mc_weight)

    weight_dict = {
        'data': '1',  
        'ttbb': mc_weight, 
        'tt': mc_weight,  
        'ttH': mc_weight
    }

    # set up the selections needed
    sel_5j3b = '(passedOfflineBoostedSelection == 0)'
    sel_ttb = '(HF_SimpleClassification == 1 && (HF_Classification >= 1000 && HF_Classification < 1100))'
    sel_ttB = '(HF_SimpleClassification == 1 && ((HF_Classification >= 200 && HF_Classification < 1000) || HF_Classification >= 1100))'
    sel_ttbb = '(HF_SimpleClassification == 1 && ((HF_Classification >= 200 && HF_Classification < 1000) || HF_Classification >= 1100))'
    sel_ttc = '(HF_SimpleClassification == -1)*(weight_ht_reweight_nominal)'
    sel_ttlight = '(HF_SimpleClassification == 0)*(weight_ht_reweight_nominal)'
    
    # region selections (for the per region analysis add to sel_dicts below)
    sel_ttH_node = 'L2_Class_discriminant_class == 0'
    sel_tt1b_node = 'L2_Class_discriminant_class == 1'
    sel_tt1B_node = 'L2_Class_discriminant_class == 2'
    sel_tt2b_node = 'L2_Class_discriminant_class == 3'
    sel_ttc_node = 'L2_Class_discriminant_class == 4'
    sel_ttlight_node = 'L2_Class_discriminant_class == 5'

    # the selection dictionary for all samples
    sel_dict = {
        'data': sel_5j3b,                                                       # resolved data in pre-selection
        'ttbb': f"({sel_5j3b} && ({sel_ttbb}) || ({sel_ttB}) || ({sel_ttb}) )", # tt2b and ttB and ttb
        'tt': f"({sel_5j3b} && ({sel_ttc} || {sel_ttlight}))",                  # ttc and ttlight  
        'ttH': sel_5j3b                                                         # resolved ttH in pre-selection
    }
    
    print('ttbb:',chain_dict['ttbb'].GetEntries(mc_weight + ' * ' + sel_dict['ttbb']))

    var_dict = {
        
    # Higher-level features
    
    'dRbb_avg_Sort4': [1.6,3.0],
    'dEtajj_MaxdEta': [1.0,5.0],
     'HT_all*0.001': [200,1400],
    'L2_Reco_higgs_m*0.001': [50,250], 
    'nJets': [5,11],
    'H2_jets':[0.05,0.90],
    'Aplanarity_jets':[0.05,0.4],
    'dRbb_HiggsMass_70':[0.5,4.00],
    'H0_all':[0.975,1.00],
    'H1_all':[0.00,0.95],
    'L2_Class_tt2b_discriminant':[0,20],
    'L2_Class_tt1b_discriminant':[0,10],
    'L2_Class_ttH_discriminant':[0,50],
    'L2_Class_ttc_discriminant':[0,10],
    'L2_Class_tt1B_discriminant':[0,10],
    'L2_Class_ttH_discriminant':[0,50],
    'L2_Class_ttlight_discriminant':[0,10],
    'L2_Reco_higgs_pt*0.001':[0,500],
    
    # Some lower-level features
    
    'jet_pt[jet_index_PCBT_ordered[0]]*0.001':[40,300],
    'jet_pt[jet_index_PCBT_ordered[1]]*0.001':[40,300],
    'jet_pt[jet_index_PCBT_ordered[2]]*0.001':[40,300],
    'jet_pt[jet_index_PCBT_ordered[3]]*0.001':[40,300],
    
    }

    # dictionary for network nodes
    node_dict = {
    'tt2b': 'L2_Class_tt2b_discriminant',
    'tt1b': 'L2_Class_tt1b_discriminant',
    'ttH': 'L2_Class_ttH_discriminant',
    'ttc': 'L2_Class_ttc_discriminant',
    'ttB': 'L2_Class_tt1B_discriminant',
    'ttlight' : 'L2_Class_ttlight_discriminant',     
    'ratio' : 'L2_Class_ttH_discriminant/L2_Class_tt2b_discriminant',
    'ratio2': 'L2_Class_tt2b_discriminant/L2_Class_ttc_discriminant',
    'ratio3': 'L2_Class_ttH_discriminant/L2_Class_ttc_discriminant',
    }
    
    # Now let's finally loop over variables and nodes to create the plots
    for var, var_range in var_dict.items():
        for node_label, node in node_dict.items():
            plot_norm_histograms(var, var_range, node, node_label, chain_dict, sel_dict, weight_dict)
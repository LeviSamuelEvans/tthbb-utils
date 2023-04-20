import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from atlasify import atlasify

# order in .tex is ttb,tB,2b,c,light

# --------------------------------------------------------------------------------------

#====================#
# tt+light Component #
#====================#

tt_light_data = {'norm tt-XS': -8.6,
                 'norm ttlight-PS-QUAD': -1.2,
                 'norm ttlight-FSR-QUAD': -1.7,
                 'norm ATLAS-FTAG-L0': 1.4,
                 'norm ATLAS-JES-Modelling-1': -1.1,
                 'norm ATLAS-JES-PU-Rho': -1.6}


tt_1b_data = {'norm tt-XS': -8.6,
              'norm ttlight-PS-QUAD': -1.8,
              'norm ttlight-FSR-QUAD': -2.1,
              'norm ATLAS-FTAG-L0': 3.8,
              'norm ATLAS-JER-EffectiveNP-2': 1.6,
              'norm ATLAS-JER-EffectiveNP-3': 1.2,
              'norm ATLAS-JES-Modelling-1': -1.7,
              'norm ATLAS-JES-PU-Rho': -2.2}


tt_2b_data = {'norm tt-XS': -8.6,
              'norm ttlight-PS-QUAD': -4.6,
              'norm ttlight-scale-var': -1.2,
              'norm ttlight-FSR-QUAD': -1.4,
              'norm ATLAS-FTAG-L0': 6.5,
              'norm ATLAS-JER-EffectiveNP-2': 2.2,
              'norm ATLAS-JER-EffectiveNP-3': 1.5,
              'norm ATLAS-JES-Modelling-1': -1.6,
              'norm ATLAS-JES-PU-Rho': -2.4}

ttc_data = {'norm bTag-High-pT-extrap1-b': 1.1,
            'norm tt-XS': -8.6,
            'norm ttlight-PS-QUAD': -2.4,
            'norm ttlight-scale-var': -1.1,
            'norm ttlight-FSR-QUAD': -2.7,
            'norm ATLAS-FTAG-L0': 8.1,
            'norm ATLAS-JES-Modelling-1': -1.4,
            'norm ATLAS-JES-PU-Rho': -1.9}


ttB_data = {'norm bTag-High-pT-extrap1-b': 4,
            'norm bTag-High-pT-extrap1-c': 3.5,
            'norm bTag-High-pT-extrap1-light': 2.4,
            'norm tt-XS': -8.6,
            'norm ttlight-PS-QUAD': -2.7,
            'norm ttlight-pthard1-gen': -1.1,
            'norm ttlight-scale-var': -1.5,
            'norm ttlight-FSR-QUAD': -1.5,
            'norm ATLAS-FTAG-L0': 4.7,
            'norm ATLAS-JES-Modelling-1': -1.2,
            'norm ATLAS-JES-PU-Rho': -1.2}

#=================#
# tt+1b Component #
#=================#

tt_light_data = {'norm ttb-4FS-PH7-PS': 2.2,
                 'norm ttb-4FS-scale-var': -1.2,
                 'norm ATLAS-JES-PU-Rho': -1.2}

tt_1b_data = {'norm ttb-4FS-scale-var': -1,
              'norm ATLAS-JES-PU-Rho': -1.2}

tt_2b_data = {'norm ttb-4FS-scale-var': -2.2,
              'norm ATLAS-FTAG-L0': 1.7,
              'norm ATLAS-JES-Modelling-1': -1.4,
              'norm ATLAS-JES-PU-Rho': -1.9}

ttc_data = {'norm ttb-4FS-scale-var': -1.6,
            'norm ATLAS-JES-Modelling-1': -1,
            'norm ATLAS-JES-PU-Rho': -1.4}

ttB_data = {'norm ttb-4FS-PH7-PS': 2.1}


#==================#
# tt+≥2b Component #
#==================#

tt_light_data = {'norm ttbb-4FS-PH7-PS': 9.9,
                 'norm ttbb-4FS-FSR-QUAD': 2.1,
                 }

tt_1b_data = {'norm ttbb-4FS-PH7-PS': 3,
              'norm ttbb-4FS-FSR-QUAD': -1.7
              }

tt_2b_data = {'norm ttbb-4FS-PH7-PS': 1.2,
              'norm ATLAS-JES-PU-Rho': -1.3
              }

ttc_data = {'norm ttbb-4FS-PH7-PS': 3.8,
            'norm ttbb-4FS-FSR-QUAD': 1.1,
            }

ttB_data = {'norm ttbb-4FS-PH7-PS': 6.9,
            'norm ttbb-4FS-FSR-QUAD': 1.4,
            'norm ttbb-4FS-PP8-dip' : -2.1
            }


#==================#
# tt+B Component #
#==================#

tt_light_data = {'norm tt1B-4FS-PH7-PS': -4.5,
                 'norm tt1B-4FS-scale-var': -1.5,
                 'norm ttB-norm' : -12
                 }

tt_1b_data = {'norm tt1B-4FS-PH7-PS': -3,
              'norm tt1B-4FS-PP8-dip': -1,
              'norm tt1B-4FS-scale-var': -1.6,
              'norm ttB-norm' : -12
              }

tt_2b_data = {'norm tt1B-4FS-PP8-dip': 3.5,
              'norm tt1B-4FS-scale-var': -2.9,
              'norm ttB-norm': -12,
              'norm ATLAS-FTAG-L0' : 1.7,
              'norm ATLAS-JES-Modelling' : -1, 
              'norm ATLAS-JES-PU-Rho' : -1.4
              }

ttc_data = {'norm tt1B-4FS-PH7-PS': -2.5,
            'norm tt1B-4FS-scale-var': -2.1,
            'norm ttB-norm' : -12 
            }

ttB_data = {'norm tt1B-4FS-PH7-PS': -2.5,
            'norm tt1B-4FS-scale-var': -1,
            'norm ttB-norm' : -12
            }


#==================#
# tt+≥1c Component #
#==================#

tt_light_data = {'norm ttc-dropc-PS-QUAD': -1.2,
                 'norm ATLAS-JES-PU-Rho': -1.3,
                 }

tt_1b_data = {'norm ttc-pthard1-gen': -1.3,
              'norm ATLAS-JES-PU-Rho': -1.2,
              }

tt_2b_data = {'norm ttc-dropc-PS-QUAD': 1.1,
              'norm ttc-pthard1-gen': -1.4,
              'norm ttc-dropc-FSR-QUAD': 1.7,
              'norm ATLAS-FTAG-L0' : 2,
              'norm ATLAS-JER-EffectiveNP' : 1.1, 
              'norm ATLAS-JES-Modelling' : -1.4,
              'ATLAS-JES-PU-Rho' : -1.9
              }

ttc_data = {'norm bTag-High-pT-extrap1-b': 1.6,
            'norm bTag-High-pT-extrap1-c': 1.5,
            'norm bTag-High-pT-extrap1-light' : 1,
            'norm ttc-pthard1-gen' : -1.3,
            'norm ATLAS-FTAG-L0' : 1.3, 
            'norm ATLAS-JES-PU-Rho' : -1.4
            }

ttB_data = {'nnorm bTag-High-pT-extrap1-b': 4.9,
            'norm bTag-High-pT-extrap1-c': 4.8,
            'norm bTag-High-pT-extrap1-light' : 3.1,
            'ttc-dropc-PS-QUAD' : 1.9,
            'ttc-dropc-FSR-QUAD' : 1.3,
            'ATLAS-FTAG-C1' : 1.5 
            }

# --------------------------------------------------------------------------------------

# Convert data to Pandas dataframes
tt_light_df = pd.DataFrame(list(tt_light_data.items()), columns=['Parameter', 'Effect'])
tt_1b_df = pd.DataFrame(list(tt_1b_data.items()), columns=['Parameter', 'Effect'])
tt_2b_df = pd.DataFrame(list(tt_2b_data.items()), columns=['Parameter', 'Effect'])
ttc_df = pd.DataFrame(list(ttc_data.items()), columns=['Parameter', 'Effect'])
ttB_df = pd.DataFrame(list(ttB_data.items()), columns=['Parameter', 'Effect'])


# Set up plot
fig, ax = plt.subplots(figsize=(10, 5))
ax.set_title('Post-fit Acceptance effects: comb')
ax.tick_params(axis='both', labelsize=6)
# ax.set_xlabel('Nuisance parameter')
# ax.set_ylabel('Acceptance effect (%)')
# Add grid to the plot
ax.grid(axis='y', linestyle='--', alpha=0.7)


# Combine data into one dataframe for plotting
df = pd.concat([tt_light_df, tt_1b_df, tt_2b_df,ttc_df, ttB_df,], axis=0)
df['Region'] = ['tt+light'] * len(tt_light_df) + ['tt+1b'] * len(tt_1b_df) + \
               ['tt+≥2b'] * len(tt_2b_df) + ['tt+≥1c'] * len(ttc_df) + ['tt+B'] * len(ttB_df)

# Set color for each region
colors = {
          'tt+1b': (0,0,255),
          'tt+≥2b': (0, 128, 255),
          'tt+B': (0,0,204),
          'tt+≥1c': (153,51,255),
          'tt+light': (51,255,51),
          }

# Convert RGB tuple to hex code
colors = {key: '#{:02x}{:02x}{:02x}'.format(*value) for key, value in colors.items()}

# Create bar plot using Seaborn
sns.barplot(x='Parameter', y='Effect', hue='Region', data=df, ax=ax, palette=colors, linewidth=15, saturation=1.0, width=0.85)

# Rotate x-axis labels
plt.xticks(rotation=45, ha='right')

ax.axhline(y=0, color='black', linewidth=0.5)

# Add legend outside the plot
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

# Adjust plot margins
plt.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.9, wspace=0.2, hspace=0.2)

# Set y-axis tick frequency
ax.yaxis.set_major_locator(ticker.MultipleLocator(1.0))
ax.set_xlabel('Nuisance parameter')
ax.set_ylabel('Acceptance effect (%)')
atlasify('Internal', '$\sqrt{s}$ = 13 TeV, 140fb$^{-1}$')
plt.savefig('PFA_ttcomb.pdf', bbox_inches='tight')
plt.savefig('PFA_ttcomb.png', bbox_inches='tight')
# Show plot
#plt.show()
import yaml

"""
A very workflow specifc helper script to update the systematic renormalisation
values.

TODO: implement function for updating calculation Lines with updated_values
      for less code repition
      fix mapping for correlated systematics
      print out in yamnl file format for easy copying over
"""

# Function to read the replacements.yaml file
def read_replacements(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

# Function to read the norm.txt file
def read_norm(file_path):
    norm_data = {}
    current_param = None
    with open(file_path, 'r') as f:
        for line in f:
            if "parameter:" in line:
                param = line.split(":")[1].strip()
                norm_data[param] = {}
            elif "nominal:" in line:
                parts = line.split(",")
                norm_data[param]['nominal'] = float(parts[0].split(":")[1].strip())
                norm_data[param]['up'] = float(parts[1].split(":")[1].split("(")[0].strip())
                norm_data[param]['down'] = float(parts[2].split(":")[1].split("(")[0].strip())
                #print(f"Current norm_data: {norm_data}")  # Debug print
    return norm_data


# Function to update normalization values
def update_normalization(norm_data, replacements):
    updated_values = {}

    # Manual mapping between names in norm.txt and replacements.yaml
    mapping = {
        # ttc {7}
        'ttc_scale_var_muR': 'XXX_ttc_scale_muR',
        'ttc_scale_var_muF': 'XXX_ttc_scale_muF',
        'ttc_Rad':'XXX_ttc_ISR',
        'ttc_FSR': 'XXX_ttc_FSR',
        'ttc_PS': 'XXX_ttc_PH7',
        'ttc_hdamp': 'XXX_ttc_hdamp',
        'ttc_gen_pthard1':'XXX_ttc_PP8_pThard1',
        # tt1b {9}
        #'ttgeq1b_scale_var_muR':'XXX_ttb_scale_1b_muR',
        #'ttgeq1b_scale_var_muF':'XXX_ttb_scale_1b_muF',
        'ttb_Rad':'XXX_ttb_ISR_1b',
        'ttb_FSR':'XXX_ttb_FSR_1b',
        'ttb_PS_PH7':'XXX_ttb_PH7_1b',
        'ttb_dipole_PS':'XXX_ttb_dip_1b',
        'ttb_gen_pthard1':'XXX_ttb_PP8_pThard1_1b',
        # tt1B {7}
        'ttgeq1b_scale_var_muR':'XXX_ttb_scale_1B_muR',
        'ttgeq1b_scale_var_muF':'XXX_ttb_scale_1B_muF',
        'tt1B_Rad':'XXX_ttb_ISR_1B',
        'tt1B_FSR':'XXX_ttb_FSR_1B',
        'tt1B_PS_PH7':'XXX_ttb_PH7_1B',
        'tt1B_dipole_PS':'XXX_ttb_dip_1B',
        'tt1B_gen_pthard1':'XXX_ttb_PP8_pThard1_1B',
        # tt2b {7}
        #'ttgeq1b_scale_var_muR':'XXX_ttb_scale_2b_muR',
        #'ttgeq1b_scale_var_muF':'XXX_ttb_scale_2b_muF',
        'ttbb_Rad':'XXX_ttb_ISR_2b',
        'ttbb_FSR':'XXX_ttb_FSR_2b',
        'ttbb_PS_PH7':'XXX_ttb_PH7_2b',
        'ttbb_dipole_PS':'XXX_ttb_dip_2b',
        'ttbb_gen_pthard1':'XXX_ttb_PP8_pThard1_2b',
        # ttlight {7}
        'ttlight_scale_var_muR':'XXX_ttlight_scale_muR',
        'ttlight_scale_var_muF':'XXX_ttlight_scale_muF',
        'ttlight_ISR_PS':'XXX_ttlight_ISR',
        'ttlight_FSR':'XXX_ttlight_FSR',
        'ttlight_PS':'XXX_ttlight_PH7',
        'ttlight_hdamp':'XXX_ttlight_hdamp',
        'ttlight_gen_pthard1':'XXX_ttlight_pThard1',
        # special cases
        #'ttgeq1b_scale_var_muR': ('XXX_ttB_scale_var_muR', 'XXX_tt_1b_scale_var_muR', 'XXX_tt_2b_scale_var_muR'),
        #'ttgeq1b_scale_var_muR': ('XXX_ttB_scale_var_muR', 'XXX_tt_1b_scale_var_muR', 'XXX_tt_2b_scale_var_muR'),
    }

    for param, data in norm_data.items():
        key_prefix = mapping.get(param, None)

        #print(f"Trying to match {key_prefix}")  # DEBUG
        if 'up' in data and 'down' in data:
            #print(f"Found 'up' and 'down' for {param}") #DEBUG
            # Calculate new normalization values using the formula: (nominal / (variation / XXX_value))
            if key_prefix + "_up" in replacements:
                updated_values[key_prefix + "_up"] = data['nominal'] / ((data['up'] / replacements[key_prefix + "_up"]))
            elif key_prefix in replacements:  # Fallback if _up is not in replacements (not needed for down)
                updated_values[key_prefix] = data['nominal'] / ((data['up'] / replacements[key_prefix]))
            else:
                print(f"Could not find {key_prefix}_up or {key_prefix} in replacements")  # Debug print

            if key_prefix + "_down" in replacements:
                updated_values[key_prefix + "_down"] = data['nominal'] / ((data['down'] / replacements[key_prefix + "_down"]))
            elif key_prefix in replacements:  # Fallback if _up is not in replacements (not needed for down)
                updated_values[key_prefix] = data['nominal'] / ((data['up'] / replacements[key_prefix])) # simple overwite the up from above (hacky)
            else:
                print(f"Could not find {key_prefix}_down or {key_prefix} in replacements")  # Debug print

    return updated_values


# Main function
if __name__ == "__main__":
    # Read the replacements.yaml file
    replacements = read_replacements("replacements.yaml")

    # Read the norm.txt file
    norm_data = read_norm("1l_Normalisations_29_08_23.txt")

    # Update the normalization values
    updated_values = update_normalization(norm_data, replacements)

    # Output the updated values
    print()
    print("=============================")
    print("Updated Normalization Values:")
    print("=============================")
    print()
    # Find the maximum length of the keys
    max_key_length = max(len(key) for key in updated_values.keys())
    for key, value in updated_values.items():
        print(f"{key:{max_key_length}}  {value}")
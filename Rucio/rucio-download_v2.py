## IN PROGRESS ##
# requires json file with dsid map

import argparse
import json
import os
from rucio.client import Client

def get_folder_from_dsid(dsid, dsid_map):
    """Given a dsid, return the appropriate folder name based on the dsid_map."""
    for folder, dsids in dsid_map.items():
        if dsid in dsids:
            return folder
    return None  # If dsid is not found in the map for some reason

def download_samples(sample_list, rse, login_info=None, nominal_only=False, dsid_map=None):
    # Initialize the Rucio client
    client = Client(rucio_account=login_info.get('account', 'default_account'), auth_host=login_info.get('auth_host', 'default_auth_host'))

    with open(sample_list, 'r') as f:
        for sample in f:
            sample = sample.strip()
            if not sample:
                continue

            # Determine folder based on the DSID
            dsid = sample.split('.')[1]  # Assuming the DSID is the second part of the sample name...
            folder = get_folder_from_dsid(dsid, dsid_map)
            if not folder:
                print(f"Warning: No folder found for DSID {dsid}. Skipping...")
                continue

            destination = os.path.join(folder, sample)

            # Skip non-nominal samples if nominal_only is set to true
            if nominal_only and not sample.endswith('nominal'):
                continue

            # Now trigger the download
            client.download_dids([{'did': sample, 'rse': rse, 'base_dir': destination}])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Download level 1 samples via Rucio.")

    parser.add_argument('-f', '--file', required=True, help="Text file with a list of samples to download.")
    parser.add_argument('-r', '--rse', required=True, help="Specify the RSE (Replica SErvice).")
    parser.add_argument('-a', '--account', default='default_account', help="Rucio account name. Default is 'default_account'.")
    parser.add_argument('--auth_host', default='default_auth_host', help="Rucio authentication host. Default is 'default_auth_host'.")
    parser.add_argument('--nominal_only', action='store_true', help="Download only the nominal samples. If not specified, all samples are downloaded.")

    args = parser.parse_args()

    login_info = {
        'account': args.account,
        'auth_host': args.auth_host
    }

    # Load the json DSID map
    with open('dsid_map.json', 'r') as f:
        dsid_map = json.load(f)

    download_samples(args.file, args.rse, login_info, args.nominal_only, dsid_map)
import subprocess
from tqdm import tqdm

# Small script for downloading L1 samples
# -- specify container names in a .txt file

def download_containers(container_list_file):

    with open(container_list_file, 'r') as file:
        container_names = file.read().splitlines()

    # The rucio download command
    command = ['rucio', 'download'] + container_names + ['--dir', '.', '--rse', 'UKI-LT2-QMUL_LOCALGROUPDISK']

    # Get the number of containers specifed in the text file
    total_containers = len(container_names)

    # Produce logs of the download
    log_file = open('rucio_download.log', 'w')
    progress_bar = tqdm(total=total_containers, desc='Downloading', unit='containers', ncols=80)


    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for line in process.stdout:

        if line.startswith('['):
            progress_bar.update(1)
        log_file.write(line)
        print(line, end='')


    process.wait()
    progress_bar.close()
    log_file.close()

    print(f"\nDownload complete. Log file created: rucio_download.log")

# Specify the path to the file containing container names
container_list_file = 'containers.txt'

download_containers(container_list_file)

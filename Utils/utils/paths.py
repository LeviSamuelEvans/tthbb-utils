import os

# Small script to write .txt files of paths and file names inside containers for L2 Production

# Container Names
directories = [
    'user.alheld.mc16_13TeV.601227.PhPy8_ttbb_4FS_bzd5_ljets.TOPQ1.e8388s3126r9364p5003.TTHbb212238-v1_1l_sys_out_root',
    'user.alheld.mc16_13TeV.601227.PhPy8_ttbb_4FS_bzd5_ljets.TOPQ1.e8388s3126r10201p5003.TTHbb212238-v1_1l_sys_out_root',
    'user.alheld.mc16_13TeV.601227.PhPy8_ttbb_4FS_bzd5_ljets.TOPQ1.e8388s3126r10724p5003.TTHbb212238-v1_1l_sys_out_root'
]


for directory in directories:
    # Create a text file based on the container name
    file_name = directory.replace('.', '_') + '.txt'

    # Get the absolute path of the directory
    abs_directory = os.path.abspath(directory)

    # Create the output file path by joining the directory path and the file name
    output_file = os.path.join(abs_directory, file_name)

    # Open the output file
    with open(output_file, 'w') as file:
        # Iterate
        for root, dirs, files in os.walk(abs_directory):
            # Iterate
            for file_name in files:
                abs_file_path = os.path.join(root, file_name)


                file.write(abs_file_path + '\n')

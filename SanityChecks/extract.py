import re

# Open the text file
with open('1l_5j3b_ttb.txt', 'r') as file:
    # Read the contents of the file
    file_contents = file.read()

# Use regular expression to extract file names
file_names = re.findall(r'\w+\.root', file_contents)

# Print the file names
for file_name in file_names:
    print(file_name)

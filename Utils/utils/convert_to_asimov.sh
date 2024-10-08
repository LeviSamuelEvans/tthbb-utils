#!/bin/bash

# This code coverts BONLY configs to ASIMOV configs. It will change the fit type to Asimov, remove the signal regions,
# and covert the Full_ regions from VALIDATION to SIGNAL. It will also change the directory output location to a new 
# asimov folder that is created.

# To use simply do ./convert_to_asimov config.yaml

# Check if the input file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

input_file="$1"
output_file="${input_file/bonly/asi}"
output_file="${output_file/BONLY/ASI}"

# Initialize the flags as false
remove_hash=false
add_hash=false
found_bkg=false
found_asimov=false
comment_signal=false
found_region=false

temp_file=$(mktemp)

# Removes hashes from Asimov fit block and hashes out Bkg-only fit block
while IFS= read -r line; do
    if [[ $line == "#Asimov"* ]]; then
        found_asimov=true
    elif [[ $line == "# Bkg-only"* ]]; then
        found_bkg=true
    elif [[ -z $line ]]; then
        if $found_asimov; then
            remove_hash=false
            found_asimov=false
        fi
        if $found_bkg; then
            add_hash=false
            found_bkg=false
        fi
    elif $found_asimov; then
        remove_hash=true
    elif $found_bkg; then
        add_hash=true
    fi

    if $add_hash && [[ -n $line ]]; then
        line="#$line"
    elif $remove_hash; then
        line="${line/#\#/}"
    fi

    echo "$line" >> "$temp_file"
done < "$input_file"

temp_file2=$(mktemp)

# Hashes out SIGNAL regions 
buffer=""
while IFS= read -r line; do
    if [[ -z $line ]]; then
        if $comment_signal && $found_region; then
            buffer="#${buffer//$'\n'/$'\n#'}"
        fi
        echo -e "$buffer" >> "$temp_file2"
        buffer=""
        comment_signal=false
        found_region=false
    else
        buffer+="$line"$'\n'
    fi

    if [[ $line == *"Type: SIGNAL"* ]]; then
        comment_signal=true
    fi

    if [[ $line == *"Region"* ]]; then
        found_region=true
    fi
done < "$temp_file"

# Save remaining lines in buffer
if [[ -n $buffer ]]; then
    if $comment_signal && $found_region; then
        buffer="#${buffer//$'\n'/$'\n#'}"
    fi
    echo -e "$buffer" >> "$temp_file2"
fi

# Converts VALIDATION regions to SIGNAL 
temp_file3=$(mktemp)
sed 's/VALIDATION/SIGNAL/g' "$temp_file2" > "$temp_file3"

# Amends the output file name by replacing the 'bonly' flag with 'asi'
sed 's/\(OutputDir.*\)bonly/\1asi/; s/BONLY/asi/' "$temp_file3" > "$output_file"

output_dir=$(grep "OutputDir" "$output_file" | awk '{print $2}' | tr -d '"')
mkdir -p "$output_dir"

rm "$temp_file" "$temp_file2" "$temp_file3"
echo "Modified file saved as $output_file"

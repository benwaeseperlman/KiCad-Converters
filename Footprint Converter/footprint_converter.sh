#!/bin/sh
echo "Parameters: Directory of files you want to convert, Path to python script"
script_path=$(readlink -f "$2")
cd "$1"
mkdir -p output
find . -type f -name "*.fpl" | while read file
do
    filename="${file%.*}"
    echo $filename
    mkdir -p "output/$filename.pretty"
    python3 "$script_path" "output/$filename.pretty" "$file" --add-courtyard 1
done
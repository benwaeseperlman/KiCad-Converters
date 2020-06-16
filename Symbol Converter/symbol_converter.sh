#!/bin/sh
echo "Parameters: Directory of files you want to convert, Path to python script"
python3 -c "import nltk; nltk.download('punkt')"
script_path=$(readlink -f "$2")
cd "$1"
echo "$script_path"
mkdir -p output
find . -type d | while read folder
do
    python3 "$script_path" "$folder" "$1"
done
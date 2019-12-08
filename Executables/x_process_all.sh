#!/bin/bash

# Process all .exe/.EXE files within current folder
readarray -t files < <(find . -type f -iname '*.exe' | sort)
for file in "${files[@]}"; do
	./x_process_exe.sh "${file}"
done

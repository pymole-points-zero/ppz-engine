#!/bin/bash

# create named pipe for python script if it's does not exists
pipe=/tmp/ppz-paip6-pipe

trap "rm -f $pipe" EXIT
if [[ ! -p $pipe ]]; then
    mkfifo $pipe
fi

# start python script
current_dir=$(dirname $0)
$current_dir/venv/bin/python3.8 $current_dir/main.py pointsaiprotocol --weights 123 --parameters [] --pipe $pipe &


# write to named pipe
while IFS='$\n' read -r line; do
    echo $line > $pipe
done
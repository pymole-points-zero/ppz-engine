#!/bin/bash

# create named pipe for python script if it does not exists
mkdir -p /tmp/paip/
r=$RANDOM
input_pipe="/tmp/paip/input${r}"
output_pipe="/tmp/paip/output${r}"


trap "rm -f $input_pipe" EXIT
if [[ ! -p $input_pipe ]]; then
    mkfifo $input_pipe
fi

trap "rm -f $output_pipe" EXIT
if [[ ! -p $output_pipe ]]; then
    mkfifo $output_pipe
fi

# start python script
current_dir=$(dirname $0)
$current_dir/venv/bin/python3.8 $current_dir/main.py paip --field_width 10 --field_height 10 --simulations 80 --weights $current_dir/model.h5 --input_pipe $input_pipe --output_pipe $output_pipe &

python_pid=$!


function finish() {
  kill -9 $python_pid
  exit
}

trap finish SIGINT


exec 3>$input_pipe
exec 4<$output_pipe
{ cat; } <&4 >&1 &
{ cat; } <&0 >&3 &
wait

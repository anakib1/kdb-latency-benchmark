#!/bin/bash

cd q-src

if ! tmux has-session -t tick 2>/dev/null; then
    echo "Creating tickerplant."
    tmux new-session -d -s tick
    tmux send-keys -t tick "q tick.q trades -t 0" C-m
    sleep 1
fi

tmux set-environment -g DURATION "$DURATION"
tmux set-environment -g THROUGHPUT "$THROUGHPUT"

tmux new-session -d -s log
tmux new-session -d -s sub
tmux new-session -d -s pub

tmux send-keys -t log  "q logger.q -p 5001; tmux wait-for -S done" C-m
sleep 1
tmux send-keys -t sub  "q sub.q" C-m
sleep 1
tmux send-keys -t pub  "q pub.q" C-m
sleep 1

echo "Experiment started!"
echo "Duration: $DURATION"
echo "Throughput: $THROUGHPUT"

tmux wait-for done

tmux kill-session -t sub
tmux kill-session -t pub
tmux kill-session -t log

echo "Experiment done! Results (throughput,50%,90%,99%,99.9%,99.99%):"
tail -n 1 ../results/results.txt

echo "Drawing.."
cd ../py-src
source venv/bin/activate
python draw.py
echo "Done"

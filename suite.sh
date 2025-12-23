#!/bin/bash

export DURATION=300
export THROUGHPUT=10000
./run.sh
export THROUGHPUT=20000
./run.sh
export THROUGHPUT=40000
./run.sh
export THROUGHPUT=60000
./run.sh
export THROUGHPUT=80000
./run.sh
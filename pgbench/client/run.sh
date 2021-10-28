#!/bin/bash

set -e

PGBENCH_SERVER_HOST="${PGBENCH_SERVER_HOST:-localhost}"
PGBENCH_SERVER_PORT="${PGBENCH_SERVER_PORT:-5432}"

BENCHDOG_DURATION="${BENCHDOG_DURATION:-10}"
BENCHDOG_ITERATIONS="${BENCHDOG_ITERATIONS:-3}"

common_args="--host $PGBENCH_SERVER_HOST --port $PGBENCH_SERVER_PORT --time $BENCHDOG_DURATION --progress 2 --select-only --log"

echo "# Running pgbench against host $PGBENCH_SERVER_HOST on $(date)"
echo

export PGUSER=postgres
export PGPASSWORD=postgres

function run {
    local clients=$1

    for ((i=1; i <= BENCHDOG_ITERATIONS; i++)); do
        sleep 10
        echo "# Run: clients: $clients, iteration $i"
        echo
        pgbench --jobs $clients --client $clients $common_args
        echo
        cat pgbench_log.* > pgbench_log
        python3 process.py pgbench_log >> results-$clients.txt
        rm pgbench_log*
    done
}

run 1
run 10
run 100

echo "# Processed results"
echo

cat results-1.txt
echo

cat results-10.txt
echo

cat results-100.txt
echo

# echo "## Median results"

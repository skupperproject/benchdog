#!/bin/bash

if [[ -z $PGBENCH_SERVER_HOST ]]; then
    PGBENCH_SERVER_HOST=localhost
fi

common_args="--host $PGBENCH_SERVER_HOST --time 30 --username test --progress 2 --select-only"

echo "# Running pgbench against host $PGBENCH_SERVER_HOST on $(date)"
echo

echo "## 1 client"
echo

for i in {1..3}; do
    echo "### Run $i"
    echo
    pgbench --jobs 1 --client 1 $common_args
    echo
    sleep 10
done

echo "## 10 clients"
echo

for i in {1..3}; do
    echo "### Run $i"
    echo
    pgbench --jobs 10 --client 10 $common_args
    echo
    sleep 10
done

echo "## 100 clients"
echo

for i in {1..3}; do
    echo "### Run $i"
    echo
    pgbench --jobs 100 --client 100 $common_args
    echo
    sleep 10
done

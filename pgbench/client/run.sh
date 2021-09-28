#!/bin/bash

if [[ -z $DATABASE_SERVER ]]; then
    DATABASE_SERVER=localhost
fi

echo "### 1 client ###"
echo

for i in {1..3}; do
    pgbench --jobs 1 --client 1 --time 30 --host $DATABASE_SERVER --username test --progress 2 --select-only
    echo
    sleep 10
done

echo "### 10 clients ###"
echo

for i in {1..3}; do
    pgbench --jobs 10 --client 10 --time 30 --host $DATABASE_SERVER --username test --progress 2 --select-only
    echo
    sleep 10
done

echo "### 100 clients ###"
echo

for i in {1..3}; do
    pgbench --jobs 100 --client 100 --time 30 --host $DATABASE_SERVER --username test --progress 2 --select-only
    echo
    sleep 10
done

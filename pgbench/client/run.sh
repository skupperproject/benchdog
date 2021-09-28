#!/bin/bash

if [[ -z $DATABASE_SERVER ]]; then
    DATABASE_SERVER=localhost
fi

pgbench --jobs 10 --client 10 --time 30 --host $DATABASE_SERVER --username test --progress 2

#!/bin/bash

if [ "$#" != 1 -a "$#" != 3 ]
then
    echo "Usage: setup-skupper.sh ROUTER-CPU [DEPLOYMENT-NAME PORT]"
    exit 1
fi

set -Ceuvx

skupper delete || :
sleep 1
skupper init --router-cpu "$1"

if [ -n "${2:-}" -a -n "${3:-}" ]
then
    # The server site

    skupper token create ~/a.token
    skupper expose deployment/"$2" --port "$3"
else
    # The client site
    skupper link create ~/a.token
    kubectl get service -w
fi

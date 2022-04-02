# Benchdog: wrk

An HTTP/1.1 benchmark test

## Running the server in Kubernetes

Server namespace:

    kubectl apply -f server/

## Running the client in Kubernetes

Client namespace:

    kubectl run -it --rm --env BENCHDOG_HOST=<host> --image quay.io/ssorj/benchdog-wrk-client wrk-client

## Connecting across sites using Skupper

Server namespace:

    skupper init
    skupper token create ~/token.yaml
    skupper expose deployment/wrk-server --port 8080

Client namespace:

    skupper init
    skupper link create ~/token.yaml

Once the `wrk-server` service appears in the client namespace, you can
run the client using that value for `BENCHDOG_HOST`.

For more information, see [Getting started with
Skupper](https://skupper.io/start/index.html).

## Configuring Skupper router resource limits

    skupper init --routers 2 --router-cpu-limit 0.5

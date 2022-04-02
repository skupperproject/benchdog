# pgbench

A PostgreSQL benchmark test

## Running the server in Kubernetes

Server namespace:

    kubectl apply -f server/

#### Running the server in OpenShift

The standard PostgreSQL container image requires running as the root
user inside the container, which OpenShift prohibits by default.  This
command removes the OpenShift prohibition:

    oc adm policy add-scc-to-group anyuid system:authenticated

## Running the client in Kubernetes

Client namespace:

    kubectl run -it --rm --env BENCHDOG_HOST=<host> --image quay.io/ssorj/benchdog-pgbench-client pgbench-client

## Connecting across sites using Skupper

Server namespace:

    skupper init
    skupper token create ~/token.yaml
    skupper expose deployment/pgbench-server --port 8080

Client namespace:

    skupper init
    skupper link create ~/token.yaml

Once the `pgbench-server` service appears in the client namespace, you can
run the client using that value for `BENCHDOG_HOST`.

For more information, see [Getting started with
Skupper](https://skupper.io/start/index.html).

## Configuring Skupper router resource limits

    skupper init --routers 2 --router-cpu-limit 0.5

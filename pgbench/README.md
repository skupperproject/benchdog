# Benchdog: pgbench

A containerized PostgreSQL benchmark tool based on [pgbench][pgbench].

[pgbench]: https://www.postgresql.org/docs/current/pgbench.html

## Running the server in Kubernetes

Server namespace:

    kubectl create namespace benchdog-server
    kubectl config set-context --current --namespace benchdog-server
    kubectl apply -f server/

#### Running root containers in OpenShift

The standard PostgreSQL container image requires running as the root
user inside the container, which OpenShift prohibits by default.  This
command removes the OpenShift prohibition:

    oc adm policy add-scc-to-group anyuid system:authenticated

Note that you need this permission for the server and client images,
since they use both use the standardard PostgreSQL container as a
base.

## Running the client in Kubernetes

Client namespace:

    kubectl create namespace benchdog-client
    kubectl config set-context --current --namespace benchdog-client
    kubectl run -it --rm --env BENCHDOG_HOST=<host> --image quay.io/ssorj/benchdog-pgbench-client pgbench-client

## Testing with Skupper

Server namespace:

    kubectl config set-context --current --namespace benchdog-server
    skupper init
    skupper token create ~/token.yaml
    skupper expose deployment/pgbench-server --port 5432

Client namespace:

    kubectl config set-context --current --namespace benchdog-client
    skupper init
    skupper link create ~/token.yaml

Once the `pgbench-server` service appears in the client namespace, you
can run the client with `--env BENCHDOG_HOST=pgbench-server`.

Client namespace:

    kubectl run -it --rm --env BENCHDOG_HOST=pgbench-server --image quay.io/ssorj/benchdog-pgbench-client pgbench-client

# Benchdog: qbench

A containerized messaging benchmark based on [qbench][qbench].

[qbench]: https://github.com/ssorj/qbench

## Running the server in Kubernetes

Server namespace:

    kubectl create namespace benchdog-server
    kubectl config set-context --current --namespace benchdog-server
    kubectl apply -f server/
    kubectl expose deployment/qbench-server --port 55672 --type LoadBalancer

## Running the client in Kubernetes

Client namespace:

    kubectl create namespace benchdog-client
    kubectl config set-context --current --namespace benchdog-client
    kubectl run -it --rm --env BENCHDOG_HOST=<host> --image quay.io/ssorj/benchdog-qbench-client qbench-client

## Testing with Skupper

Server namespace:

    kubectl config set-context --current --namespace benchdog-server
    skupper init
    skupper token create ~/token.yaml
    skupper expose deployment/qbench-server --port 55672

Client namespace:

    kubectl config set-context --current --namespace benchdog-client
    skupper init
    skupper link create ~/token.yaml

Once the `qbench-server` service appears in the client namespace, you
can run the client with `--env BENCHDOG_HOST=qbench-server`.

Client namespace:

    kubectl run -it --rm --env BENCHDOG_HOST=qbench-server --image quay.io/ssorj/benchdog-qbench-client qbench-client

## Example commands

    kubectl run -it --rm --env BENCHDOG_HOST=qbench-server --env BENCHDOG_SCENARIOS=100:100,100:200,100:300,100:400,100:500 --env BENCHDOG_ITERATIONS=3 --env BENCHDOG_DURATION=60 --image quay.io/ssorj/benchdog-qbench-client qbench-client

    kubectl run -it --rm --env BENCHDOG_HOST=qbench-server --env BENCHDOG_SCENARIOS=100:100,500:100 --env BENCHDOG_ITERATIONS=3 --env BENCHDOG_DURATION=60 --image quay.io/ssorj/benchdog-qbench-client qbench-client

    kubectl run -it --rm --env BENCHDOG_HOST=qbench-server --env BENCHDOG_SCENARIOS=100:100 --env BENCHDOG_ITERATIONS=7 --env BENCHDOG_DURATION=60 --image quay.io/ssorj/benchdog-qbench-client qbench-client

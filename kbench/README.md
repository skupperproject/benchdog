# Benchdog: kbench

A containerized Kafka benchmark tool using the [Kafka Java
client][client] and [Strimzi][strimzi].

[client]: https://kafka.apache.org/documentation/#api
[strimzi]: https://strimzi.io/

## Running the server in Kubernetes

Server namespace:

    kubectl create namespace benchdog-server
    kubectl config set-context --current --namespace benchdog-server
    kubectl create -f server/strimzi.yaml
    kubectl create -f server/cluster.yaml
    kubectl wait --for condition=ready --timeout 900s kafka/kbench

## Running the client in Kubernetes

Client namespace:

    kubectl create namespace benchdog-client
    kubectl config set-context --current --namespace benchdog-client
    kubectl run kbench-client --attach --rm --restart Never --image quay.io/ssorj/benchdog-kbench-client \
        --env BENCHDOG_HOST=kbench-kafka-brokers.benchdog-server

## Testing with Skupper

Server namespace:

    kubectl config set-context --current --namespace benchdog-server
    skupper init
    skupper token create ~/token.yaml
    skupper expose statefulset/kbench-kafka --headless --port 9092

Client namespace:

    kubectl config set-context --current --namespace benchdog-client
    skupper init
    skupper link create ~/token.yaml

Once the `kbench-kafka-brokers` service appears in the client
namespace, you can run the client with `--env
BENCHDOG_HOST=kbench-kafka-brokers`.

Client namespace:

    kubectl run kbench-client --attach --rm --restart Never --image quay.io/ssorj/benchdog-kbench-client \
        --env BENCHDOG_HOST=kbench-kafka-brokers

## Cleaning up

    kubectl delete -f server/strimzi.yaml

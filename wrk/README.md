# Benchdog: wrk

A containerized HTTP/1.1 benchmark based on [wrk][wrk] and
[nginx][nginx].

[wrk]: https://github.com/wg/wrk
[nginx]: https://nginx.org/

## Running the server in Kubernetes

Server namespace:

    kubectl create namespace benchdog-server
    kubectl config set-context --current --namespace benchdog-server
    kubectl apply -f server/
    kubectl expose deployment/wrk-server --port 58080 --type LoadBalancer

## Running the client in Kubernetes

Client namespace:

    kubectl create namespace benchdog-client
    kubectl config set-context --current --namespace benchdog-client
    kubectl run -it --rm --env BENCHDOG_HOST=<host> --image quay.io/ssorj/benchdog-wrk-client wrk-client

## Testing with Skupper

Server namespace:

    kubectl config set-context --current --namespace benchdog-server
    skupper init
    skupper token create ~/token.yaml
    skupper expose deployment/wrk-server --port 58080

Client namespace:

    kubectl config set-context --current --namespace benchdog-client
    skupper init
    skupper link create ~/token.yaml

Once the `wrk-server` service appears in the client namespace, you can
run the client with `--env BENCHDOG_HOST=wrk-server`.

Client namespace:

    kubectl run -it --rm --env BENCHDOG_HOST=wrk-server --image quay.io/ssorj/benchdog-wrk-client wrk-client

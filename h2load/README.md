# Benchdog: h2load

A containerized AMQP messaging benchmark based on [h2load][h2load].

[h2load]: https://nghttp2.org/documentation/h2load.1.html

## Running the server in Kubernetes

Server namespace:

    kubectl create namespace benchdog-server
    kubectl config set-context --current --namespace benchdog-server
    kubectl apply -f server/

## Running the client in Kubernetes

Client namespace:

    kubectl create namespace benchdog-client
    kubectl config set-context --current --namespace benchdog-client
    kubectl run -it --rm --env BENCHDOG_HOST=<host> --image quay.io/ssorj/benchdog-h2load-client h2load-client

## Testing with Skupper

Server namespace:

    kubectl config set-context --current --namespace benchdog-server
    skupper init
    skupper token create ~/token.yaml
    skupper expose deployment/h2load-server --port 58080

Client namespace:

    kubectl config set-context --current --namespace benchdog-client
    skupper init
    skupper link create ~/token.yaml

Once the `h2load-server` service appears in the client namespace, you
can run the client with `--env BENCHDOG_HOST=h2load-server`.

Client namespace:

    kubectl run -it --rm --env BENCHDOG_HOST=h2load-server --image quay.io/ssorj/benchdog-h2load-client h2load-client
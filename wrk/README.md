# Wrk

## Setup

Server namespace:

    skupper init
    # skupper init --routers 2 --router-cpu-limit 0.5
    skupper token create ~/token.yaml
    kubectl apply -f server/
    skupper expose deployment/wrk-server --port 8080

Client namespace:

    skupper init
    # skupper init --routers 2 --router-cpu-limit 0.5
    skupper link create ~/token.yaml

## Run

Client namespace:

    kubectl run -it --rm --env BENCHDOG_HOST=wrk-server --env BENCHDOG_PORT=8080 --env BENCHDOG_DURATION=60 --env BENCHDOG_ITERATIONS=3 --image quay.io/ssorj/benchdog-wrk-client wrk-client

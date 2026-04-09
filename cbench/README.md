# Benchdog : cbench

A containerized test measuring Skupper connection rate.

The Cbench client repeatedly makes and then closes connections with the server. After making each connection, it waits to receive a small message back from the server. The duration that the client records is the time between its request for a connection, and its receipt of the message from the server. 

This is a slight over estimate of the connection time, but this is the only way we can know that the connection has gone all the way through the router network to the target server.

Each test lasts 15 seconds. At the end of each test, the client prints out statistics for that test.


## Testing with Skupper

### Server namespace:

```
    kubectl create namespace cbench-server
    kubectl config set-context --current --namespace cbench-server
    skupper init
    kubectl create deployment cbench-server --image quay.io/skupper/benchdog-cbench-server
    skupper expose deployment/cbench-server --port 5800
    skupper token create ~/token.yaml
```

### Client namespace:

```
    kubectl create namespace cbench-client
    kubectl config set-context --current --namespace=cbench-client
    skupper init
    skupper link create ~/token.yaml
    skupper link status      # Make sure it's connected
    kubectl get services     # Look for cbench-server
    kubectl run --env="CBENCH_HOST=cbench-server" --env="CBENCH_PORT=5800" --image quay.io/skupper/benchdog-cbench-client cbench-client
    kubectl logs cbench-client  # To see the output
```

## Controlling number of client threads

The client main program does not itself create connections to the server. Instead, it launches one or more threads, each of which repeatedly makes and closes connections as quickly as possible in a loop. Each separate test can use a different number of threads. 

The number of tests that are run, and the number of threads used in each test, is controlled by the N\_CLIENTS\_LIST environment variable. If it is not present, its value defaults to "1 2 5". You can override the default by giving it a new value in the kubectl run command like so:

```
    kubectl run --env="CBENCH_HOST=cbench-server" --env="CBENCH_PORT=5800" --env N_CLIENTS_LIST="1 2 3 4" --image quay.io/skupper/benchdog-cbench-client cbench-client
```

It will take a little over 15 seconds to run each test, so you may need to look at the logs several times to get all of your output.






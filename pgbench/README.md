## Running the server on OpenShift

    oc adm policy add-scc-to-group anyuid system:authenticated

## Running the client

    kubectl run -it --rm --env BENCHDOG_SERVER_HOST=169.63.182.185 --env BENCHDOG_SERVER_PORT=5432 --env BENCHDOG_DURATION=1 --env BENCHDOG_ITERATONS=3 --image quay.io/ssorj/benchdog-pgbench-client pgbench-client

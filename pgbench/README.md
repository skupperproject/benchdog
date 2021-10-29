## Running the server

    kubectl apply -f server/

### Running the server on OpenShift

The standard PostgreSQL container image requires running as the root
user inside the container, which OpenShift prohibits by default.  This
command removes the OpenShift prohibition:

    oc adm policy add-scc-to-group anyuid system:authenticated

## Running the client job

    kubectl run -it --rm --env BENCHDOG_SERVER_HOST=169.63.182.185 --env BENCHDOG_SERVER_PORT=5432 --env BENCHDOG_DURATION=1 --env BENCHDOG_ITERATONS=3 --image quay.io/ssorj/benchdog-pgbench-client pgbench-client

## Links

- https://www.postgresql.org/docs/current/pgbench.html

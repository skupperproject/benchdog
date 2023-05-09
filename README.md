# Benchdog

Containerized client-server benchmarking tools for comparing cloud
networking solutions.

I developed these with a focus on comparing [Skupper][skupper] to
other options for multi-site deployment, but there's nothing
Skupper-specific about them.

[skupper]: https://skupper.io/

## Overview

Each benchmark has a server container and a client container.  All
tests run with a single server instance.  The number of client jobs
varies across three scenarios: 1 job, 10 jobs, and 100 jobs.  A job
typically corresponds to a client connection.

For each scenario, we perform a certain number of iterations (default
5).  For our results, we keep only the "middlest" value, by
throughput.

Sample output:

    CLIENTS    THROUGHPUT   LATENCY AVG   LATENCY 50%   LATENCY 99%
          1        581.98          1.82          1.64          6.84
         10      4,444.76          2.40          2.05          9.02
        100     19,770.96          5.19          4.58         14.27

    Each operation is an HTTP/1.1 GET request.
    Throughput is the number of operations per second.
    Latency is the duration of an operation in milliseconds.
    High and low results from repeated runs are discarded.

## Benchmarks

- [**kbench**](kbench) - Kafka
- [**pgbench**](pgbench) - PostgreSQL
- [**wrk**](wrk) - HTTP/1.1 and Nginx

## Configuration

The benchmark client is configured using these environment variables:

- **BENCHDOG_HOST** - The host to connect to (default localhost)
- **BENCHDOG_PORT** - The port to connect to (the default is benchmark specific)
- **BENCHDOG_DURATION** - The time in seconds to run the test (default 60)
- **BENCHDOG_ITERATIONS** - The number of repeated runs for each scenario (default 5)

<!-- - **BENCHDOG_TLS** - Set to `1` to connect using TLS (TLS is off by default) -->

## Testing with Skupper

The individual benchmarks have instructions for running the client and
server on Kubernetes.

### Configuring Skupper router resource limits

Setting the CPU limit implicitly sets the requested CPU to the same
value.

    skupper init --router-cpu-limit 0.5

### Monitoring CPU and memory usage

I find these useful for confirming that my configuration has taken
effect.

    watch kubectl top pod -n benchdog-client
    watch kubectl top pod -n benchdog-server

## Resources

- https://dev.mysql.com/downloads/benchmarks.html
- https://www.postgresql.org/docs/current/pgbench.html
- https://gist.github.com/jkreps/c7ddb4041ef62a900e6c
- https://github.com/denji/awesome-http-benchmark
- https://github.com/wg/wrk

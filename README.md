# Benchdog

Containerized client-server benchmarking tools for comparing cloud
networking solutions.

I developed these with a focus on comparing [Skupper][skupper] to
other options for multi-site deployment, but there's nothing
Skupper-specific about them.

[skupper]: https://skupper.io/

## Overview

Each benchmark has a server container and a client container.  All
tests run with a single server instance.  The number of client
connections can be configured.  The default is a set with 10
connections, 100 connections, and 500 connections.

Sample output:

    ## Configuration

    Host:        localhost
    Port:        55432
    Scenarios:   10:100,100:100,500:100
    Duration:    60 seconds
    Iterations:  1

    ## Results

    CONNECTIONS          THROUGHPUT     LATENCY AVG     LATENCY P50     LATENCY P99
             10         994.0 ops/s        0.260 ms        0.230 ms        0.580 ms
            100      10,000.9 ops/s        0.200 ms        0.180 ms        0.370 ms
            500      49,938.5 ops/s        0.350 ms        0.160 ms        2.840 ms

    Each operation is a SQL select.
    Throughput is the number of operations per second.
    Latency is the duration of an operation in milliseconds.
    High and low results from repeated runs are discarded.

## Benchmarks

- [**h2load**](h2load) - HTTP/2
- [**kbench**](kbench) - Kafka
- [**pgbench**](pgbench) - PostgreSQL
- [**qbench**](qbench) - AMQP messaging
- [**wrk**](wrk) - HTTP/1.1

## Configuration

The benchmark client is configured using these environment variables:

- **BENCHDOG_HOST** - The host to connect to (default localhost)
- **BENCHDOG_PORT** - The port to connect to (the default is benchmark specific)
- **BENCHDOG_DURATION** - The time in seconds to run the test (default 60)
- **BENCHDOG_ITERATIONS** - The number of repeated runs for each
  scenario (default 1).  If this is more than 1, the high median by
  average latency is reported.
- **BENCHDOG_SCENARIOS** - A comma-separated list of
  `<connections>:<rate>` pairs, where `<connections>` is the number of
  concurrent client connections and `<rate>` is the number of
  operations per second, per connection.

## Testing with Skupper

The individual benchmarks have instructions for running the client and
server on Kubernetes.

### Configuring Skupper router resource limits

    skupper init --router-cpu 0.5

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

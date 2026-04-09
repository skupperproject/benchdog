# Benchdog

Containerized client-server benchmarking tools for comparing cloud
networking solutions.

I developed these with a focus on comparing [Skupper][skupper] to
other options for multi-site deployment, but there's nothing
Skupper-specific about them.

[skupper]: https://skupper.io/

## Overview

Each benchmark has a server container and a client container.  All
tests run with a single client and a single server.  The number of
client connections and target throughput can be configured.  The
default is a set with 10 connections, 100 connections, and 500
connections, with each connection running 100 operations per second.

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

[**h2load**](h2load) - HTTP/2

<!-- [**kbench**](kbench) - Kafka -->

[**qbench**](qbench) - Messaging

[**pgbench**](pgbench) - PostgreSQL

[**cbench**](cbench) - Connection Rate

[**wrk**](wrk) - HTTP/1.1

## Configuration

The benchmark client is configured using these environment variables:

`BENCHDOG_HOST` - The host to connect to (default `localhost`).

`BENCHDOG_PORT` - The port to connect to (the default is benchmark-specific).

`BENCHDOG_SCENARIOS` - A comma-separated list of
`<connections>:<rate>` pairs, where `<connections>` is the number of
concurrent client connections and `<rate>` is the number of operations
per second, per connection (default `10:100,100:100,500:100`).

`BENCHDOG_DURATION` - The time in seconds to run the test (default `60`).

`BENCHDOG_ITERATIONS` - The number of repeated runs for each
scenario (default `1`).  If greater than 1, Benchdog reports the high
median result selected by average latency.

## Testing with Skupper

The individual benchmarks have instructions for running the client and
server in Kubernetes and setting up Skupper.

### Configuring router CPU

    skupper init --router-cpu 0.5

### Monitoring CPU and memory usage

I find these useful for confirming that my configuration has taken
effect.

    watch kubectl top pod -n benchdog-client
    watch kubectl top pod -n benchdog-server

## Resources

- https://github.com/denji/awesome-http-benchmark
- https://github.com/giltene/wrk2

# Benchdog

Containerized client-server benchmarking tools for comparing cloud
networking solutions.

I developed these with a focus on comparing Skupper to other options
for multi-site deployment, but there's nothing Skupper-specific about
them.

## Overview

Each benchmark has a server container and a client container.  All
tests run with a single server instance.  The number of clients varies
across three scenarios: 1 client, 10 clients, and 100 clients.

For each scenario, we perform a certain number of iterations (default
3).  For our results, we keep only the "middlest" value, by
throughput.

Sample output:

    CLIENTS    THROUGHPUT   LATENCY AVG   LATENCY 50%   LATENCY 99%
          1     10,067.27        101.25         93.00        352.00
         10     70,830.91        239.37        130.00      2,591.00
        100     63,168.18      1,883.14      1,401.00     10,427.00

    Each operation is an HTTP/1.1 GET.
    Throughput is the number of operations per second.
    Latency is the duration of an operation in milliseconds.
    High and low results from repeated runs are discarded.

## Benchmarks

- **pgbench** - PostgreSQL
- **wrk** - HTTP/1.1 and Nginx

<!-- - **Quiver** - AMQP 1.0 and ActiveMQ Artemis -->

## Configuration

The benchmark client is configured using these environment variables:

BENCHDOG_HOST
: The host to connect to

BENCHDOG_PORT
: The port to connect to

BENCHDOG_TLS
: Set to "1" to enable TLS

BENCHDOG_DURATION
: The time in seconds to run the test

BENCHDOG_ITERATIONS
: The number of repeated runs for each scenario

## Unfiled

- https://dev.mysql.com/downloads/benchmarks.html
- https://www.postgresql.org/docs/current/pgbench.html
- https://gist.github.com/jkreps/c7ddb4041ef62a900e6c
- https://github.com/denji/awesome-http-benchmark
- https://github.com/wg/wrk

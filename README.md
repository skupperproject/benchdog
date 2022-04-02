# Benchdog

Containerized client-server benchmarking tools for comparing cloud
networking solutions.

I developed these with a focus on comparing [Skupper][skupper] to
other options for multi-site deployment, but there's nothing
Skupper-specific about them.

[skupper]: https://skupper.io/

## Overview

Each benchmark has a server container and a client container.  All
tests run with a single server instance.  The number of clients varies
across three scenarios: 1 client, 10 clients, and 100 clients.

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

- [**pgbench**](pgbench) - PostgreSQL
- [**wrk**](wrk) - HTTP/1.1 and Nginx

## Configuration

The benchmark client is configured using these environment variables:

- **BENCHDOG_HOST** - The host to connect to (default localhost)
- **BENCHDOG_PORT** - The port to connect to (the default is benchmark-specific)
- **BENCHDOG_TLS** - Set to "1" to connect using TLS (default disabled)
- **BENCHDOG_DURATION** - The time in seconds to run the test (default 60)
- **BENCHDOG_ITERATIONS** - The number of repeated runs for each scenario (default 5)

## Resources

- https://dev.mysql.com/downloads/benchmarks.html
- https://www.postgresql.org/docs/current/pgbench.html
- https://gist.github.com/jkreps/c7ddb4041ef62a900e6c
- https://github.com/denji/awesome-http-benchmark
- https://github.com/wg/wrk

done = function(summary, latency, requests)
    file = io.open("result.json", "w")
    file:write(string.format("{\"duration\": %.03f, \"operations\": %d, \"latency\": {\"average\": %.03f, \"p50\": %.03f, \"p99\": %.03f}}\n",
                             summary.duration / 1000000, summary.requests, latency.mean / 1000, latency:percentile(50) / 1000, latency:percentile(99) / 1000))
    file:close()
end

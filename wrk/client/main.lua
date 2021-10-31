done = function(summary, latency, requests)
    file = io.open("result.json", "w")
    file:write(string.format("{\"duration\": %.02f, \"operations\": %d, \"latency\": {\"average\": %.02f, \"50\": %.02f, \"99\": %.02f}}\n",
                             summary.duration / 1000000, summary.requests, latency.mean, latency:percentile(50), latency:percentile(99)))
    file:close()
end

done = function(summary, latency, requests)
    file = io.open("result.json", "w")
    file:write(string.format("{\"duration\": %.02f, \"operations\": %d, \"latency\": {\"average\": %.02f, \"50\": %.02f, \"99\": %.02f}}\n",
                             summary.duration / 1000000, summary.requests, latency.mean / 1000, latency:percentile(50) / 1000, latency:percentile(99) / 1000))
    file:close()
end

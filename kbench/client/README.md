# Kbench client

~~~
kubectl run client --attach --rm --restart Never --image quay.io/ssorj/benchdog-kbench-client --env BENCHDOG_HOST=kbench-kafka-brokers --env BENCHDOG_PORT=9092
~~~

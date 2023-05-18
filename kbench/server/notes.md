# Kafka notes

## Install

~~~
wget https://dlcdn.apache.org/kafka/3.4.0/kafka_2.13-3.4.0.tgz
tar -xf kafka_2.13-3.4.0
mv kafka_2.13-3.4.0 ~/kafka
cd ~/kafka
KAFKA_CLUSTER_ID="$(bin/kafka-storage.sh random-uuid)"
bin/kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c config/kraft/server.properties
~~~

## Server

~~~
advertised.listeners=PLAINTEXT://localhost:9092

bin/kafka-server-start.sh config/kraft/server.properties
~~~

## Client

~~~
cd ~/kafka/bin

./kafka-topics.sh --create --topic messages --bootstrap-server localhost:9092 --if-not-exists
./kafka-producer-perf-test.sh --topic messages --num-records 1000000 --throughput -1 --record-size 100 --producer-props bootstrap.servers=localhost:9092
./kafka-consumer-perf-test.sh --topic messages --messages 1000000000 --bootstrap-server localhost:9092
~~~

## Unfiled

./kafka-topics.sh --bootstrap-server localhost:9092 --topic kbench --delete --if-exists
./kafka-topics.sh --bootstrap-server localhost:9092 --topic kbench --create --partitions 1

https://developers.redhat.com/articles/2022/05/03/fine-tune-kafka-performance-kafka-optimization-theorem#optimization_goals_for_kafka

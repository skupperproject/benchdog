/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

package io.skupper.kbench;

import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.concurrent.locks.*;
import java.io.*;
import java.util.*;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.errors.WakeupException;

public class Main {
    public static void main(String[] args) throws Exception {
        String host = args[0];
        String port = args[1];
        int duration = Integer.parseInt(args[2]);
        int jobs = Integer.parseInt(args[3]);

        HashMap commonConfig = new HashMap();

        commonConfig.put("bootstrap.servers", host + ":" + port);

        HashMap producerConfig = new HashMap(commonConfig);

        producerConfig.put("producer.type", "async");
        producerConfig.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        producerConfig.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        HashMap consumerConfig = new HashMap(commonConfig);

        consumerConfig.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        consumerConfig.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");

        ProducerThread producer = new ProducerThread(producerConfig);
        ArrayList<ConsumerThread> consumers = new ArrayList();

        for (int i = 0; i < jobs; i++) {
            consumers.add(new ConsumerThread(i, consumerConfig));
        }

        for (ConsumerThread consumer : consumers) {
            consumer.start();
        }

        producer.start();

        Thread.sleep(duration * 1000);

        producer.terminate();
        producer.join();

        for (ConsumerThread consumer : consumers) {
            consumer.terminate();
        }

        for (ConsumerThread consumer : consumers) {
            consumer.join();
        }
    }
}

class ProducerThread extends Thread {
    private final AtomicBoolean stopping = new AtomicBoolean();
    private final KafkaProducer producer;

    ProducerThread(HashMap props) {
        super();

        this.producer = new KafkaProducer(props);
    }

    public void run() {
        try {
            produce();
        } catch (Exception e) {
            System.err.println(e);
        }
    }

    private void produce() throws Exception {
        StringBuilder line = new StringBuilder();

        char[] chars = new char[100];
        Arrays.fill(chars, 'X');
        String body = new String(chars);

        long startTime = System.nanoTime();
        long interval = TimeUnit.SECONDS.toNanos(1) / 10_000;
        long nextTime = startTime + interval;

        try (producer) {
            while (!stopping.get()) {
                long waitTime = nextTime - System.nanoTime();

                if (waitTime > 0) {
                    LockSupport.parkNanos(waitTime);
                }

                nextTime = nextTime + interval;

                long sendTime = System.nanoTime() / 1000;

                line.setLength(0);
                line = line.append(sendTime).append(",").append(body);

                producer.send(new ProducerRecord<String, String>("kbench", line.toString()));
            }
        }
    }

    public void terminate() {
        stopping.set(true);
    }
}

class ConsumerThread extends Thread {
    private final int job;
    private final AtomicBoolean stopping = new AtomicBoolean();
    private final KafkaConsumer consumer;

    ConsumerThread(int job, HashMap props) {
        super();

        this.job = job;

        HashMap copy = new HashMap(props);
        copy.put("group.id", UUID.randomUUID().toString());

        this.consumer = new KafkaConsumer(copy);
    }

    public void run() {
        try {
            consume();
        } catch (Exception e) {
            System.err.println(e);
        }
    }

    private void consume() throws Exception {
        String file = "kbench.log." + this.job;
        BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(file)));
        StringBuilder line = new StringBuilder();

        try (consumer; writer) {
            consumer.subscribe(Arrays.asList(new String[] {"kbench"}));

            while (!stopping.get()) {
                ConsumerRecords<String, String> records = consumer.poll(Long.MAX_VALUE);

                for (ConsumerRecord<String, String> record : records) {
                    String payload = record.value();
                    long sendTime = Long.parseLong(payload.split(",", 0)[0]);
                    long duration = System.nanoTime() / 1000 - sendTime;

                    line.setLength(0);
                    writer.append(line.append(sendTime).append(",").append(duration).append("\n").toString());
                }
            }
        } catch (WakeupException e) {
            if (!stopping.get()) throw e;
        }
    }

    public void terminate() {
        stopping.set(true);
        consumer.wakeup();
    }
}

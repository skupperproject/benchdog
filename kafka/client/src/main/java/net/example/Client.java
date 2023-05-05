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

package net.example;

import java.util.concurrent.atomic.AtomicBoolean;
import java.io.*;
import java.util.*;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;

public class Client {
    public static void main(String[] args) throws Exception {
        int jobCount = Integer.parseInt(args[0]);
        int duration = Integer.parseInt(args[1]);

        HashMap commonConfig = new HashMap();

        commonConfig.put("bootstrap.servers", "localhost:9092");

        HashMap producerConfig = new HashMap(commonConfig);

        producerConfig.put("producer.type", "async");
        producerConfig.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        producerConfig.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        HashMap consumerConfig = new HashMap(commonConfig);

        consumerConfig.put("group.id", UUID.randomUUID().toString());
        consumerConfig.put("enable.auto.commit", true);
        consumerConfig.put("key.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");
        consumerConfig.put("value.deserializer", "org.apache.kafka.common.serialization.StringDeserializer");

        record Job(ProducerThread producer, ConsumerThread consumer) {}
        ArrayList<Job> jobs = new ArrayList();

        for (int i = 0; i < jobCount; i++) {
            jobs.add(new Job(new ProducerThread(producerConfig), new ConsumerThread(consumerConfig, i)));
        }

        for (Job job : jobs) {
            job.producer.start();
            job.consumer.start();
        }

        Thread.sleep(duration * 1000);

        for (Job job : jobs) {
            job.producer.terminate();
            job.consumer.terminate();
        }

        for (Job job : jobs) {
            job.producer.join();
            job.consumer.join();
        }
    }
}

class ProducerThread extends Thread {
    private HashMap props;
    private AtomicBoolean stopping = new AtomicBoolean();

    ProducerThread(HashMap props) {
        super();
        this.props = props;
    }

    public void run() {
        try (KafkaProducer producer = new KafkaProducer(props)) {
            StringBuilder line = new StringBuilder();

            char[] chars = new char[100];
            Arrays.fill(chars, 'X');
            String body = new String(chars);

            while (!stopping.get()) {
                line.setLength(0);

                long sendTime = System.currentTimeMillis();

                line = line.append(sendTime).append(",").append(body);

                producer.send(new ProducerRecord<String, String>("messages", line.toString()));
            }
        }
    }

    public void terminate() {
        stopping.lazySet(true);
    }
}

class ConsumerThread extends Thread {
    private HashMap props;
    private AtomicBoolean stopping = new AtomicBoolean();
    int jobNumber;

    ConsumerThread(HashMap props, int jobNumber) {
        super();

        this.props = props;
        this.jobNumber = jobNumber;
    }

    public void run() {
        String file = "output.log." + this.jobNumber;

        try (BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(file)));
             KafkaConsumer consumer = new KafkaConsumer(props)) {
            consumer.subscribe(Arrays.asList(new String[] {"messages"}));

            StringBuilder line = new StringBuilder();
            boolean running = true;

            while (!stopping.get()) {
                ConsumerRecords<String, String> records = consumer.poll(Long.MAX_VALUE);

                for (ConsumerRecord<String, String> record : records) {
                    line.setLength(0);

                    long receiveTime = System.currentTimeMillis();
                    String payload = record.value();
                    String sendTime = payload.split(",", 0)[0];

                    writer.append(line.append(sendTime).append(",").append(receiveTime).append("\n").toString());
                }
            }
        } catch (Exception e) {
            System.err.println(e);
        }
    }

    public void terminate() {
        stopping.lazySet(true);
    }
}

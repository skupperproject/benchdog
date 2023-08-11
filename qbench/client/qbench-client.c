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

#include <proton/engine.h>
#include <proton/error.h>
#include <proton/event.h>
#include <proton/listener.h>
#include <proton/message.h>
#include <proton/proactor.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct worker {
    pn_bytes_t body_bytes;
    pn_proactor_t* proactor;
    pn_connection_t* connection;
    pn_message_t* request_message;
    pn_message_t* response_message;
    pn_rwbytes_t* message_buffer;
    FILE* log_file;
    long sender_sequence;
    int credit_window;
    int id;
} worker_t;

static void fail(char* message) {
    fprintf(stderr, "FAILED: %s\n", message);
    abort();
}

static void error(char* message) {
    fprintf(stderr, "ERROR: %s\n", message);
}

static void info(char* message) {
    printf("%s\n", message);
}

static bool delivery_done(pn_delivery_t* delivery) {
    return pn_delivery_readable(delivery) && !pn_delivery_partial(delivery);
}

static ssize_t message_encode(pn_message_t* message, char* buffer, size_t size) {
    size_t inout_size = size;
    int err = pn_message_encode(message, buffer, &inout_size);

    if (err) return err;

    return inout_size;
}

static int message_send(pn_message_t* message, pn_link_t* sender, pn_rwbytes_t* buffer) {
    ssize_t ret;

    while (true) {
        ret = message_encode(message, buffer->start, buffer->size);

        if (ret == PN_OVERFLOW) {
            buffer->size *= 2;
            buffer->start = (char*) realloc(buffer->start, buffer->size);

            if (!buffer->start) return PN_OUT_OF_MEMORY;

            continue;
        }

        if (ret < 0) return ret;

        break;
    }

    // API: I want pn_delivery to take a NULL for the delivery
    // tag.  Want it to generate the tag for me.
    //
    // Alternatively, I could do it in message_send.
    pn_delivery_t* delivery = pn_delivery(sender, pn_bytes_null);

    ret = pn_link_send(sender, buffer->start, ret);
    if (ret < 0) return ret;

    pn_link_advance(sender);

    return 0;
}

static int message_receive(pn_message_t* message, pn_link_t* receiver, pn_rwbytes_t* buffer) {
    pn_delivery_t* delivery = pn_link_current(receiver);
    ssize_t size = pn_delivery_pending(delivery);
    ssize_t ret;

    if (buffer->size < size) {
        buffer->start = realloc(buffer->start, size);
        buffer->size = size;
    }

    ret = pn_link_recv(receiver, buffer->start, size);
    if (ret < 0) return ret;
    if (ret != size) return PN_ERR;

    ret = pn_message_decode(message, buffer->start, size);
    if (ret) return ret;

    pn_link_advance(receiver);

    return 0;
}

static int worker_send_message(worker_t* worker, pn_event_t* event) {
    pn_link_t* sender = pn_event_link(event);
    int err;

    pn_msgid_t id = (pn_msgid_t) {
        .type = PN_ULONG,
        .u.as_ulong = worker->sender_sequence,
    };

    pn_message_set_id(worker->request_message, id);

    // pn_data_t* body = pn_message_body(worker->request_message);
    // pn_data_put_string(body, pn_data_get_string(request_body));

    err = message_send(worker->request_message, sender, worker->message_buffer);
    if (err) return err;

    worker->sender_sequence += 1;

    return 0;
}

static int worker_receive_message(worker_t* worker, pn_event_t* event) {
    pn_delivery_t* delivery = pn_event_delivery(event);
    pn_link_t* receiver = pn_event_link(event);
    int err;

    err = message_receive(worker->response_message, receiver, worker->message_buffer);
    if (err) return err;

    fprintf(worker->log_file, "1,1\n"); // XXX

    pn_delivery_update(delivery, PN_ACCEPTED);
    pn_delivery_settle(delivery);

    pn_link_flow(receiver, worker->credit_window - pn_link_credit(receiver));

    return 0;
}

static void check_condition(pn_event_t* event, pn_condition_t* condition) {
    if (pn_condition_is_set(condition)) {
        fprintf(stderr, "ERROR: %s: %s: %s",
                pn_event_type_name(pn_event_type(event)),
                pn_condition_get_name(condition),
                pn_condition_get_description(condition));
    }
}

static int worker_handle_event(worker_t* worker, pn_event_t* event, bool* running) {
    switch (pn_event_type(event)) {
    case PN_CONNECTION_INIT: {
        pn_connection_t* connection = pn_event_connection(event);
        pn_session_t* session = pn_session(connection);

        pn_connection_set_container(pn_event_connection(event), "qbench-client");
        pn_session_open(session);

        pn_link_t* sender = pn_sender(session, "requests");
        pn_terminus_t* sender_target = pn_link_target(sender);

        pn_terminus_set_address(sender_target, "requests");
        pn_link_open(sender);

        pn_link_t* receiver = pn_receiver(session, "responses");
        pn_terminus_t* receiver_target = pn_link_target(receiver);

        pn_terminus_set_address(receiver_target, "responses");
        pn_link_open(receiver);
        pn_link_flow(receiver, worker->credit_window);

        break;
    }
    case PN_LINK_FLOW: {
        pn_link_t* sender = pn_event_link(event);
        int err;

        if (pn_link_is_receiver(sender)) fail("in flow link_is_receiver");

        while (pn_link_credit(sender) > 0) {
            err = worker_send_message(worker, event);
            if (err) return err;
        }

        break;
    }
    case PN_DELIVERY: {
        pn_delivery_t* delivery = pn_event_delivery(event);
        pn_link_t* link = pn_delivery_link(delivery);
        int err;

        if (pn_link_is_receiver(link)) {
            // Receiver
            if (delivery_done(delivery)) {
                err = worker_receive_message(worker, event);
                if (err) return err;
            }
        } else {
            // Sender
            pn_delivery_settle(delivery);
        }

        break;
    }
    case PN_CONNECTION_REMOTE_CLOSE: {
        pn_connection_t* connection = pn_event_connection(event);

        check_condition(event, pn_connection_remote_condition(connection));
        pn_connection_close(connection);

        break;
    }
    case PN_SESSION_REMOTE_CLOSE: {
        pn_session_t* session = pn_event_session(event);

        check_condition(event, pn_session_remote_condition(session));
        pn_session_close(session);

        break;
    }
    case PN_LINK_REMOTE_CLOSE: {
        pn_link_t* link = pn_event_link(event);

        check_condition(event, pn_link_remote_condition(link));
        pn_link_close(link);

        break;
    }
    case PN_PROACTOR_INTERRUPT: {
        // Interrupt the next thread
        pn_proactor_interrupt(worker->proactor);
        *running = false;
        return 0;
    }
    }

    return 0;
}

static void worker_init(worker_t* worker, int id, pn_proactor_t* proactor, int credit_window) {
    pn_rwbytes_t* buffer = (pn_rwbytes_t*) malloc(sizeof(pn_rwbytes_t));

    *buffer = (pn_rwbytes_t) {
        .size = 64,
        .start = malloc(64),
    };

    const int body_size = 100;
    char* body_bytes = (char*) malloc(body_size);
    memset(body_bytes, 'x', body_size);

    *worker = (worker_t) {
        .id = id,
        .proactor = proactor,
        .request_message = pn_message(),
        .response_message = pn_message(),
        .message_buffer = buffer,
        .credit_window = credit_window,
        .body_bytes = pn_bytes(body_size, body_bytes),
    };
}

static void worker_free(worker_t* worker) {
    pn_message_free(worker->request_message);
    pn_message_free(worker->response_message);

    free(worker->message_buffer->start);
    free(worker->message_buffer);
    free((char*) worker->body_bytes.start);
}

static void* worker_run(void* data) {
    worker_t* worker = (worker_t*) data;
    int id = worker->id;

    char log_file_name[256];
    snprintf(log_file_name, sizeof(log_file_name), "qbench.%d.log", id);

    worker->log_file = fopen(log_file_name, "w");
    if (!worker->log_file) fail("fopen");

    char addr[256];
    pn_connection_t* connection = pn_connection();

    pn_proactor_addr(addr, sizeof(addr), "localhost", "5672");
    pn_proactor_connect2(worker->proactor, connection, NULL, addr);

    bool running = true;

    while (running) {
        pn_event_batch_t* batch = pn_proactor_wait(worker->proactor);
        pn_event_t* event;
        int err;

        while ((event = pn_event_batch_next(batch))) {
            err = worker_handle_event(worker, event, &running);
            if (err) error("Error handling event");
        }

        pn_proactor_done(worker->proactor, batch);
    }

    fflush(worker->log_file);

    return NULL;
}

static pn_proactor_t* proactor = NULL;

static void signal_handler(int signum) {
    pn_proactor_interrupt(proactor);
}

int main(size_t argc, char** argv) {
    proactor = pn_proactor();

    const int worker_count = 10;
    worker_t workers[worker_count];
    pthread_t worker_threads[worker_count];

    signal(SIGINT, signal_handler);
    signal(SIGQUIT, signal_handler);
    signal(SIGTERM, signal_handler);

    for (int i = 0; i < worker_count; i++) {
        worker_init(&workers[i], i, proactor, 1000);
        pthread_create(&worker_threads[i], NULL, &worker_run, &workers[i]);
    }

    info("Client started");

    for (int i = 0; i < worker_count; i++) {
        pthread_join(worker_threads[i], NULL);
        worker_free(&workers[i]);
    }

    pn_proactor_free(proactor);

    info("Client stopped");
}

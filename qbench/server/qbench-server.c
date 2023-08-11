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

typedef struct worker {
    pn_proactor_t* proactor;
    pn_message_t* request_message;
    pn_message_t* response_message;
    pn_rwbytes_t* message_buffer;
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

static bool delivery_complete(pn_delivery_t* delivery) {
    return pn_delivery_readable(delivery) && !pn_delivery_partial(delivery);
}

static ssize_t message_encode(pn_message_t* message, char* buffer, size_t size) {
    size_t inout_size = size;
    int err = pn_message_encode(message, buffer, &inout_size);

    if (err) return err;

    return inout_size;
}

static int message_send(pn_link_t* sender, pn_message_t* message, pn_rwbytes_t* buffer) {
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
    pn_delivery_t* delivery = pn_delivery(sender, pn_bytes_null);

    ret = pn_link_send(sender, buffer->start, ret);
    if (ret < 0) return ret;

    pn_link_advance(sender);

    return 0;
}

static int message_receive(pn_delivery_t* delivery, pn_message_t* message, pn_rwbytes_t* buffer) {
    pn_link_t* receiver = pn_delivery_link(delivery);
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

static int worker_receive_message(worker_t* worker, pn_event_t* event) {
    pn_delivery_t* delivery = pn_event_delivery(event);
    pn_link_t* receiver = pn_event_link(event);
    pn_connection_t* connection = pn_event_connection(event);
    int err;

    err = message_receive(delivery, worker->request_message, worker->message_buffer);
    if (err) return err;

    pn_message_set_address(worker->response_message, pn_message_get_reply_to(worker->request_message));
    pn_message_set_correlation_id(worker->response_message, pn_message_get_id(worker->request_message));

    pn_data_t* request_body = pn_message_body(worker->request_message);
    pn_data_t* response_body = pn_message_body(worker->response_message);

    pn_data_next(request_body);
    pn_data_put_string(response_body, pn_data_get_string(request_body));

    pn_link_t* sender = (pn_link_t*) pn_connection_get_context(connection);

    // XXX Not sure I need this
    if (!sender) fail("sender is null");

    message_send(sender, worker->response_message, worker->message_buffer);

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
    case PN_LISTENER_ACCEPT: {
        pn_listener_t* listener = pn_event_listener(event);
        pn_connection_t* connection = pn_connection();

        pn_listener_accept(listener, connection);

        break;
    }
    case PN_CONNECTION_INIT: {
        pn_connection_set_container(pn_event_connection(event), "qbench-server");
        break;
    }
    case PN_CONNECTION_REMOTE_OPEN: {
        pn_connection_open(pn_event_connection(event));
        break;
    }
    case PN_SESSION_REMOTE_OPEN: {
        pn_session_open(pn_event_session(event));
        break;
    }
    case PN_LINK_REMOTE_OPEN: {
        pn_link_t* link = pn_event_link(event);
        pn_terminus_t* target = pn_link_target(link);
        pn_terminus_t* remote_target = pn_link_remote_target(link);
        const char* remote_address = pn_terminus_get_address(remote_target);

        pn_terminus_set_address(target, remote_address);
        pn_link_open(link);

        if (pn_link_is_receiver(link)) {
            // Receiver
            pn_link_flow(link, worker->credit_window);
        } else {
            // Sender

            // Save the sender for sending responses
            pn_connection_set_context(pn_event_connection(event), link);
        }

        break;
    }
    case PN_DELIVERY: {
        pn_delivery_t* delivery = pn_event_delivery(event);
        pn_link_t* link = pn_delivery_link(delivery);
        int err;

        if (pn_link_is_receiver(link)) {
            // Receiver
            if (delivery_complete(delivery)) {
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
    case PN_LISTENER_CLOSE: {
        check_condition(event, pn_connection_remote_condition(pn_event_connection(event)));
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

    *worker = (worker_t) {
        .id = id,
        .proactor = proactor,
        .request_message = pn_message(),
        .response_message = pn_message(),
        .message_buffer = buffer,
        .credit_window = credit_window,
    };
}

static void worker_free(worker_t* worker) {
    pn_message_free(worker->request_message);
    pn_message_free(worker->response_message);

    free(worker->message_buffer->start);
    free(worker->message_buffer);
}

static void* worker_run(void* data) {
    worker_t* worker = (worker_t*) data;
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

    return NULL;
}

static pn_proactor_t* proactor = NULL;

static void signal_handler(int signum) {
    pn_proactor_interrupt(proactor);
}

int main(size_t argc, char** argv) {
    proactor = pn_proactor();
    pn_listener_t* listener = pn_listener();
    char addr[256];

    const int worker_count = 10;
    worker_t workers[worker_count];
    pthread_t worker_threads[worker_count];

    signal(SIGINT, signal_handler);
    signal(SIGQUIT, signal_handler);
    signal(SIGTERM, signal_handler);

    pn_proactor_addr(addr, sizeof(addr), "localhost", "5672");
    pn_proactor_listen(proactor, listener, addr, 32);

    for (int i = 0; i < worker_count; i++) {
        worker_init(&workers[i], i, proactor, 1000);
        pthread_create(&worker_threads[i], NULL, &worker_run, &workers[i]);
    }

    info("Server started");

    for (int i = 0; i < worker_count; i++) {
        pthread_join(worker_threads[i], NULL);
        worker_free(&workers[i]);
    }

    pn_proactor_free(proactor);

    info("Server stopped");
}

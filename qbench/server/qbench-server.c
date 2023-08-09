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
    pn_link_t* sender;
    pn_message_t* request_message;
    pn_message_t* response_message;
    pn_rwbytes_t* message_buffer;
    long sender_sequence;
    int credit_window;
} worker_t;

static int message_send(pn_message_t* message, pn_delivery_t* delivery, pn_rwbytes_t* buffer) {
    pn_link_t* sender = pn_delivery_link(delivery);
    ssize_t ret;

    ret = pn_message_encode2(message, buffer);
    if (ret < 0) return ret;

    ret = pn_link_send(sender, buffer->start, ret);
    if (ret < 0) return ret;

    pn_link_advance(sender);

    return 0;
}

static int message_receive(pn_message_t* message, pn_delivery_t* delivery, pn_rwbytes_t* buffer) {
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

// delivery instead of event in signature XXX
static int worker_handle_delivery(worker_t* worker, pn_event_t* event) {
    pn_delivery_t* delivery = pn_event_delivery(event);
    pn_link_t* receiver = pn_delivery_link(delivery);
    int err;

    err = message_receive(worker->request_message, delivery, worker->message_buffer);
    if (err) return err;

    pn_message_set_address(worker->response_message, pn_message_get_reply_to(worker->request_message));
    pn_message_set_correlation_id(worker->response_message, pn_message_get_id(worker->request_message));

    pn_data_t* request_body = pn_message_body(worker->request_message);
    pn_data_t* response_body = pn_message_body(worker->response_message);

    pn_data_next(request_body);
    pn_data_put_string(response_body, pn_data_get_string(request_body));

    // API: I want pn_delivery to take a NULL for the delivery tag.
    // pn_delivery_tag_t tag = pn_dtag((char*) &worker->sender_sequence, sizeof(worker->sender_sequence));
    pn_delivery_t* response_delivery = pn_delivery(worker->sender, pn_bytes_null);

    err = message_send(worker->response_message, response_delivery, worker->message_buffer);
    if (err) return err;

    worker->sender_sequence += 1;

    // API: Want pn_delivery_accept(delivery);
    pn_delivery_update(delivery, PN_ACCEPTED);
    pn_delivery_settle(delivery);

    pn_link_flow(receiver, worker->credit_window - pn_link_credit(receiver));

    return 0;
}

static void check_condition(pn_event_t* event, pn_condition_t* condition) {
    if (pn_condition_is_set(condition)) {
        fprintf(stderr, "%s: %s: %s",
                pn_event_type_name(pn_event_type(event)),
                pn_condition_get_name(condition),
                pn_condition_get_description(condition));
        abort();
    }
}

// XXX return int error and pass running by ref
static bool worker_handle_event(worker_t* worker, pn_event_t* event) {
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
        pn_terminus_t* local_target = pn_link_target(link);
        pn_terminus_t* remote_target = pn_link_remote_target(link);
        const char* remote_address = pn_terminus_get_address(remote_target);

        if (pn_link_is_sender(link)) {
            // Open an anonymous sender

            // pn_terminus_set_address(local_target, NULL);
            // pn_terminus_set_dynamic(local_target, true);

            pn_link_open(link);

            worker->sender = link;
        } else if (pn_link_is_receiver(link)) {
            pn_terminus_set_address(local_target, remote_address);
            pn_link_open(link);
            pn_link_flow(link, worker->credit_window);
        } else {
            abort();
        }

        break;
    }
    case PN_DELIVERY: {
        // API: Using PN_DELIVERY for so many different things sucks.
        // We could have DELIVERY_ENTIRE vs partial
        // We could have PN_TRACKER or PN_DELIVERY_DISPOSITION_UPDATE

        pn_delivery_t* delivery = pn_event_delivery(event);
        pn_link_t* link = pn_delivery_link(delivery);
        int err;

        // API: Want to avoid the link types here.  Want to focus on a
        // message *or* an ack.
        if (pn_link_is_sender(link)) {
            // Message acknowledged
            pn_delivery_settle(delivery);
        } else if (pn_link_is_receiver(link)) {
            // API: These preconditions also suck.

            if (!pn_delivery_readable(delivery)) {
                printf("!pn_delivery_readable\n");
                break;
            }

            if (pn_delivery_partial(delivery)) {
                printf("pn_delivery_partial\n");
                break;
            }

            if (!worker->sender) {
                printf("sender not ready\n");
                break;
            }

            // Message received
            err = worker_handle_delivery(worker, event);
            if (err) abort();
        } else {
            abort();
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
        return false;
    }
    }

    return true;
}

static void worker_init(worker_t* worker, pn_proactor_t* proactor, int credit_window) {
    pn_rwbytes_t* buf = (pn_rwbytes_t*) malloc(sizeof(pn_rwbytes_t));

    *buf = (pn_rwbytes_t) {0};

    *worker = (worker_t) {
        .proactor = proactor,
        .request_message = pn_message(),
        .response_message = pn_message(),
        .message_buffer = buf,
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

        while (running && (event = pn_event_batch_next(batch))) {
            running = worker_handle_event(worker, event);
        }

        // API: Should be pn_event_batch_done(batch) IMO.
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

    const int worker_count = 1;
    worker_t workers[worker_count];
    pthread_t worker_threads[worker_count];

    signal(SIGINT, signal_handler);
    signal(SIGQUIT, signal_handler);
    signal(SIGTERM, signal_handler);

    printf("Starting\n");

    pn_proactor_addr(addr, sizeof(addr), "localhost", "5672");
    pn_proactor_listen(proactor, listener, addr, 32);

    for (int i = 0; i < worker_count; i++) {
        worker_init(&workers[i], proactor, 10);
        pthread_create(&worker_threads[i], NULL, &worker_run, &workers[i]);
    }

    for (int i = 0; i < worker_count; i++) {
        pthread_join(worker_threads[i], NULL);
        worker_free(&workers[i]);
    }

    pn_proactor_free(proactor);

    printf("Stopping\n");
}

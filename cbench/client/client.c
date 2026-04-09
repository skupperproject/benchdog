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

#define _GNU_SOURCE

#include <errno.h>
#include <netdb.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

typedef struct thread_context {
    int id;
    uint16_t port;
    char * host_name;
    char * output_dir;
} thread_context_t;


double first_timestamp = 0;

double timestamp() {
    struct timeval t;
    gettimeofday(&t, 0);
    double ts = t.tv_sec + ((double) t.tv_usec) / 1000000.0;
    return ts - first_timestamp;
}


void * client ( void * data ) {
    thread_context_t * ctx = (thread_context_t *) data;
    char * output_dir = ctx->output_dir;
    char * host_name  = ctx->host_name;
    int id            = ctx->id;
    uint16_t port_number          = ctx->port;

    // Get the output file
    char transfers_file[256];
    snprintf(transfers_file, 256, "%s/connections.%d.data", output_dir, id);

    FILE* transfers = fopen(transfers_file, "w");
    if (!transfers) goto bailout;

    int connection_count = 0;
    while (1) {
        struct sockaddr_in router_addr;
        struct hostent * router;
        int sockfd;

        if ( (sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0 ) {
            perror ( "Socket creation failed" );
            exit ( 1 );
        }

        if ((router = gethostbyname(host_name)) == NULL) {
            fprintf(stderr, "No such host: %s\n", host_name);
            exit ( 1 );
        }

        // Set router address and port
        bzero ( (char *) & router_addr, sizeof(router_addr) );
        router_addr.sin_family = AF_INET;
        bcopy ((char *)router->h_addr,
               (char *)&router_addr.sin_addr.s_addr,
               router->h_length);
        router_addr.sin_port = htons(port_number);

        double start_time = timestamp();
        // Connect to router
        if (connect(sockfd, (struct sockaddr *)&router_addr, sizeof(router_addr)) < 0) {
            perror("Connection failed");
            exit(1);
        }

        // Receive message from server, and measure the time it took
        // to make this connection.
        // This means we are overestimating the connect time, but this 
        // is the only way we can be sure that the connection has gone 
        // all the way through the router network to the server.
        char buffer[1024];
        ssize_t n = recv ( sockfd, buffer, sizeof(buffer) - 1, 0 );
        close ( sockfd );
        if (n <= 0) {
          fprintf ( stderr, "message failure: recv returned %zd\n", n );
          goto bailout;
        }

        // Measure the connection time and store it in the output file.
        double duration = timestamp() - start_time;
        ++ connection_count;
        fprintf(transfers, "%.6lf,%6lf\n", start_time, duration);
        fflush(transfers);
    }

bailout:

    fclose(transfers);
    if (errno) {
        fprintf(stderr, "client: ERROR! %s\n", strerror(errno));
    }
}


int main(size_t argc, char** argv) {
    if (argc != 3) {
        fprintf(stderr, "Usage: client JOBS OUTPUT-DIR\n");
        return 1;
    }
    int jobs = atoi(argv[1]);
    char* output_dir = argv[2];

    // These two are environment variables because
    // I want to be able to supply them from the 
    // 'kubectl run' command.
    char* host     = getenv("CBENCH_HOST");
    char* port_str = getenv("CBENCH_PORT");

    if (! (host && port_str)) {
        fprintf(stderr, "need host and port\n");
        exit(1);
    }
    uint16_t port_number = atoi(port_str);

    thread_context_t contexts       [jobs];
    pthread_t        client_threads [jobs];

    // This will be Time Zero for all other timestamps.
    first_timestamp = timestamp();

    // Start all the threads that will make connections
    // as fast as they can.
    // Send each one its own context.
    for (int i = 0; i < jobs; i++) {
        contexts[i] = (thread_context_t) {
            .id = i,
            .port = port_number,
            .host_name = host,
            .output_dir = output_dir,
        };
        pthread_create(client_threads+i, NULL, & client, contexts+i);
    }

    for(int i = 0; i < jobs; i++) {
        pthread_join(client_threads[i], NULL);
    }

    exit(errno);
}




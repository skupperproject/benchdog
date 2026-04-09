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

#include <errno.h>
#include <netdb.h>
#include <netinet/tcp.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>


typedef struct thread_context {
    int socket;
} thread_context_t;


int main ( size_t argc, char** argv ) {
    if (argc != 2) {
      fprintf(stderr, "Usage: server PORT\n");
      return 1;
    }

    int port = atoi(argv[1]);

    int server_sock = socket(AF_INET, SOCK_STREAM, 0);
    if (server_sock < 0) goto skedaddle ;

    int opt = 1;
    int err = setsockopt(server_sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    if (err) goto skedaddle ;

    struct sockaddr_in addr = (struct sockaddr_in) {
        0,
        .sin_family = AF_INET,
        .sin_addr.s_addr = htonl(INADDR_ANY),
        .sin_port = htons(port)
    };

    err = bind(server_sock, (const struct sockaddr*) &addr, sizeof(addr));
    if (err) goto skedaddle ;

    // This program is terminated by the shell script.
    while (1) {
        err = listen(server_sock, 1);
        if (err) goto skedaddle ;
        int sock = accept(server_sock, NULL, NULL);
        if (sock < 0) goto skedaddle ;
        char* str = "server says hi";
        int n = write(sock, str, strlen(str));
        if (n < 0) goto skedaddle ;
        close(sock);
    }

skedaddle :

    if (errno) {
        fprintf(stderr, "server: ERROR! %s\n", strerror(errno));
    }

    if (server_sock > 0) {
        shutdown(server_sock, SHUT_RDWR);
    }

    return errno;
}



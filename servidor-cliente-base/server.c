#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/socket.h>

#include "common.h"

/* Function to prompt the usage of the program and exit */
void usage(const char **argv) {
    printf("Usage: %s <v4|v6> <server port>\n", argv[0]);
    printf("Example: %s v4 51511\n", argv[0]);

    exit(EXIT_FAILURE);
}

/* Function to initialize server address returning 0 on success and -1 otherwise */
int server_sockaddr_init(struct sockaddr_storage *storage, const char *protostr, const char *portstr) {
    if (protostr == NULL || portstr == NULL) {
        return -1;
    }
    
    // Clearing any garbage data on storage pointer
    memset(storage, 0, sizeof(*storage));

    // Parsing port from string to unsigned short
    uint16_t port = (uint16_t) atoi(portstr);
    if (port == 0) {
        return -1;
    }

    // Converting from host to network endian
    port = htons(port);

    // Passed protocol is IPv4
    if (strcmp(protostr, "v4") == 0) {
        struct sockaddr_in *addr4 = (struct sockaddr_in *) storage;
        addr4->sin_family = AF_INET;
        addr4->sin_port = port;
        addr4->sin_addr.s_addr = INADDR_ANY;
        return 0;
    }
    
    // Passed protocol is IPv6
    else if (strcmp(protostr, "v6") == 0) {
        struct sockaddr_in6 *addr6 = (struct sockaddr_in6 *) storage;
        addr6->sin6_family = AF_INET6;
        addr6->sin6_port = port;
        addr6->sin6_addr = in6addr_any;
        return 0;
    }

    // Unknown protocol family (neither v4 nor v6)
    return -1;
}

int main(int argc, const char **argv) {
    // Checking program arguments (must be exactly 3)
    if (argc != 3) {
        usage(argv);
    }

    // Initializing server address
    struct sockaddr_storage storage;
    if (server_sockaddr_init(&storage, argv[1], argv[2]) != 0) {
        usage(argv);
    }

    // Creating server socket
    int server_socket = socket(storage.ss_family, SOCK_STREAM, 0);
    if (server_socket == -1) {
        logexit("socket");
    }

    // Enabling reconnection to the same port
    int enable = 1;
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, &enable, sizeof(int)) != 0) {
        logexit("setsockopt");
    }

    // Binding server address
    struct sockaddr *addr = (struct sockaddr *) (&storage);
    if (bind(server_socket, addr, sizeof(storage)) != 0) {
        logexit("bind");
    }

    // Listen connections (max to 10 in this case)
    if (listen(server_socket, 10)) {
        logexit("listen");
    }

    // Parsing "addr" structure to string
    char addrstr[BUFSZ];
    addrtostr(addr, addrstr, BUFSZ);
    printf("Bound to %s, waiting connections...\n", addrstr);


    // Main loop to treat information from clients
    while (1) {
        // Creating client storage and address structure
        struct sockaddr_storage client_storage;
        struct sockaddr *client_addr = (struct sockaddr *) (&client_storage);

        // Getting client socket
        socklen_t client_addrlen = sizeof(client_storage);
        int client_socket = accept(server_socket, client_addr, &client_addrlen);
        if (client_socket == -1) {
            logexit("accept");
        }

        // Logging client address
        char client_addrstr[BUFSZ];
        addrtostr(client_addr, client_addrstr, BUFSZ);
        printf("[log] Connection from %s\n", client_addrstr);

        // Creating buffer structure to store messages
        char buffer[BUFSZ];
        memset(buffer, 0, BUFSZ);

        // Receiving and logging client message
        size_t count_bytes = recv(client_socket, buffer, BUFSZ, 0);
        printf("[msg] %s, %lu bytes: %s\n", client_addrstr, count_bytes, buffer);

        // Sending a default message to the client
        snprintf(buffer, BUFSZ, "remote endpoint: %.1000s\n", client_addrstr);
        count_bytes = send(client_socket, buffer, strlen(buffer) + 1, 0);
        if (count_bytes != strlen(buffer) + 1) {
            logexit("send");
        }

        // Closing connection with client
        close(client_socket);
    }

    return 0;
}
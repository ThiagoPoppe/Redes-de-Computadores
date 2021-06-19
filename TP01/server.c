#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/socket.h>

#include "common.h"
#include "location_array.h"

// Function to prompt the usage of the program and exit
void usage(const char *argv[]) {
    printf("usage: %s <v4|v6> <server port>\n", argv[0]);
    exit(EXIT_FAILURE);
}

// Function to initiliaze the server storage, returning 0 on success and -1 otherwise
int init_server_storage(struct sockaddr_storage *storage, const char *protostr, const char *portstr) {
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

int main(int argc, const char *argv[]) {
    if (argc != 3)
        usage(argv);

    // Initializing server storage
    struct sockaddr_storage server_storage;
    if (init_server_storage(&server_storage, argv[1], argv[2]) != 0)
        usage(argv);

    // Creating server socket
    int server_socket = socket(server_storage.ss_family, SOCK_STREAM, 0);
    if (server_socket == -1)
        logexit("socket");

    // Enabling reconnection to the same port
    int enable = 1;
    if (setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, &enable, sizeof(int)) != 0)
        logexit("setsockopt");

    // Binding server address
    struct sockaddr *server_addr = (struct sockaddr *) (&server_storage);
    if (bind(server_socket, server_addr, sizeof(server_storage)) != 0)
        logexit("bind");

    // Listen connections (max to 1 in this case)
    if (listen(server_socket, 1))
        logexit("listen");

    // Debugging connection
    char addrstr[BUFSZ];
    addrtostr(server_addr, addrstr, BUFSZ);
    printf("bound to %s, waiting connections...\n", addrstr);

    // Main loop to receive clients
    int server_closed = 0;
    while (!server_closed) {
        // Creating client storage and address structure
        struct sockaddr_storage client_storage;
        struct sockaddr *client_addr = (struct sockaddr *) (&client_storage);

        // Accepting and getting client socket
        socklen_t client_addrlen = sizeof(client_storage);
        int client_socket = accept(server_socket, client_addr, &client_addrlen);
        if (client_socket == -1)
            logexit("accept");

        // Logging client address
        char client_addrstr[BUFSZ];
        addrtostr(client_addr, client_addrstr, BUFSZ);
        printf("received connection from: %s\n", client_addrstr);

        // Loop to communicate with the client
        int client_disconnected = 0;
        while (!client_disconnected) {
            // Creating buffer structure to store messages
            char buffer[BUFSZ];
            memset(buffer, 0, BUFSZ);

            // Loop to receive client information
            size_t count_bytes = 0;
            unsigned int total_bytes = 0;
            int received_complete_message = 0;
            while (!received_complete_message && !client_disconnected) {
                // Notice that the message may be sent to the client in "small parts"
                // So we will keep track of the total bytes received until this moment
                count_bytes = recv(client_socket, buffer + total_bytes, BUFSZ, 0);
                total_bytes += count_bytes;

                // Checking if client disconnected (received 0 bytes)
                if (count_bytes == 0 || count_bytes == -1)
                    client_disconnected = 1;
                
                // Checking if the message was fully received
                else if (buffer[total_bytes - 1] == '\n')
                    received_complete_message = 1;
            }

            if (!client_disconnected) {
                // Treating client message
                if (strcmp(buffer, "kill\n") == 0) {
                    client_disconnected = 1;
                    server_closed = 1;
                    close(client_socket);
                }
                else {
                    // Debugging client message
                    printf("%u bytes: %s", total_bytes, buffer);

                    // Sending a default message to the client
                    sprintf(buffer, "this is a default message :)\n");
                    count_bytes = send(client_socket, buffer, strlen(buffer), 0);
                    if (count_bytes != strlen(buffer))
                        logexit("send");
                }
            }
        }
    }

    // Closing server
    printf("closing server...\n");
    close(server_socket);
}
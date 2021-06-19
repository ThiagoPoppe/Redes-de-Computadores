#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <sys/types.h>
#include <sys/socket.h>

#include "common.h"

/* Function to prompt the usage of the program and exit */
void usage(const char **argv) {
    printf("Usage: %s <server IP> <server port>\n", argv[0]);
    printf("Example: %s 127.0.0.1 51511\n", argv[0]);
    
    exit(EXIT_FAILURE);
}

int main(int argc, const char **argv) {
    // Checking program arguments (must be exactly 3)
    if (argc != 3) {
        usage(argv);
    }

    // Parsing server IP and server port to storage
    struct sockaddr_storage storage;
    if (addrparse(&storage, argv[1], argv[2]) != 0) {
        usage(argv);
    }

    // Creating client socket
    int client_socket = socket(storage.ss_family, SOCK_STREAM, 0);
    if (client_socket == -1) {
        logexit("socket");
    }

    // Establishing connection with server
    struct sockaddr *addr = (struct sockaddr *) (&storage);
    if (connect(client_socket, addr, sizeof(storage)) != 0) {
        logexit("connect");
    }

    // Parsing "addr" structure to string
    char addrstr[BUFSZ];
    addrtostr(addr, addrstr, BUFSZ);
    printf("Connected to %s\n", addrstr);

    // Creating buffer structure to store messages
    char buffer[BUFSZ];
    memset(buffer, 0, BUFSZ);

    // Reading client message from keyboard
    printf("message> ");
    fgets(buffer, BUFSZ, stdin);

    // Sending message to server and checking if we sent it correctly
    size_t count_bytes = send(client_socket, buffer, strlen(buffer) + 1, 0);
    if (count_bytes != strlen(buffer) + 1) {
        logexit("send");
    }

    // Reseting buffer content
    memset(buffer, 0, BUFSZ);

    // Main loop to receive information from server
    unsigned int total_bytes = 0;
    while (1) {
        // Notice that the message may be sent to the client in "small parts"
        count_bytes = recv(client_socket, buffer + total_bytes, BUFSZ, 0);
        
        // Checking if the connection has terminated (received 0 bytes)
        if (count_bytes == 0) {
            break;
        }

        // Updating total read bytes
        total_bytes += count_bytes;
    }

    // Printing received message to the client
    printf("Received in total %u bytes\n", total_bytes);
    printf("Final message: %s\n", buffer);

    // Closing connection
    close(client_socket);

    return 0;
}
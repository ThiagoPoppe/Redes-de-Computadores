#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <inttypes.h>

#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/socket.h>

#include "common.h"

// Function to prompt the usage of the program and exit
void usage(const char *argv[]) {
    printf("usage: %s <server IP> <server port>\n", argv[0]);
    exit(EXIT_FAILURE);
}

// Function to initiliaze the client storage, returning 0 on success and -1 otherwise
int init_client_storage(struct sockaddr_storage *storage, const char *addrstr, const char *portstr) {
    if (addrstr == NULL || portstr == NULL)
        return -1;

    // Clearing any gargabe data on pointed storage
    memset(storage, 0, sizeof(*storage));

    // Parsing port from string to unsigned short
    uint16_t port = (uint16_t) atoi(portstr);
    if (port == 0)
        return -1;

    // Converting from host to network endian
    port = htons(port);

    // Trying to parse address as IPv4
    struct in_addr inaddr4; // 32-bits IP address
    if (inet_pton(AF_INET, addrstr, &inaddr4)) {
        struct sockaddr_in *addr4 = (struct sockaddr_in *) storage;
        addr4->sin_family = AF_INET;
        addr4->sin_port = port;
        addr4->sin_addr = inaddr4;
        return 0;
    }

    // Trying to parse address as IPv6
    struct in6_addr inaddr6; // 128-bits IP address
    if (inet_pton(AF_INET6, addrstr, &inaddr6)) {
        struct sockaddr_in6 *addr6 = (struct sockaddr_in6 *) storage;
        addr6->sin6_family = AF_INET6;
        addr6->sin6_port = port;
        memcpy(&(addr6->sin6_addr), &inaddr6, sizeof(inaddr6));
        return 0;
    }

    // Failed to parse address
    return -1;
}

int main(int argc, char const *argv[]) {
    if (argc != 3)
        usage(argv);

    // Initializing client storage
    struct sockaddr_storage client_storage;
    if (init_client_storage(&client_storage, argv[1], argv[2]) != 0)
        usage(argv);

    // Creating client socket
    int client_socket = socket(client_storage.ss_family, SOCK_STREAM, 0);
    if (client_socket == -1)
        logexit("socket");

    // Establishing connection with server
    struct sockaddr *client_addr = (struct sockaddr *) (&client_storage);
    if (connect(client_socket, client_addr, sizeof(client_storage)) != 0)
        logexit("connect");

    // Debugging connection
    char addrstr[BUFSZ];
    addrtostr(client_addr, addrstr, BUFSZ);
    printf("connected to: %s\n", addrstr);

    // Main loop to communicate with the server
    char buffer[BUFSZ];
    while (1) {
        // Reading message from keyboard
        printf("> ");
        memset(buffer, 0, BUFSZ);
        fgets(buffer, BUFSZ, stdin);

        // Sending message to server and checking if we sent it correctly
        size_t count_bytes = send(client_socket, buffer, strlen(buffer), 0);
        if (count_bytes != strlen(buffer))
            logexit("send");

        // Resetting buffer content and receiving information from server
        memset(buffer, 0, BUFSZ);
        unsigned int total_bytes = 0;
        while (1) {
            // Notice that the message may be sent to the client in "small parts"
            count_bytes = recv(client_socket, buffer + total_bytes, BUFSZ, 0);

            // Updating total read bytes
            total_bytes += count_bytes;

            // Checking to see if the message was fully received
            if (count_bytes == 0 || buffer[total_bytes - 1] == '\n')
                break;
        }

        // Checking if the connection has terminated (received 0 bytes)
        if (total_bytes == 0)
            break;

        printf("< received %u bytes\n", total_bytes);
        printf("< %s", buffer);
    }

    // Closing connection
    printf("< closing connection with server...\n");
    close(client_socket);

    return 0;
}

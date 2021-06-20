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

// Helper function to count the number of messages in a sequence of bytes
// It returns the number of messages found
int count_messages(const char *sequence) {
    int count = 0;
    for (int i = 0; i < strlen(sequence); i++)
        if (sequence[i] == '\n')
            count++;
    
    return count;
}

// Function to receive a complete message from the server
// It returns 1 on success and 0 in case of a failure
int receive_message(int client_socket, char *recv_buffer) {
    // Resetting buffer content
    memset(recv_buffer, 0, BUFSZ);
    
    size_t count_bytes = 0;
    unsigned int total_bytes = 0;
    int received_complete_message = 0;
    
    while (!received_complete_message) {
        // Notice that the message may be sent to the client in "small parts"
        // So we will keep track of the total bytes received until this moment
        count_bytes = recv(client_socket, recv_buffer + total_bytes, BUFSZ - total_bytes, 0);
        total_bytes += count_bytes;

        // Checking if client disconnected (received 0 bytes)
        if (count_bytes == 0)
            break;

        // Checking if the message was fully received
        else if (recv_buffer[total_bytes - 1] == '\n')
            received_complete_message = 1;
    }

    return received_complete_message;
}

// Function to send a message to the server
void send_message(int client_socket, char *send_buffer) {
    // Resetting buffer content
    memset(send_buffer, 0, BUFSZ);

    // Reading message from keyboard
    memset(send_buffer, 0, BUFSZ);
    fgets(send_buffer, BUFSZ, stdin);

    // Sending message to server and checking if we sent it correctly
    size_t count_bytes = send(client_socket, send_buffer, strlen(send_buffer), 0);
    if (count_bytes != strlen(send_buffer))
        logexit("send");
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

    // Main loop to communicate with the server
    int disconnected = 0;
    char send_buffer[BUFSZ], recv_buffer[BUFSZ];
    
    while (!disconnected) {
        // Sending message to server
        send_message(client_socket, send_buffer);
        
        // Receiving each sent message (we can send multiple messages on a single entry)
        // For example "add 111 111\nadd 111 222\n"
        int expected_number_messages = count_messages(send_buffer);
        while (expected_number_messages != 0) {
            if (receive_message(client_socket, recv_buffer) == 0) {
                disconnected = 1;
                break;
            }
            
            printf("%s", recv_buffer);
            expected_number_messages -= count_messages(recv_buffer);
        }
    }

    // Closing connection
    close(client_socket);
    return 0;
}
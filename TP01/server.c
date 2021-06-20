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
    if (protostr == NULL || portstr == NULL)
        return -1;
    
    // Clearing any garbage data on storage pointer
    memset(storage, 0, sizeof(*storage));

    // Parsing port from string to unsigned short
    uint16_t port = (uint16_t) atoi(portstr);
    if (port == 0)
        return -1;

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

// Function to return the client socket
// It returns the client socket descriptor on success or -1 for errors
int get_client_socket(int server_socket) {
    // Creating client storage and address structure
    struct sockaddr_storage client_storage;
    struct sockaddr *client_addr = (struct sockaddr *) (&client_storage);

    // Accepting and getting client socket
    socklen_t client_addrlen = sizeof(client_storage);
    return accept(server_socket, client_addr, &client_addrlen);
}

// Returns 1 if the command is valid and 0 otherwise
int is_valid_command(char *cmd) {
    char *valid_commands[] = {"add", "rm", "query", "list", "kill"};
    for (int i = 0; i < 5; i++)
        if (strcmp(cmd, valid_commands[i]) == 0)
            return 1;

    return 0;
}

// Returns 1 if the string is made only with numbers and 0 otherwise
int is_numerical_string(char *str) {
    if (str == NULL)
        return 0;
    
    for (int i = 0; i < strlen(str); i++)
        if (str[i] < '0' || str[i] > '9')
            return 0;

    return 1;
}

// Function to parse a message with format "cmd" or "cmd X Y"
// The command, X and Y values are stored on the function's parameters
// This function will return 1 on success and 0 otherwise
int parse_message(char *msg, char *cmd, int *x, int *y) {
    char *message_ptr;
    char *cmd_token  = strtok_r(msg,  " ", &message_ptr);
    char *x_token    = strtok_r(NULL, " ", &message_ptr);
    char *y_token    = strtok_r(NULL, " ", &message_ptr);
    char *null_token = strtok_r(NULL, " ", &message_ptr);

    // Checking if the command is valid
    if (cmd_token == NULL || !is_valid_command(cmd_token))
        return 0;

    // If the command is either "list" or "kill" we can't have any parameters
    strcpy(cmd, cmd_token);
    if (strcmp(cmd, "list") == 0 || strcmp(cmd, "kill") == 0)
        return x_token == NULL;

    // Checking if the message is in the correct format (2 numerical parameters only)
    if (!is_numerical_string(x_token) || !is_numerical_string(y_token) || null_token != NULL)
        return 0;
    
    // Converting location strings to integers
    *x = atoi(x_token);
    *y = atoi(y_token);

    // Checking if X and Y values are within the correct range
    if (*x < 0 || *x > 9999 || *y < 0 || *y > 9999)
        return 0;

    return 1;
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

    // Listen connections (max to 10 in this case)
    if (listen(server_socket, 10))
        logexit("listen");

    // Creating structure to maintain the locations
    location_array_t locations;
    create_location_array(&locations);

    // Main loop to receive clients
    int server_closed = 0;
    char send_buffer[BUFSZ], recv_buffer[BUFSZ];
    while (!server_closed) {
        int client_socket = get_client_socket(server_socket);

        // Loop to communicate with the client
        int client_disconnected = 0;
        while (!client_disconnected) {
            if (receive_message(client_socket, recv_buffer) == 0) {
                client_disconnected = 1;
                break;
            }

            // Checking if the message has no more than 500 bytes
            if (strlen(recv_buffer) > 500) {
                client_disconnected = 1;
                break;
            }
            
            int x, y;
            char cmd[10], *sequence_token, *sequence_ptr;
            
            sequence_token = strtok_r(recv_buffer, "\n", &sequence_ptr);
            while (sequence_token != NULL) {
                if (parse_message(sequence_token, cmd, &x, &y) == 0) {
                    client_disconnected = 1;
                    break;
                }

                if (strcmp(cmd, "kill") == 0) {
                    server_closed = 1;
                    client_disconnected = 1;
                    break;
                }

                else if (strcmp(cmd, "list") == 0)
                    location_array_to_string(&locations, send_buffer);
                
                else if (strcmp(cmd, "add") == 0)
                    add_location(&locations, (Point2D_t){x, y}, send_buffer);
                
                else if (strcmp(cmd, "rm") == 0)
                    remove_location(&locations, (Point2D_t){x, y}, send_buffer);

                else if (strcmp(cmd, "query") == 0)
                    get_closest_location(&locations, (Point2D_t){x, y}, send_buffer);
                
                size_t count_bytes = send(client_socket, send_buffer, strlen(send_buffer), 0);
                if (count_bytes != strlen(send_buffer))
                    logexit("send");

                sequence_token = strtok_r(NULL, "\n", &sequence_ptr);
            }
        }

        close(client_socket);
    }

    // Closing server
    close(server_socket);
}
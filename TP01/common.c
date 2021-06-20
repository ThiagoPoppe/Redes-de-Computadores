#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

#include <sys/types.h>
#include <sys/socket.h>

#include "common.h"

// Function to prompt an error and exit the program
void logexit(const char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

// Function to receive a complete message from the network
// It returns 1 on success and 0 in case of a failure
int receive_message(int socket, char *buffer) {
    int received_complete_message = 0;
    size_t count_bytes = 0, total_bytes = 0;
    
    memset(buffer, 0, BUFSZ);
    while (!received_complete_message) {
        // Notice that the message may be sent to the client in "small parts"
        // So we will keep track of the total bytes received until this moment
        count_bytes = recv(socket, buffer + total_bytes, BUFSZ - total_bytes, 0);
        total_bytes += count_bytes;

        // Checking if client disconnected (received 0 bytes)
        if (count_bytes == 0)
            break;

        // Checking if the message was fully received
        else if (buffer[total_bytes - 1] == '\n')
            received_complete_message = 1;
    }

    return received_complete_message;
}
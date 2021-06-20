#ifndef COMMON_H
#define COMMON_H

#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>

#define BUFSZ 512 // size of messages

// Function to prompt an error and exit the program
void logexit(const char *msg);

// Function to receive a complete message from the network
// It returns 1 on success and 0 in case of a failure
int receive_message(int socket, char *buffer);

#endif
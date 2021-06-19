#pragma once

#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>

#define BUFSZ 1024 // size of string messages

/* Function to prompt an error and exit the program */
void logexit(const char *msg);

/* Function to parse a string to address returning 0 on success and -1 otherwise. */
int addrparse(struct sockaddr_storage *storage, const char *addrstr, const char *portstr);

/* Function to parse an address to string */
void addrtostr(struct sockaddr *addr, char *str, size_t strsize);
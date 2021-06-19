#ifndef COMMON_H
#define COMMON_H

#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>

#define BUFSZ 512 // size of string messages

/* Function to prompt an error and exit the program */
void logexit(const char *msg);

/* Function to parse port from string to unsigned short returning 0 on success and -1 otherwise */
int portparse(const char *portstr);

/* Function to parse an address to string */
void addrtostr(struct sockaddr *addr, char *str, size_t strsize);

#endif
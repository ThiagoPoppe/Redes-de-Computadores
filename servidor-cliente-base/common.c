#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

#include <arpa/inet.h>

/* Function to prompt an error and exit the program */
void logexit(const char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

/* Function to parse a string to address returning 0 on success and -1 otherwise. */
int addrparse(struct sockaddr_storage *storage, const char *addrstr, const char *portstr) {
    if (addrstr == NULL || portstr == NULL) {
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

/* Function to parse an address to string */
void addrtostr(struct sockaddr *addr, char *str, size_t strsize) {
    // Checking if output string was provided
    if (str == NULL) {
        logexit("Output string cannot be NULL.");
    }

    int version;
    uint16_t port;
    char addrstr[INET6_ADDRSTRLEN + 1] = "";

    // Trying to parse as IPv4
    if (addr->sa_family == AF_INET) {
        version = 4;
        struct sockaddr_in *addr4 = (struct sockaddr_in *) addr;
        if (!inet_ntop(AF_INET, &(addr4->sin_addr), addrstr, INET6_ADDRSTRLEN + 1)) {
            logexit("ntop (network to presentation)");
        }
        port = ntohs(addr4->sin_port); // Network to host short
    }

    // Trying to parse as IPv6
    else if (addr->sa_family == AF_INET6) {
        version = 6;
        struct sockaddr_in6 *addr6 = (struct sockaddr_in6 *) addr;
        if (!inet_ntop(AF_INET6, &(addr6->sin6_addr), addrstr, INET6_ADDRSTRLEN + 1)) {
            logexit("ntop (network to presentation)");
        }
        port = ntohs(addr6->sin6_port); // Network to host short
    }

    else {
        logexit("Unknown protocol family.");
    }

    // Constructing output string address representation
    snprintf(str, strsize, "IPv%d %s %hu", version, addrstr, port);
}
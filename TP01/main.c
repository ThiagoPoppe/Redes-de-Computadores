#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Helper function to count the number of messages (number of \n)
// It returns the number of messages found
int count_messages(const char *msg) {
    int count = 0;
    for (int i = 0; i < strlen(msg); i++)
        if (msg[i] == '\n')
            count++;
    
    return count;
}

int main(int argc, const char *argv[]) {
    char buffer[] = "oi xofanna\ndone\n";

    char msg[512];
    strncpy(msg, buffer, strlen(buffer)-5);

    printf("%s", msg);

    return 0;
}
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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
    
    // Reading each message token
    char *cmd_token  = strtok_r(msg,  " ", &message_ptr);
    char *x_token    = strtok_r(NULL, " ", &message_ptr);
    char *y_token    = strtok_r(NULL, " ", &message_ptr);
    char *null_token = strtok_r(NULL, " ", &message_ptr);

    // Checking if the command it's not NULL or invalid
    if (cmd_token == NULL || !is_valid_command(cmd_token))
        return 0;

    // Parsing the command token
    strcpy(cmd, cmd_token);

    // Checking if the command is a "non-parameter" command
    // If so, we can't have a parameter (x_token must be null)
    // If x_token is NULL we return success and failure otherwise
    if (strcmp(cmd, "list") == 0 || strcmp(cmd, "kill") == 0)
        return x_token == NULL;

    // Checking if the message format is correct (given that the command accepts parameters)
    // In other words, X and Y must be numerical strings and we can't have a third parameter
    if (!is_numerical_string(x_token) || !is_numerical_string(y_token) || null_token != NULL)
        return 0;
    
    // Parsing X and Y parameters
    *x = atoi(x_token);
    *y = atoi(y_token);

    return 1;
}

int main(int argc, const char *argv[]) {
    char buffer[] = "add 1 2 3\nrm 1 a 3\nquery 1 2 3\nlist 1 2 3\nkill 1 2 3";
    char *sequence_token, *sequence_ptr;

    char cmd[10];
    int x, y;

    sequence_token = strtok_r(buffer, "\n", &sequence_ptr);
    while (sequence_token != NULL) {
        printf("%s: ", sequence_token);
        if (parse_message(sequence_token, cmd, &x, &y) == 0)
            printf("erro na mensagem\n");
        else {
            if (strcmp(cmd, "list") == 0 || strcmp(cmd, "kill") == 0)
                printf("%s\n", cmd);
            else
                printf("%s %d %d\n", cmd, x, y);
        }
            
        sequence_token = strtok_r(NULL, "\n", &sequence_ptr);
    }

    return 0;
}
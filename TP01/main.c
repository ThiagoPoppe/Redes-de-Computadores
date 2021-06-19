#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char const *argv[]) {
    char buffer[] = "Mensagem teste strcmp :D";
    char *token;

    token = strtok(buffer, " ");
    while (token != NULL) {
        printf("%s\n", token);
        if (strcmp(token, "strcmp") == 0)
            printf("CHEGUEI NA STRCMP!!\n");

        token = strtok(NULL, " ");
    }

    printf("Valor do buffer: %s\n", buffer);

    return 0;
}

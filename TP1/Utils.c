#include <stdio.h>
#include <stdlib.h>

#include "Utils.h"

// Função para mostrar o erro e sair do programa
void logexit(const char* error_msg) {
    perror(error_msg);
    exit(EXIT_FAILURE);
}
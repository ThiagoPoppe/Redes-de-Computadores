#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <sys/socket.h>
#include <sys/types.h>
#include <arpa/inet.h>

#define BUFSZ 4096

void usage(const char* argv[]);
void logexit(const char* error_msg);
int sockaddr_cliente_init(const char *addrstr, const char *portstr, struct sockaddr_storage *storage);

int main(int argc, const char* argv[]) {
    if (argc != 3)
        usage(argv);

    // Inicialização do storage do cliente
    struct sockaddr_storage storage;
    if (sockaddr_cliente_init(argv[1], argv[2], &storage) != 0)
        usage(argv);

    // Criando o socket do cliente
    int sock = socket(storage.ss_family, SOCK_STREAM, 0);
    if (sock == -1)
        logexit("socket");

    // Estabelecendo conexão
    struct sockaddr* addr = (struct sockaddr*) (&storage);
    if (connect(sock, addr, sizeof(storage)) != 0)
        logexit("connect");

    // Loop principal
    char inBuffer[BUFSZ], outBuffer[BUFSZ];
    while (1) {
        memset(outBuffer, 0, BUFSZ);
        printf("> "); fgets(outBuffer, BUFSZ, stdin);

        // Enviando mensagem para o servidor
        size_t count = send(sock, outBuffer, strlen(outBuffer)+1, 0);
        if (count != strlen(outBuffer)+1)
            logexit("send");

        // Recebendo mensagem do servidor
        memset(inBuffer, 0, BUFSZ);
        count = recv(sock, inBuffer, BUFSZ, 0);
        printf("%s", inBuffer);

        // Conexão finalizada
        if (count == 0)
            break;
    }
    
    // Fechando a conexão cliente servidor
    close(sock);
    exit(EXIT_SUCCESS);
}


/* **************** DEFINIÇÃO DAS FUNÇÕES **************** */

// Função auxiliar para explicar como usar o programa
void usage(const char* argv[]) {
    printf("usage: %s <server IP> <server port>\n", argv[0]);
    printf("example: %s 127.0.0.1 51511\n", argv[0]);

    exit(EXIT_FAILURE);
}

// Função para mostrar o erro e sair do programa
void logexit(const char* error_msg) {
    perror(error_msg);
    exit(EXIT_FAILURE);
}

// Função para inicializar o sockaddr_storage do cliente
int sockaddr_cliente_init(const char *addrstr, const char *portstr, struct sockaddr_storage *storage) {
    if (addrstr == NULL || portstr == NULL)
        return -1;

    uint16_t port = (uint16_t) atoi(portstr); // uint16_t => unsigned short
    if (port == 0)
        return -1;

    // Testar com endereço IPv4 de 32 bits
    struct in_addr inaddr4;
    if (inet_pton(AF_INET, addrstr, &inaddr4)) {
        struct sockaddr_in *addr4 = (struct sockaddr_in *) storage;
        addr4->sin_family = AF_INET;
        addr4->sin_port = htons(port); // host to network short: sempre big-ending
        addr4->sin_addr = inaddr4;
        return 0;
    }

    // Testar com endereço IPv6 de 128 bits
    struct in6_addr inaddr6;
    if (inet_pton(AF_INET6, addrstr, &inaddr6)) {
        struct sockaddr_in6 *addr6 = (struct sockaddr_in6 *) storage;
        addr6->sin6_family = AF_INET6;
        addr6->sin6_port = htons(port); // host to network short: sempre big-ending
        memcpy(&(addr6->sin6_addr), &inaddr6, sizeof(inaddr6));
        return 0;
    }

    // Protocolo não encontrado (não é IPv4 nem IPv6)
    return -1;
}
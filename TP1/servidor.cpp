#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <arpa/inet.h>

/* **************** CABEÇALHOS **************** */

#define BUFSZ 4096

// Estrutura para armazenar o cliente
typedef struct client {
    int csock;
    struct sockaddr_storage storage;
} ClientData;

void usage(const char* argv[]);
void logexit(const char* error_msg);
void* client_thread(void* args);
ClientData* create_client(int csock, struct sockaddr_storage cstorage);
int sockaddr_servidor_init(const char* proto,const char* portstr, struct sockaddr_storage* storage);

/* **************** FUNÇÃO PRINCIPAL **************** */

int main(int argc, const char** argv) {
    if (argc != 3)
        usage(argv);

    // Inicialização do storage do servidor
    struct sockaddr_storage storage;
    if (sockaddr_servidor_init(argv[1], argv[2], &storage) != 0)
        usage(argv);

    // Criação do socket do servidor
    int sock = socket(storage.ss_family, SOCK_STREAM, 0);
    if (sock == -1)
        logexit("socket");

    // Fazendo o bind e listen do servidor
    struct sockaddr* addr = (struct sockaddr*) (&storage);
    if (bind(sock, addr, sizeof(storage)) != 0)
        logexit("bind");

    if (listen(sock, 10))
        logexit("listen");

    // Loop principal
    while (1) {
        // Variáveis para a comunicação com o cliente
        struct sockaddr_storage cstorage;
        struct sockaddr* caddr = (struct sockaddr*) (&cstorage);
        socklen_t caddrlen = sizeof(cstorage);

        // Realizando o accept da conexão
        int csock = accept(sock, caddr, &caddrlen);
        if (csock == -1)
            logexit("accept");

        // Alocando estrutura do cliente
        ClientData* cdata = create_client(csock, cstorage);

        // Disparando thread do cliente
        pthread_t tid;
        pthread_create(&tid, NULL, client_thread, cdata);
    }

    // Fechando o servidor
    close(sock);
    exit(EXIT_SUCCESS);

    return 0;
}

/* **************** DEFINIÇÃO DAS FUNÇÕES **************** */

// Função auxiliar para explicar como usar o programa
void usage(const char** argv) {
    printf("usage: %s <v4|v6> <server port>\n", argv[0]);
    printf("example: %s v4 51511\n", argv[0]);
    exit(EXIT_FAILURE);    
}

// Função para mostrar o erro e sair do programa
void logexit(const char* error_msg) {
    perror(error_msg);
    exit(EXIT_FAILURE);
}

// Thread do cliente
void* client_thread(void* args) {
    // Recuperando as informações do cliente
    ClientData* cdata = (ClientData*) args;
    char inBuffer[BUFSZ], outBuffer[BUFSZ];

    // Recebendo mensagem do cliente
    memset(inBuffer, 0, BUFSZ);
    size_t count = recv(cdata->csock, inBuffer, BUFSZ, 0);

    // Inscrevendo o cliente na tag especificada
    if (inBuffer[0] == '+') {
        memset(outBuffer, 0, BUFSZ);
        snprintf(outBuffer, BUFSZ, "< subscribed %s", inBuffer);

        // Enviando mensagem
        count = send(cdata->csock, outBuffer, strlen(outBuffer)+1, 0);
        if (count != strlen(outBuffer)+1)
            logexit("send");
    }

    // Desinscrevendo o cliente na tag especificada
    else if (inBuffer[0] == '-') {
        memset(outBuffer, 0, BUFSZ);
        snprintf(outBuffer, BUFSZ, "< unsubscribed %s", inBuffer);

        // Enviando mensagem
        count = send(cdata->csock, outBuffer, strlen(outBuffer)+1, 0);
        if (count != strlen(outBuffer)+1)
            logexit("send");
    }

    close(cdata->csock);
    pthread_exit(NULL);
}

ClientData* create_client(int csock, struct sockaddr_storage cstorage) {
    ClientData* cdata = (ClientData*) malloc(sizeof(ClientData));
    if (!cdata)
        logexit("malloc");

    cdata->csock = csock;
    memcpy(&(cdata->storage), &cstorage, sizeof(cstorage));

    return cdata;
}

// Função para inicializar o sockaddr_storage do servidor
int sockaddr_servidor_init(const char* proto,const char* portstr, struct sockaddr_storage* storage) {
    uint16_t port = (uint16_t) atoi(portstr); // uint16_t => unsigned short
    if (port == 0) 
        return -1;
    
    // Testar com endereço IPv4 de 32 bits
    if(strcmp(proto, "v4") == 0) {
        struct sockaddr_in *addr4 = (struct sockaddr_in *) storage;
        addr4->sin_family = AF_INET;
        addr4->sin_port = htons(port); // host to network short: sempre big-ending
        addr4->sin_addr.s_addr = INADDR_ANY;
        return 0;
    }
    
    // Testar com endereço IPv6 de 128 bits
    if (strcmp(proto, "v6") == 0) {
        struct sockaddr_in6 *addr6 = (struct sockaddr_in6 *) storage;
        addr6->sin6_family = AF_INET6;
        addr6->sin6_port = htons(port); // host to network short: sempre big-ending
        addr6->sin6_addr = in6addr_any;
        return 0;
    }

    // Protocolo não encontrado (não é IPv4 nem IPv6)
    return -1;
}
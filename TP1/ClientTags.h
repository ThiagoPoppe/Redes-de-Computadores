#ifndef CLIENT_TAGS_H
#define CLIENT_TAGS_H

#include <map>
#include <set>
#include <string>

using namespace std;

class ClientTags {
private:
    map< int, set<string> > mymap;

public:
    // Construtor e destrutor da classe
    ClientTags()  { }
    ~ClientTags() { }

    // Função que adiciona uma tag no cliente representado por csock (socket do cliente)
    // Retornando uma string indicando o que foi feito
    string add_tag(int csock, string tag);

    // Função que remove uma tag do cliente representado por csock (socket do cliente)
    // Retornando uma string indicando o que foi feito
    string remove_tag(int csock, string tag);

    // Função que remove um cliente da estrutura
    void remove_client(int csock);

    // Função auxiliar que retorna se um cliente já possui uma tag
    bool has_tag(int csock, string tag);
};

#endif
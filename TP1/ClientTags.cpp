#include "ClientTags.h"
#include <iostream>

// Função que adiciona uma tag no cliente representado por csock (socket do cliente)
// Retornando uma string indicando o que foi feito
string ClientTags::add_tag(int csock, string tag) {
    string output = "";
    string tag_str = tag.substr(1, tag.size());

    // Caso o cliente não seja inscrito na tag iremos inscrevê-lo,
    // senão iremos alertar que ele já é inscrito
    if (!has_tag(csock, tag_str)) {
        mymap[csock].insert(tag_str);
        output = "< subscribed " + tag + "\n";
    }
    else
        output = "< already subscribed " + tag + "\n";

    return output;
}

// Função que remove uma tag do cliente representado por csock (socket do cliente)
// Retornando uma string indicando o que foi feito
string ClientTags::remove_tag(int csock, string tag) {
    string output = "";
    string tag_str = tag.substr(1, tag.size());

    // Caso o cliente seja inscrito na tag iremos desinscrevê-lo,
    // senão iremos alertar que ele já é desinscrito
    if (has_tag(csock, tag_str)) {
        mymap[csock].erase(tag_str);
        output = "< unsubscribed " + tag + "\n";
    }
    else
        output = "< not subscribed " + tag + "\n";

    return output;
}

// Função que remove um cliente da estrutura
void ClientTags::remove_client(int csock) {
    mymap.erase(csock);
}

// Função auxiliar que retorna se um cliente já possui uma tag
bool ClientTags::has_tag(int csock, string tag) {
    return mymap[csock].find(tag) != mymap[csock].end();
}

// Função auxiliar para exibir a estrutura
void ClientTags::show_clients() {
    for (auto client : mymap) {
        cout << "Client (Socket=" << client.first << "):" << endl;
        for (auto tag : client.second)
            cout << "  - " << tag << endl;
        cout << endl;
    }
}
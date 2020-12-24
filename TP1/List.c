#include <stdio.h>
#include <stdlib.h>

#include "List.h"

// Função de criação do node
Node* create_node(int val) {
    Node* new_node = (Node*) malloc(sizeof(Node));
    new_node->val = val;
    new_node->next = NULL;

    return new_node;
}

// Função de criação da lista
List* create_list() {
    List* new_list = (List*) malloc(sizeof(List));
    new_list->head = NULL;
    new_list->tail = NULL;
    new_list->size = 0;

    return new_list;
}

// Função de inserção no final da lista
void list_append(List* list, int val) {
    Node* new_node = create_node(val);

    // Atualizando ponteiros
    if (is_list_empty(list))
        list->head = new_node;
    else
        list->tail->next = new_node;

    list->tail = new_node;
    list->size++;
}

// Função auxiliar "privada" para a remoção de um nó, retornando seu valor
int remove_node(List* list, Node* prev, Node* toFree) {
    // Atualizando ponteiros
    if (prev == NULL) {
        list->head = toFree->next;
    }
    else {
        prev->next = toFree->next;
        if (toFree == list->tail)
            list->tail = prev;
    }

    // Salvando valor e removendo node
    int node_val = toFree->val;
    list->size--;
    free(toFree);

    return node_val;
}

// Função de remoção de nodes por índice, retornando o valor removido
int remove_by_index(List* list, int idx) {
    if (idx < 0 || idx >= list->size) {
        perror("List index out of bounds");
        exit(EXIT_FAILURE);
    }

    // Caminhando até o índice solicitado
    Node* prev = NULL;
    Node* toFree = list->head;
    
    for (int i = 0; i < idx; i++) {
        prev = toFree;
        toFree = toFree->next;
    }

    return remove_node(list, prev, toFree);
}

// Função de remoção de nodes por valor, retornando o valor removido
int remove_by_value(List* list, int val) {
    // Caminhando até o índice solicitado
    Node* prev = NULL;
    Node* toFree = list->head;

    // Caminhando até o valor solicitado
    while (toFree != NULL && toFree->val != val) {
        prev = toFree;
        toFree = toFree->next;
    }

    // Se aux for nulo, o valor não foi encontrado!
    if (toFree == NULL) {
        perror("Value not found");
        exit(EXIT_FAILURE);
    }

    return remove_node(list, prev, toFree);
}

// Função auxiliar que exibe uma lista
void show_list(List* list) {
    Node* aux = list->head;

    while (aux != NULL) {
        printf("%d ", aux->val);
        aux = aux->next;
    }

    printf("\n");
}

// Função auxiliar que retorna se a lista está vazia ou não
int is_list_empty(List* list) {
    return list->head == NULL;
}

// Função para desalocar a memória de uma lista
void free_list(List* list) {
    Node* toFree = NULL;
    Node* aux = list->head;

    // Dando free em cada node
    while (aux != NULL) {
        toFree = aux;
        aux = aux->next;

        free(toFree);
    }

    // Dando free na lista
    free(list);
}
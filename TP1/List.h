#ifndef LIST_H
#define LIST_H

typedef struct node {
    int val;
    struct node* next;
} Node;

typedef struct list {
    int size;
    struct node* head;
    struct node* tail;
} List;

// Funções de criação (lista e node)
Node* create_node(int val);
List* create_list();

// Função de inserção no final da lista
void list_append(List* list, int val);

// Funções de remoção de nodes (por índice e por valor)
// retornando o valor removido
int remove_by_index(List* list, int idx);
int remove_by_value(List* list, int val);

// Funções auxiliares (exibir lista e verificar se lista está vazia)
void show_list(List* list);
int is_list_empty(List* list);

// Função para desalocar a memória de uma lista
void free_list(List* list);

#endif

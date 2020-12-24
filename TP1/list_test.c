#include <stdio.h>
#include <stdlib.h>

#include "List.h"

int main(int argc, const char** argv) {
    List* list = create_list();

    for (int i = 0; i <= 10; i++)
        list_append(list, i);

    list_append(list, 1000);
    show_list(list);
    
    remove_by_index(list, 0);
    show_list(list);
    
    remove_by_index(list, 2);
    show_list(list);
    
    remove_by_value(list, 5);
    show_list(list);

    remove_by_value(list, 1000);
    show_list(list);

    // list_append(list, 500);
    // show_list(list);

    free_list(list);
    return 0;
}
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "location_array.h"

location_array_t location_array;
char answer[128];

int total_tests = 15;
int passed_tests = 0;

void assert(char *method, char *actual, char *expected) {
    if (strcmp(actual, expected) != 0) {
        printf("[-] %s : failed\n", method);
        printf("\t - expected : %s", expected);
        printf("\t - actual   : %s", actual);
    }
    else {
        passed_tests++;
        printf("[+] %s : success\n", method);
    }
}

void test_empty_location_array_to_string() {
    create_location_array(&location_array);

    location_array_to_string(&location_array, answer);
    assert("test_empty_location_array_to_string", answer, "none\n");
}

void test_location_array_to_string() {
    create_location_array(&location_array);

    add_location(&location_array, (Point2D_t){0,1}, answer);
    add_location(&location_array, (Point2D_t){2,3}, answer);
    add_location(&location_array, (Point2D_t){4,5}, answer);

    location_array_to_string(&location_array, answer);
    assert("test_location_array_to_string", answer, "0 1 2 3 4 5\n");
}

void test_add_location() {
    create_location_array(&location_array);

    add_location(&location_array, (Point2D_t){0,1}, answer);
    assert("test_add_location", answer, "0 1 added\n");
}

void test_limit_exceeded() {
    create_location_array(&location_array);
    
    for (int i = 0; i < MAX_NUM_LOCATIONS + 1; i++)
        add_location(&location_array, (Point2D_t){i,i+1}, answer);

    assert("test_limit_exceeded", answer, "limit exceeded\n");
}

void test_already_exists() {
    create_location_array(&location_array);

    add_location(&location_array, (Point2D_t){0,1}, answer);
    add_location(&location_array, (Point2D_t){0,1}, answer);
    assert("test_already_exists", answer, "0 1 already exists\n");
}

void test_remove_empty_location_array() {
    create_location_array(&location_array);

    remove_location(&location_array, (Point2D_t){0,1}, answer);
    assert("test_remove_empty_location_array", answer, "0 1 does not exist\n");
}

void test_remove_does_not_exist() {
    create_location_array(&location_array);

    add_location(&location_array, (Point2D_t){0,1}, answer);
    add_location(&location_array, (Point2D_t){2,3}, answer);

    remove_location(&location_array, (Point2D_t){4,5}, answer);
    assert("test_remove_does_not_exist", answer, "4 5 does not exist\n");  
}

void test_remove_from_begin() {
    create_location_array(&location_array);

    add_location(&location_array, (Point2D_t){0,1}, answer);
    add_location(&location_array, (Point2D_t){2,3}, answer);

    remove_location(&location_array, (Point2D_t){0,1}, answer);
    assert("test_remove_from_begin", answer, "0 1 removed\n");    
}

void test_remove_from_end() {
    create_location_array(&location_array);

    add_location(&location_array, (Point2D_t){0,1}, answer);
    add_location(&location_array, (Point2D_t){2,3}, answer);

    remove_location(&location_array, (Point2D_t){2,3}, answer);
    assert("test_remove_from_end", answer, "2 3 removed\n");
}

void test_remove_location() {
    create_location_array(&location_array);

    add_location(&location_array, (Point2D_t){0,1}, answer);
    add_location(&location_array, (Point2D_t){2,3}, answer);
    add_location(&location_array, (Point2D_t){4,5}, answer);

    remove_location(&location_array, (Point2D_t){2,3}, answer);
    assert("test_remove_location", answer, "2 3 removed\n");
}

void test_remove_then_add_back_in_different_order() {
    create_location_array(&location_array);

    add_location(&location_array, (Point2D_t){0,1}, answer);
    add_location(&location_array, (Point2D_t){2,3}, answer);
    add_location(&location_array, (Point2D_t){4,5}, answer);

    remove_location(&location_array, (Point2D_t){2,3}, answer);
    add_location(&location_array, (Point2D_t){2,3}, answer);

    remove_location(&location_array, (Point2D_t){2,3}, answer);
    add_location(&location_array, (Point2D_t){2,3}, answer);

    remove_location(&location_array, (Point2D_t){0,1}, answer);
    add_location(&location_array, (Point2D_t){0,1}, answer);

    location_array_to_string(&location_array, answer);
    assert("test_remove_then_add_back_in_different_order", answer, "4 5 2 3 0 1\n");
}

void test_remove_all_then_add_back_limit_exceeded() {
    create_location_array(&location_array);

    for (int i = 0; i < MAX_NUM_LOCATIONS; i++)
        add_location(&location_array, (Point2D_t){i,i+1}, answer);

    for (int i = 0; i < MAX_NUM_LOCATIONS; i++)
        remove_location(&location_array, (Point2D_t){i,i+1}, answer);

    for (int i = 0; i < MAX_NUM_LOCATIONS; i++)
        add_location(&location_array, (Point2D_t){i,i+1}, answer);

    add_location(&location_array, (Point2D_t){0,0}, answer);

    assert("test_remove_all_then_add_back_limit_exceeded", answer, "limit exceeded\n");
}

void test_get_closest_location_empty_location_array() {
    create_location_array(&location_array);

    get_closest_location(&location_array, (Point2D_t){0,1}, answer);
    assert("test_get_closest_location_empty_location_array", answer, "none\n");
}

void test_get_closest_location_equal_distances() {
    create_location_array(&location_array);

    add_location(&location_array, (Point2D_t){0,0}, answer);
    add_location(&location_array, (Point2D_t){0,2}, answer);
    add_location(&location_array, (Point2D_t){2,0}, answer);
    add_location(&location_array, (Point2D_t){2,2}, answer);

    get_closest_location(&location_array, (Point2D_t){1,1}, answer);
    assert("test_get_closest_location_equal_distances", answer, "0 0\n");
}

void test_get_closest_location() {
    create_location_array(&location_array);

    add_location(&location_array, (Point2D_t){2,5}, answer);
    add_location(&location_array, (Point2D_t){9,6}, answer);
    add_location(&location_array, (Point2D_t){0,3}, answer);
    add_location(&location_array, (Point2D_t){2,8}, answer);
    add_location(&location_array, (Point2D_t){8,1}, answer);

    get_closest_location(&location_array, (Point2D_t){5,4}, answer);
    assert("test_get_closest_location", answer, "2 5\n");
}

int main(int argc, const char *argv[]) {
    printf("\n");
    
    test_add_location();
    test_already_exists();
    test_limit_exceeded();
    test_remove_from_end();
    test_remove_location();
    test_remove_from_begin();
    test_get_closest_location();
    test_remove_does_not_exist();
    test_location_array_to_string();
    test_remove_empty_location_array();
    test_empty_location_array_to_string();
    test_get_closest_location_equal_distances();
    test_remove_all_then_add_back_limit_exceeded();
    test_remove_then_add_back_in_different_order();
    test_get_closest_location_empty_location_array();

    double percentage = (double) passed_tests / total_tests;
    printf("\n%d/%d = %.2f%% tests were successful\n", passed_tests, total_tests, 100 * percentage);

    return 0;
}
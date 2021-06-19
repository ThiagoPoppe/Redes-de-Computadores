#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "common.h"
#include "location_array.h"

// Function to create the location array
void create_location_array(LocationArray_t* location_array) {
    location_array->size = 0;
    for (int i = 0; i < MAX_NUM_LOCATIONS; i++) {
        location_array->array[i].x = -1;
        location_array->array[i].y = -1;
    }
}

// Function to add a new location
// The operation status will be saved on the string "status"
void add_location(LocationArray_t* location_array, Point2D_t coord, char *status) {
    // Cleaning any garbage in status string
    memset(status, 0, strlen(status));

    // Checking if location array is already full
    if (location_array->size == MAX_NUM_LOCATIONS) {
        sprintf(status, "limit exceeded\n");
        return ;
    }

    // Checking if coordenate exists on location array
    for (int i = 0; i < location_array->size; i++) {
        Point2D_t curr_location = location_array->array[i];
        if (curr_location.x == coord.x && curr_location.y == coord.y) {
            sprintf(status, "%d %d already exists\n", coord.x, coord.y);
            return ;
        }
    }

    // Adding new location to the location array
    int idx = location_array->size;
    location_array->array[idx] = coord;
    location_array->size++;

    sprintf(status, "%d %d added\n", coord.x, coord.y);
    return ;
}

// Function to shift the location array to the left given an index
void shift_left(LocationArray_t* location_array, int idx) {
    for (int i = idx; i < location_array->size - 1; i++) {
        location_array->array[i] = location_array->array[i+1];
        location_array->array[i+1].x = -1;
        location_array->array[i+1].y = -1;
    }
}

// Function to remove a location
// The operation status will be saved on the string "status"
void remove_location(LocationArray_t* location_array, Point2D_t coord, char *status) {
    // Cleaning any garbage in status string
    memset(status, 0, strlen(status));

    int location_idx = -1;
    for (int i = 0; i < MAX_NUM_LOCATIONS; i++) {
        Point2D_t curr_location = location_array->array[i];
        if (curr_location.x == coord.x && curr_location.y == coord.y) {
            location_idx = i;
            break;
        }
    }

    // Checking if the location was not found
    if (location_idx == -1) {
        sprintf(status, "%d %d does not exist\n", coord.x, coord.y);
        return ;
    }

    // Removing location (adding {-1, -1} to the location position)
    location_array->array[location_idx].x = -1;
    location_array->array[location_idx].y = -1;

    // Shifting the whole array to the left if the location is not the last one
    if (location_idx != MAX_NUM_LOCATIONS - 1)
        shift_left(location_array, location_idx);

    location_array->size--;

    sprintf(status, "%d %d removed\n", coord.x, coord.y);
    return ;
}

// Function to represent the location array as a string (X1 Y1 X2 Y2 ... Xn Yn)
void location_array_to_string(LocationArray_t* location_array, char *str) {
    // Clearning any garbage in output string
    memset(str, 0, strlen(str));

    // Checking for empty location array
    if (location_array->size == 0) {
        sprintf(str, "none\n");
        return ;
    }
    
    char buffer[BUFSZ];
    for (int i = 0; i < location_array->size; i++) {
        Point2D_t curr_location = location_array->array[i];
        if (i != location_array->size - 1)
            sprintf(buffer, "%d %d ", curr_location.x, curr_location.y);
        else
            sprintf(buffer, "%d %d\n", curr_location.x, curr_location.y);

        strcat(str, buffer);
    }

    return ;
}

// Function to get the closest location
// The operation status will be saved on the string "status"
void get_closest_location(LocationArray_t* location_array, Point2D_t coord, char *status) {
    // Cleaning any garbage in status string
    memset(status, 0, strlen(status));

    // Checking for empty location array
    if (location_array->size == 0) {
        sprintf(status, "none\n");
        return ;
    }
    
    // Start search with first point as the closest one so far
    int xmin = location_array->array[0].x;
    int ymin = location_array->array[0].y;
    int dx = (coord.x - xmin);
    int dy = (coord.y - ymin);
    int min_dist = dx*dx + dy*dy; // we can forget about the sqrt

    for (int i = 1; i < location_array->size; i++) {
        Point2D_t curr_location = location_array->array[i];
        int dx = (coord.x - curr_location.x);
        int dy = (coord.y - curr_location.y);
        int dist = dx*dx + dy*dy;

        if (dist < min_dist) {
            xmin = curr_location.x;
            ymin = curr_location.y;
            min_dist = dist;
        }
    }

    sprintf(status, "%d %d\n", xmin, ymin);
    return ;
}